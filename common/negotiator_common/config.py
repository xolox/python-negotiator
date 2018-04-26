# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: April 26, 2018
# URL: https://negotiator.readthedocs.org

"""Configuration defaults for the `negotiator` project."""

import os

CHANNELS_DIRECTORY = '/var/lib/libvirt/qemu/channel/target'
"""The pathname of the directory containing the host side of each channel."""

USER_COMMANDS_DIRECTORY = '/usr/lib/negotiator/commands'
"""
The pathname of the directory containing user defined commands
that 'the other side' can invoke through `negotiator`.
"""

BUILTIN_COMMANDS_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
"""The directory with built-in commands (a string)."""

GUEST_TO_HOST_CHANNEL_NAME = 'negotiator-guest-to-host.0'
"""The name of the channel that's used for communication initiated by the guest (a string)."""

HOST_TO_GUEST_CHANNEL_NAME = 'negotiator-host-to-guest.0'
"""The name of the channel that's used for communication initiated by the host (a string)."""

DEFAULT_TIMEOUT = 10
"""
The number of seconds to wait for a reply from the other side (an integer).

If more time elapses an exception is raised causing the process to exit with a
nonzero status code.
"""
