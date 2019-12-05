# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 11, 2019
# URL: https://negotiator.readthedocs.org

"""
Channel for communication with guests.

This module implements the :class:`GuestChannel` class which provides the
host side of the channel between QEMU hosts and guests. Channel objects can be
used to query and command running guests.
"""

# Standard library modules.
import logging
import multiprocessing
import os
import socket
import time
import xml.etree.ElementTree

# Modules included in our project.
from negotiator_common import NegotiatorInterface
from negotiator_common.config import GUEST_TO_HOST_CHANNEL_NAME, HOST_TO_GUEST_CHANNEL_NAME, SUPPORTED_CHANNEL_NAMES
from negotiator_common.utils import GracefulShutdown

# External dependencies.
from executor import ExternalCommandFailed, execute

# Semi-standard module versioning.
__version__ = '0.12'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class HostDaemon(object):

    """The host daemon automatically manages a group of processes that handle "guest to host" calls."""

    def __init__(self):
        """Initialize the host daemon."""
        self.workers = {}
        self.guests_to_ignore = set()
        self.enter_main_loop()

    def enter_main_loop(self):
        """Create and maintain active channels for all running guests."""
        with GracefulShutdown():
            try:
                while True:
                    self.update_workers()
                    time.sleep(10)
            finally:
                for channel in self.workers.values():
                    channel.terminate()

    def update_workers(self):
        """Automatically spawn subprocesses (workers) to maintain connections to all guests."""
        logger.debug("Synchronizing workers to channels ..")
        running_guests = set(find_running_guests())
        self.cleanup_workers(running_guests)
        self.spawn_workers(running_guests)

    def cleanup_workers(self, running_guests):
        """Cleanup crashed workers and workers for guests that are no longer running."""
        for guest_name in list(self.workers.keys()):
            # Check for and cleanup crashed workers.
            if not self.workers[guest_name].is_alive():
                logger.warning("[%s] Cleaning up crashed worker ..", guest_name)
                self.workers.pop(guest_name)
            # Check for and terminate workers for guests that are no longer running.
            if guest_name not in running_guests:
                logger.info("[%s] Terminating worker because guest is no longer running ..", guest_name)
                self.workers[guest_name].terminate()
                self.workers.pop(guest_name)

    def spawn_workers(self, running_guests):
        """Spawn new workers on demand (ignoring guests known not to support negotiator)."""
        for guest_name in sorted(running_guests - self.guests_to_ignore):
            if guest_name not in self.workers:
                available_channels = find_channels_of_guest(guest_name)
                if GUEST_TO_HOST_CHANNEL_NAME in available_channels:
                    logger.info("[%s] Initializing worker for guest ..", guest_name)
                    self.workers[guest_name] = AutomaticGuestChannel(
                        guest_name=guest_name, unix_socket=available_channels[GUEST_TO_HOST_CHANNEL_NAME],
                    )
                    self.workers[guest_name].start()
                else:
                    # Don't keep running 'virsh dumpxml' for this guest when we
                    # know that it is not configured to support negotiator.
                    logger.info("[%s] Doesn't support negotiator, adding to ignore list ..", guest_name)
                    self.guests_to_ignore.add(guest_name)


class AutomaticGuestChannel(multiprocessing.Process):

    """
    Thin wrapper for :class:`GuestChannel` that puts it in a separate process.

    Uses :class:`multiprocessing.Process` to isolate guest channels in
    separate processes.
    """

    def __init__(self, guest_name, unix_socket):
        """
        Initialize a :class:`GuestChannel` in a separate process.

        :param guest_name: The name of the guest to connect to (a string).
        :param unix_socket: The absolute pathname of the UNIX socket that we
                            should connect to (a string).
        """
        # Initialize the super class.
        super(AutomaticGuestChannel, self).__init__()
        # Store the arguments to the constructor.
        self.guest_name = guest_name
        self.unix_socket = unix_socket

    def run(self):
        """Start the main loop of the common negotiator interface."""
        try:
            # Initialize the guest to host channel.
            channel = GuestChannel(self.guest_name, self.unix_socket)
            # Wait for messages from the other side.
            channel.enter_main_loop()
        except GuestChannelInitializationError:
            # We know what the reason is here, so there's no need to log a noisy traceback.
            logger.error("[%s] Failed to initialize channel to guest! (worker will respawn in a bit)", self.guest_name)
        except Exception:
            # Unhandled exceptions get a traceback in the log output to make it easier to debug problems.
            logger.exception(
                "[%s] Caught exception while connecting to guest! (worker will respawn in a bit)",
                self.guest_name,
            )


