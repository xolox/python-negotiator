# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: December 5, 2019
# URL: https://negotiator.readthedocs.org

"""
The guest agent daemon and client.

This module implements the guest agent, the Python daemon process that's always
running inside KVM/QEMU guests.
"""

# Standard library modules.
import errno
import fcntl
import itertools
import logging
import multiprocessing
import os
import signal
import sys
import time

# External dependencies.
from humanfriendly import Timer, compact

# Modules included in our project.
from negotiator_common import NegotiatorInterface
from negotiator_common.utils import GracefulShutdown

# Semi-standard module versioning.
__version__ = '0.12'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class GuestAgent(NegotiatorInterface):

    """Implementation of the daemon running inside KVM/QEMU guests."""

    def __init__(self, character_device, retry=False):
        """
        Initialize a negotiator guest agent.

        :param character_device: The absolute pathname of the character device
                                 that we should use to connect to the host (a
                                 string).
        :param retry: :data:`True` to retry ``EBUSY`` errors, :data:`False`
                      otherwise (defaults to :data:`False`).

        .. note:: When ``retry`` is :data:`True` it is (somewhat theoretically)
                  possible for infinite retrying to cause control to never be
                  returned to the caller. This is why callers are expected to
                  use :class:`~negotiator_common.utils.TimeOut` or a similar
                  solution.
        """
        custom_open = self.retry_open if retry else open
        super(GuestAgent, self).__init__(
            handle=custom_open(character_device, 'r+'),
            label="character device %s" % character_device,
        )

    def retry_open(self, character_device, mode):
        """Open the character device and retry ``EBUSY`` errors."""
        while True:
            try:
                return open(character_device, mode)
            except OSError as e:
                if e.errno == errno.EBUSY:
                    logger.debug("Retrying access to %s after EBUSY error ..", character_device)
                    time.sleep(1)
                else:
                    raise

    def raw_readline(self):
        """
        Read a newline terminated string from the remote side.

        This method overrides the
        :func:`~negotiator_common.NegotiatorInterface.raw_readline()` method
        of the :func:`~negotiator_common.NegotiatorInterface` class to
        implement blocking reads based on :data:`os.O_ASYNC` and
        :data:`signal.SIGIO` (see also :class:`WaitForRead`).

        :returns: The data read from the remote side (a string).
        """
        while True:
            # Check if the channel contains data.
            logger.debug("Preparing to read line from %s ..", self.conn_label)
            data = self.conn_handle.readline()
            if data:
                break
            # If the readline() above returns an empty string the channel
            # is (probably) not connected. At this point we'll bother to
            # prepare a convoluted way to block until the channel does
            # become connected.
            logger.debug("Got an empty read, emulating blocking read of %s ..", self.conn_label)
            # Set the O_ASYNC flag on the file descriptor connected to the
            # character device (this is required to use SIGIO signals).
            flags = fcntl.fcntl(self.conn_handle, fcntl.F_GETFL)
            fcntl.fcntl(self.conn_handle, fcntl.F_SETFL, flags | os.O_ASYNC)
            # Spawn a subprocess to reliably handle SIGIO signals. Due to the
            # nature of (SIGIO) signals more than one signal may be delivered
            # and this is a big problem when you want to do more than just call
            # sys.exit(). The alternative to this would be signal.pause() but
            # that function has an inherent race condition. To fix that race
            # condition there is sigsuspend() but this function is not
            # available in the Python standard library.
            waiter = WaitForRead()
            # If we get killed we need to make sure we take the subprocess
            # down with us, otherwise the subprocess may still be reading
            # from the character device when we are restarted and that's a
            # problem because the character device doesn't allow multiple
            # readers; all but the first reader will get the error
            # `IOError: [Errno 16] Device or resource busy'.
            with GracefulShutdown():
                try:
                    # Start the subprocess.
                    waiter.start()
                    # Connect the file descriptor to the subprocess.
                    fcntl.fcntl(self.conn_handle, fcntl.F_SETOWN, waiter.pid)
                    # The channel may have become connected after we last got an empty
                    # read but before we spawned our subprocess, so check one more
                    # time to make sure.
                    data = self.conn_handle.readline()
                    if data:
                        break
                    # If there is still no data available we'll wait for the
                    # subprocess to indicate that data has become available.
                    waiter.join()
                    # Let's see if the subprocess is right :-)
                    data = self.conn_handle.readline()
                    if data:
                        break
                finally:
                    logger.debug("Terminating subprocess with process id %i ..", waiter.pid)
                    waiter.terminate()
            # If the convoluted way to simulate blocking reads above ever
            # fails we don't want this method to turn into a `busy loop'.
            logger.debug("Blocking read emulation seems to have failed, falling back to 1 second polling interval ..")
            time.sleep(1)
        logger.debug("Read %i bytes from %s: %r", len(data), self.conn_label, data)
        return data


class WaitForRead(multiprocessing.Process):

    """Used by :func:`GuestAgent.raw_readline()` to implement blocking reads."""

    def run(self):
        """Endless loop that waits for one or more ``SIGIO`` signals to arrive."""
        logger.debug("Installing SIGIO signal handler ..")
        signal.signal(signal.SIGIO, self.signal_handler)
        timer = Timer()
        for seconds in itertools.count():
            logger.debug("Waiting for SIGIO signal (%s) ..", timer)
            time.sleep(seconds)

    def signal_handler(self, signal_number, frame):
        """Signal handler for ``SIGIO`` signals that immediately exits the process."""
        sys.exit(0)


def find_character_device(port_name):
    """
    Find the character device for the given port name.

    :param port_name: The name of the virtio port (a string).
    :returns: The absolute pathname of a character device (a string).
    :raises: :exc:`Exception` when the character device cannot be found.
    """
    root = '/sys/class/virtio-ports'
    logger.debug("Automatically selecting appropriate character device based on %s ..", root)
    for entry in os.listdir(root):
        name_file = os.path.join(root, entry, 'name')
        if os.path.isfile(name_file):
            with open(name_file) as handle:
                contents = handle.read().strip()
            if contents == port_name:
                character_device = '/dev/%s' % entry
                logger.debug("Selected character device: %s", character_device)
                return character_device
    raise Exception(compact("""
        Failed to select the appropriate character device for the port name
        {name}! This is probably caused by a configuration issue on either the
        QEMU host or inside the QEMU guest. Please refer to the following web
        page for help: http://negotiator.readthedocs.org/en/latest/#character-device-detection-fails
    """, name=repr(port_name)))
