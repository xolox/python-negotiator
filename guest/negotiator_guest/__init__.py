# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 24, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_guest`` - The guest agent daemon
=============================================

This module implements the guest agent, the Python daemon process that's always
running inside KVM/QEMU guests.
"""

# Standard library modules.
import logging
import os

# External dependencies.
from negotiator_common import NegotiatorInterface
from negotiator_common.utils import compact

# Semi-standard module versioning.
__version__ = '0.5.2'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class GuestAgent(NegotiatorInterface):

    """Implementation of the daemon running inside KVM/QEMU guests."""

    def __init__(self, character_device):
        """
        Initialize a negotiator guest agent.

        :param character_device: The absolute pathname of the character device
                                 that we should use to connect to the host (a
                                 string).
        """
        # Initialize the super class, passing it a file like object connected
        # to the character device in read/write mode.
        super(GuestAgent, self).__init__(handle=open(character_device, 'r+'),
                                         label="character device %s" % character_device)


def find_character_device(port_name):
    """
    Find the character device for the given port name.

    :param port_name: The name of the virtio port (a string).
    :returns: The absolute pathname of a character device (a string).
    :raises: :py:exc:`Exception` when the character device cannot be found.
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
