# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
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
import os
import socket

# External dependencies.
from negotiator_common import NegotiatorInterface, compact

# Semi-standard module versioning.
__version__ = '0.1'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)

# The location of the directory containing the UNIX sockets created by QEMU.
DEFAULT_CHANNEL_DIRECTORY = '/var/lib/libvirt/qemu/channel/target'

# The filename suffix of the UNIX sockets created by QEMU. This is the channel
# target name in the QEMU guest configuration.
DEFAULT_CHANNEL_NAME = 'negotiator-channel.0'


class GuestChannel(NegotiatorInterface):

    """
    The host side of the channel connecting KVM/QEMU hosts and guests.

    The documentation of this class defines no public methods although
    :py:class:`GuestChannel` is the external API of the negotiator project. The
    reason for this is that calls to unknown :py:class:`GuestChannel` methods
    are automatically relayed to the remote side running on a KVM/QEMU guest.
    For this reason you should refer to the public methods implemented by the
    :py:class:`.GuestAgent` class.
    """

    def __init__(self, guest_name=None, unix_socket=None):
        """
        Initialize a negotiator host agent.

        :param guest_name: The name of the guest that we should connect to (a
                           string, optional).
        :param unix_socket: The absolute pathname of the UNIX socket that we
                            should connect to (a string, optional).
        :raises: :py:exc:`exceptions.ValueError` when neither ``guest_name``
                 nor ``unix_socket`` is given.
        """
        # Make sure either the guest name or the UNIX socket was given.
        if not guest_name and not unix_socket:
            raise ValueError(compact("""
                Please provide either the name of a QEMU guest or the absolute
                pathname of the UNIX socket connected to a QEMU guest!
            """))
        # Figure out the absolute pathname of the UNIX socket?
        if not unix_socket:
            unix_socket = os.path.join(DEFAULT_CHANNEL_DIRECTORY, '%s.%s' % (guest_name, DEFAULT_CHANNEL_NAME))
        # Connect to the UNIX socket.
        logger.debug("Connecting to UNIX socket: %s", unix_socket)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(unix_socket)
        # Initialize the super class, passing it a file like object connected
        # to the character device in read/write mode.
        super(GuestChannel, self).__init__(handle=self.socket.makefile(),
                                           label="UNIX socket %s" % unix_socket)
