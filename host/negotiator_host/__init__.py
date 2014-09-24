# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 24, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_host`` - Channel for communication with guests
===========================================================

This module implements the :py:class:`GuestChannel` class which provides the
host side of the channel between QEMU hosts and guests. Channel objects can be
used to query and command running guests.
"""

# Standard library modules.
import logging
import multiprocessing
import os
import socket
import stat
import time

# External dependencies.
from negotiator_common import NegotiatorInterface
from negotiator_common.config import CHANNELS_DIRECTORY, GUEST_TO_HOST_CHANNEL_NAME, HOST_TO_GUEST_CHANNEL_NAME

# Semi-standard module versioning.
__version__ = '0.5'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class HostDaemon(object):

    """The host daemon automatically manages a group of processes that handle "guest to host" calls."""

    def __init__(self, channel_directory=CHANNELS_DIRECTORY):
        """
        Initialize the host daemon.

        :param channel_directory: The pathname of the directory containing
                                  UNIX sockets connected to guests (a string).
        """
        self.active_channels = {}
        self.channel_directory = channel_directory
        self.enter_main_loop()

    def enter_main_loop(self):
        """Create and maintain active channels for all running guests."""
        while True:
            self.update_active_channels()
            time.sleep(10)

    def update_active_channels(self):
        """Automatically spawn subprocesses to maintain connections to all guests."""
        logger.debug("Checking for new/missing channels in %s ..", self.channel_directory)
        # Discover the available channels (by checking for UNIX socket files).
        available_channels = find_available_channels(self.channel_directory, GUEST_TO_HOST_CHANNEL_NAME).items()
        # Synchronize the set of active channels with the set of available channels.
        for key in set(self.active_channels) | set(available_channels):
            guest_name, unix_socket = key
            # Create channels for UNIX sockets that don't have one yet.
            if key not in self.active_channels:
                logger.info("Initializing channel to guest %s (UNIX socket %s) ..", guest_name, unix_socket)
                channel = AutomaticGuestChannel(guest_name=guest_name, unix_socket=unix_socket)
                channel.start()
                self.active_channels[key] = channel
            # Destroy channels whose UNIX socket has disappeared.
            if key not in available_channels:
                logger.info("Destroying channel to guest %s (UNIX socket %s) ..", guest_name, unix_socket)
                self.active_channels[key].terminate()
                self.active_channels.pop(key)


class AutomaticGuestChannel(multiprocessing.Process):

    """
    Thin wrapper for :py:class:`GuestChannel` that puts it in a separate process.

    Uses :py:class:`multiprocessing.Process` to isolate guest channels in
    separate processes.
    """

    def __init__(self, *args, **kw):
        """
        Initialize a :py:class:`GuestChannel` in a separate process.

        All positional arguments and keyword arguments are passed on to the
        :py:class:`GuestChannel` constructor.
        """
        # Initialize the super class.
        super(AutomaticGuestChannel, self).__init__()
        # Initialize the guest to host channel.
        self.channel = GuestChannel(*args, **kw)

    def run(self):
        """Start the main loop of the common negotiator interface."""
        self.channel.enter_main_loop()


class GuestChannel(NegotiatorInterface):

    """
    The host side of the channel connecting KVM/QEMU hosts and guests.

    See also :py:class:`AutomaticGuestChannel` which wraps
    :py:class:`GuestChannel` and puts it in its own process.
    """

    def __init__(self, guest_name, unix_socket=None):
        """
        Initialize a negotiator host agent.

        :param guest_name: The name of the guest to connect to (a string).
        :param unix_socket: The absolute pathname of the UNIX socket that we
                            should connect to (a string, optional).
        :raises: :py:exc:`exceptions.ValueError` when neither ``guest_name``
                 nor ``unix_socket`` is given.
        """
        self.guest_name = guest_name
        # Figure out the absolute pathname of the UNIX socket?
        if not unix_socket:
            unix_socket = os.path.join(CHANNELS_DIRECTORY, '%s.%s' % (self.guest_name, HOST_TO_GUEST_CHANNEL_NAME))
        # Connect to the UNIX socket.
        logger.debug("Opening UNIX socket: %s", unix_socket)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        logger.debug("Connecting to UNIX socket: %s", unix_socket)
        self.socket.connect(unix_socket)
        logger.debug("Successfully connected to UNIX socket!")
        # Initialize the super class, passing it a file like object connected
        # to the character device in read/write mode.
        super(GuestChannel, self).__init__(handle=self.socket.makefile(),
                                           label="UNIX socket %s" % unix_socket)

    def prepare_environment(self):
        """Prepare environment variables for command execution."""
        os.environ['NEGOTIATOR_GUEST'] = self.guest_name


def find_available_channels(directory, name):
    """
    Find available channels by checking for available UNIX sockets.

    :param directory: The pathname of the directory to search (a string).
    :param name: The name of the channel to search for (a string).
    :returns: A dictionary with KVM/QEMU guest names (strings) as keys and
              pathnames of UNIX sockets as values.
    """
    channels = {}
    suffix = '.%s' % name
    for entry in os.listdir(directory):
        if entry.endswith(suffix):
            pathname = os.path.join(directory, entry)
            if stat.S_ISSOCK(os.stat(pathname).st_mode):
                guest_name = entry[:-len(suffix)]
                channels[guest_name] = pathname
    return channels
