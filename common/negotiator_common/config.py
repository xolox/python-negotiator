# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 24, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_common.config`` - Configuration defaults
=====================================================

.. data:: CHANNELS_DIRECTORY

   The pathname of the directory containing the host side of each channel.
   Defaults to ``/var/lib/libvirt/qemu/channel/target``.

.. data:: USER_COMMANDS_DIRECTORY

   The pathname of the directory containing user defined commands that 'the
   other side' can invoke through Negotiator. Defaults to
   ``/usr/lib/negotiator/commands``.

.. data:: GUEST_TO_HOST_CHANNEL_NAME

   The name of the channel that's used for communication initiated by the
   guest. Defaults to ``negotiator-guest-to-host.0``.

.. data:: HOST_TO_GUEST_CHANNEL_NAME

   The name of the channel that's used for communication initiated by the
   host. Defaults to ``negotiator-host-to-guest.0``.
"""

import os

CHANNELS_DIRECTORY = '/var/lib/libvirt/qemu/channel/target'
USER_COMMANDS_DIRECTORY = '/usr/lib/negotiator/commands'
BUILTIN_COMMANDS_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
GUEST_TO_HOST_CHANNEL_NAME = 'negotiator-guest-to-host.0'
HOST_TO_GUEST_CHANNEL_NAME = 'negotiator-host-to-guest.0'
