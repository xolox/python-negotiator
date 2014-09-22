# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_guest`` - The guest agent daemon
=============================================

This module implements the guest agent, the Python daemon process that's always
running inside KVM/QEMU guests.
"""

# Standard library modules.
import functools
import logging

# External dependencies.
from executor import execute
from negotiator_common import NegotiatorInterface

# Semi-standard module versioning.
__version__ = '0.1'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)

# Inject our logger into all execute() invocations.
execute = functools.partial(execute, logger=logger)

# The location of the default character device connected to the KVM/QEMU host.
DEFAULT_CHARACTER_DEVICE = '/dev/vport0p1'


class GuestAgent(NegotiatorInterface):

    """Implementation of the daemon running inside KVM/QEMU guests."""

    def __init__(self, character_device=DEFAULT_CHARACTER_DEVICE):
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

    def execute(self, *command, **options):
        """
        Execute an external command inside the guest.

        :param command: The program name and its arguments (one or more strings).
        :param check: If ``True`` (the default) then commands that exit with a
                      nonzero status will raise an exception.
        :param capture: If ``True`` (not the default) the output of the
                        external command is returned.
        :returns: Depending on the arguments any of these values can be returned:

                  - If ``check=True`` and ``capture=False`` (the default) then
                    nothing is returned, but an exception is raised if the
                    command exits with a nonzero status code.

                  - If ``check=False`` the return value is a boolean indicating
                    whether the command exited with status code zero.

                  - If ``capture=True`` and the command exits with status code
                    zero the output of the external command is returned as a
                    string.
        """
        return execute(*command, **options)

    def find_distributor_id(self):
        """
        Find the distributor ID using the lsb_release_ command.

        :returns: The distributor ID (a string like ``Ubuntu``).

        .. _lsb_release: http://linux.die.net/man/1/lsb_release
        """
        return execute('lsb_release', '--short', '--id', capture=True)

    def find_distribution_release(self):
        """
        Find the distribution release using the lsb_release_ command.

        :returns: The distribution release (a string like ``12.04``).
        """
        return execute('lsb_release', '--short', '--release', capture=True)

    def find_distribution_codename(self):
        """
        Find the distribution codename using the lsb_release_ command.

        :returns: The distribution codename (a string like ``precise``).

        .. _lsb_release: http://linux.die.net/man/1/lsb_release
        """
        return execute('lsb_release', '--short', '--codename', capture=True)

    def find_ip_addresses(self):
        """
        Find the IP addresses in use on the guest.

        :returns: A list of IP addresses (strings) in `CIDR notation`_.

        .. _CIDR notation: http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing#CIDR_notation
        """
        ip_addresses = []
        for line in execute('ip', 'addr', 'show', capture=True).splitlines():
            tokens = line.split()
            if tokens and tokens[0] == 'inet':
                ip_addresses.append(tokens[1])
        return ip_addresses
