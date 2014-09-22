# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_common.config`` - Configuration defaults
=====================================================

.. data:: DEFAULT_CHANNEL_NAME

   The name that's used to identify the host and guest side of each channel.
   Defaults to ``negotiator-channel.0``.

.. data:: DEFAULT_CHANNEL_DIRECTORY

   The directory containing the host side of each channel. Defaults to
   ``/var/lib/libvirt/qemu/channel/target``.

.. data:: DEFAULT_CHARACTER_DEVICE

   The absolute pathname of the character device inside guests. Only used if
   automatic selection fails (which shouldn't happen). Defaults to
   ``/dev/vport0p1``.
"""

# The location of the default character device connected to the KVM/QEMU host.
DEFAULT_CHARACTER_DEVICE = '/dev/vport0p1'

# The location of the directory containing the UNIX sockets created by QEMU.
DEFAULT_CHANNEL_DIRECTORY = '/var/lib/libvirt/qemu/channel/target'

# The filename suffix of the UNIX sockets created by QEMU. This is the channel
# target name in the QEMU guest configuration.
DEFAULT_CHANNEL_NAME = 'negotiator-channel.0'