class GuestChannel(NegotiatorInterface):

    """
    The host side of the channel connecting KVM/QEMU hosts and guests.

    See also :class:`AutomaticGuestChannel` which wraps
    :class:`GuestChannel` and puts it in its own process.
    """

    def __init__(self, guest_name, unix_socket=None):
        """
        Initialize a negotiator host agent.

        :param guest_name: The name of the guest to connect to (a string).
        :param unix_socket: The absolute pathname of the UNIX socket that we
                            should connect to (a string, optional).
        """
        self.guest_name = guest_name
        # Figure out the pathname of the UNIX socket?
        if not unix_socket:
            available_channels = find_channels_of_guest(guest_name)
            if HOST_TO_GUEST_CHANNEL_NAME in available_channels:
                logger.debug("[%s] Found UNIX socket using channel discovery.", self.guest_name)
                unix_socket = available_channels[HOST_TO_GUEST_CHANNEL_NAME]
            else:
                msg = "No UNIX socket pathname provided and auto-detection failed!"
                raise GuestChannelInitializationError(msg)
        # Connect to the UNIX socket.
        logger.debug("[%s] Opening UNIX socket (%s) ..", self.guest_name, unix_socket)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            logger.debug("[%s] Connecting to UNIX socket ..", self.guest_name)
            self.socket.connect(unix_socket)
        except Exception:
            raise GuestChannelInitializationError("Guest refused connection attempt!")
        logger.debug("[%s] Successfully connected to UNIX socket!", self.guest_name)
        # Initialize the super class, passing it a file like object connected
        # to the character device in read/write mode.
        super(GuestChannel, self).__init__(handle=self.socket.makefile(),
                                           label="UNIX socket %s" % unix_socket)

    def prepare_environment(self):
        """
        Prepare environment variables for command execution on KVM/QEMU hosts.

        The following environment variables are currently exposed to commands:

        ``$NEGOTIATOR_GUEST``
          The name of the KVM/QEMU guest that invoked the command.
        """
        os.environ['NEGOTIATOR_GUEST'] = self.guest_name


class GuestChannelInitializationError(Exception):

    """Exception raised by :class:`GuestChannel` when socket initialization fails."""


class GuestDiscoveryError(Exception):

    """Exception raised by :func:`find_running_guests()` when ``virsh list`` fails."""


def find_supported_guests():
    """
    Find guests supporting the negotiator interface.

    :returns: A generator of strings with guest names.

    This function uses :func:`find_running_guests()` to determine which guests
    are currently running and then uses :func:`find_channels_of_guest()` to
    determine which guests support the negotiator interface.
    """
    for guest_name in sorted(find_running_guests()):
        matches = find_channels_of_guest(guest_name)
        if HOST_TO_GUEST_CHANNEL_NAME in matches:
            yield guest_name


def find_channels_of_guest(guest_name):
    """
    Find the pathnames of the channels associated to a guest.

    :param guest_name: The name of the guest (a string).
    :returns: A dictionary with channel names (strings) as keys and pathnames
              of UNIX socket files (strings) as values. If no channels are
              detected an empty dictionary will be returned.

    This function uses ``virsh dumpxml`` and parses the XML output to
    determine the pathnames of the channels associated to the guest.
    """
    logger.debug("Discovering '%s' channels using 'virsh dumpxml' command ..", guest_name)
    domain_xml = execute('virsh', 'dumpxml', guest_name, capture=True)
    parsed_xml = xml.etree.ElementTree.fromstring(domain_xml)
    channels = {}
    for channel in parsed_xml.findall('devices/channel'):
        if channel.attrib.get('type') == 'unix':
            source = channel.find('source')
            target = channel.find('target')
            if source is not None and target is not None and target.attrib.get('type') == 'virtio':
                name = target.attrib.get('name')
                path = source.attrib.get('path')
                if name in SUPPORTED_CHANNEL_NAMES:
                    channels[name] = path
    if channels:
        logger.debug("Discovered '%s' channels: %s", guest_name, channels)
    else:
        logger.debug("No channels found for guest '%s'.", guest_name)
    return channels


def find_running_guests():
    """
    Find the names of the guests running on the current host.

    This function parses the output of the ``virsh list`` command instead of
    using the libvirt API because of two reasons:

    1. I'm under the impression that the libvirt API is still very much in flux
       and large changes are still being made, so it's not the most stable
       foundation for Negotiator to find running guests.

    2. The Python libvirt API needs to match the version of the libvirt API on
       the host system and there is AFAIK no obvious way to express this in the
       ``setup.py`` script of Negotiator.

    :returns: A generator of strings.
    :raises: :exc:`GuestDiscoveryError` when ``virsh list`` fails.
    """
    try:
        logger.debug("Discovering running guests using 'virsh list' command ..")
        output = execute('virsh', '--quiet', 'list', '--all', capture=True, logger=logger)
    except ExternalCommandFailed:
        raise GuestDiscoveryError("The 'virsh list' command failed! Most likely libvirtd isn't running...")
    else:
        for line in output.splitlines():
            logger.debug("Parsing 'virsh list' output: %r", line)
            try:
                vm_id, vm_name, vm_status = line.split(None, 2)
                if vm_status == 'running':
                    yield vm_name
            except Exception:
                logger.warning("Failed to parse 'virsh list' output! (%r)", line)
