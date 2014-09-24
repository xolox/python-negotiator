Generic KVM/QEMU guest agent implemented in Python
==================================================

The Python packages negotiator-host_, negotiator-guest_ and negotiator-common_
together implement a generic KVM/QEMU guest agent infrastructure in Python.
This infrastructure enables realtime bidirectional communication between hosts
and guests which allows user defined metadata to be transferred between them.

.. contents::

Status
------

Some points to consider:

- The Negotiator project does what I expect from it: realtime bidirectional
  communication between KVM/QEMU hosts and guests.

- The project doesn't have an automated test suite yet, although its
  functionality has been extensively tested during development.

- The project has not been peer reviewed with regards to security. My primary
  use case is KVM/QEMU hosts and guests that trust each other to some extent
  (think private clouds, not shared hosting :-).

Installation
------------

The ``negotiator`` packages and their dependencies are compatible with Python
2.6 and newer and are all pure Python. This means you don't need a compiler
toolchain to install the ``negotiator`` packages. This is a design decision and
so won't be changed.

On KVM/QEMU hosts
~~~~~~~~~~~~~~~~~

Here's how to install the negotiator-host_ package on your host(s)::

  sudo pip install negotiator-host

If you prefer you can install the Python package in a virtual environment::

  sudo apt-get install --yes python-virtualenv
  virtualenv /tmp/negotiator-host
  source /tmp/negotiator-host/bin/activate
  pip install negotiator-host

After installation the ``negotiator-host`` program is available. The usage
message will help you get started, try the ``--help`` option. Now you need to
find a way to run the ``negotiator-host`` command as a daemon. I have good
experiences with ``supervisord``, here's how to set that up::

  sudo apt-get install --yes supervisor
  cat > /etc/supervisor/conf.d/negotiator-host.conf << EOF
  [program:negotiator-host]
  command = /usr/local/bin/negotiator-host --daemon
  autostart = True
  redirect_stderr = True
  stdout_logfile = /var/log/negotiator-host.log
  EOF
  supervisorctl update negotiator-host

On KVM/QEMU guests
~~~~~~~~~~~~~~~~~~

Install the negotiator-guest_ package on your guest(s)::

  sudo pip install negotiator-guest

If you prefer you can install the Python package in a virtual environment::

  sudo apt-get install --yes python-virtualenv
  virtualenv /tmp/negotiator-guest
  source /tmp/negotiator-guest/bin/activate
  pip install negotiator-guest

After installation you need to find a way to run the ``negotiator-guest``
command as a daemon. I have good experiences with ``supervisord``, here's how
to set that up::

  sudo apt-get install --yes supervisor
  cat > /etc/supervisor/conf.d/negotiator-guest.conf << EOF
  [program:negotiator-guest]
  command = /usr/local/bin/negotiator-guest --daemon
  autostart = True
  redirect_stderr = True
  stdout_logfile = /var/log/negotiator-guest.log
  EOF
  supervisorctl update negotiator-guest

Getting started
---------------

If the instructions below are not enough to get you started, take a look at the
*Debugging* section below for hints about what to do when things don't work as
expected.

1. First you have to add two virtual devices to your QEMU guest. You can do so
   by editing the guest's XML definition file. On Ubuntu Linux KVM/QEMU hosts
   these files are found in the directory ``/etc/libvirt/qemu``. Open the file
   in your favorite text editor (Vim? :-) and add the the following XML snippet
   inside the ``<devices>`` section::

     <channel type='unix'>
        <source mode='bind' />
        <target type='virtio' name='negotiator-host-to-guest.0' />
     </channel>

     <channel type='unix'>
        <source mode='bind' />
        <target type='virtio' name='negotiator-guest-to-host.0' />
     </channel>

   You don't have to supply channel source path attributes, they should be
   filled in automatically by KVM/QEMU/libvirt when it notices that you've
   added the devices (in step 2).

2. After adding the configuration snippet you have to activate it::

     virsh define /etc/libvirt/qemu/NAME-OF-GUEST.xml

3. Now you need to shut down the guest and then start it again::

     virsh shutdown --mode acpi NAME-OF-GUEST
     virsh start NAME-OF-GUEST

   Note that just rebooting the guest will not add the new virtual devices, you
   have to actually stop the guest and then start it again!

4. Now go and create some scripts in ``/usr/lib/negotiator/commands`` and try
   to execute them from the other side! Once you start writing your own
   commands it's useful to know that commands on the KVM/QEMU host side have
   access to some `environment variables`_.

Debugging
---------

This section contains hints about what to do when things don't work as
expected.

Broken channels on KVM/QEMU hosts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Whether you want to get the official QEMU guest agent or the Negotiator project
running, you will need a working bidirectional channel. I'm testing Negotiator
on an Ubuntu 14.04 KVM/QEMU host and I needed several changes to get things
working properly::

  CHANNELS_DIRECTORY=/var/lib/libvirt/qemu/channel/target
  sudo mkdir -p $CHANNELS_DIRECTORY
  sudo chown libvirt-qemu:kvm $CHANNELS_DIRECTORY

The above should be done by KVM/QEMU if you ask me, but anyway. On top of this
if you are running Ubuntu with AppArmor enabled (the default) you will need to
apply the following patch::

  root@trusty-kvm-host# diff -u /etc/apparmor.d/abstractions/libvirt-qemu.orig /etc/apparmor.d/abstractions/libvirt-qemu
  --- /etc/apparmor.d/abstractions/libvirt-qemu.orig      2014-09-19 12:46:54.316593334 +0200
  +++ /etc/apparmor.d/abstractions/libvirt-qemu   2014-09-24 14:43:43.642064576 +0200
  @@ -49,6 +49,9 @@
     /run/shm/ r,
     owner /run/shm/spice.* rw,

  +  # Local modification to enable the QEMU guest agent.
  +  owner /var/lib/libvirt/qemu/channel/target/* rw,
  +
     # 'kill' is not required for sound and is a security risk. Do not enable
     # unless you absolutely need it.
     deny capability kill,

Again this should just be part of the KVM/QEMU packages, but whatever. The
Negotiator project is playing with new-ish functionality so I pretty much know
to expect sharp edges :-)

Character device detection fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the ``negotiator-guest`` program fails to detect the correct character
devices it will complain loudly and point you here. Here are some of things
I've run into that can cause this:

- The virtual channel(s) have not been correctly configured or the correct
  configuration hasn't been applied yet. Please carefully follow the
  instructions in the *Getting started* section above.

- The kernel module ``virtio_console`` is not loaded because it is not
  available in your kernel. You can check by using the ``lsmod`` command. If
  the module is not loaded you'll need to install and boot to a kernel that
  does have the module.

Why another guest agent?
------------------------

The QEMU project provides an `official guest agent`_ and this agent is very
useful to increase integration between QEMU hosts and guests. However the
official QEMU guest agent has two notable shortcomings (for me at least):

**Extensibility**
  The official QEMU guest agent has some generic mechanisms like being able to
  write files inside guests, but this is a far cry from a generic, extensible
  architecture. Ideally given the host and guest's permission we should be able
  to transfer arbitrary data and execute user defined logic on both sides.

**Platform support**
  Despite considerable effort I haven't been able to get a recent version of
  the QEMU guest agent running on older Linux distributions (e.g. Ubuntu Linux
  10.04). Older versions of the guest agent can be succesfully compiled for
  such distributions but don't support the features I require. By creating my
  own guest agent I have more control over platform support (given the
  primitives required for communication).

Note that my project in no way tries to replace the official QEMU guest agent.
For example I have no intention of implementing freezing and thawing of file
systems because the official agent already does that just fine :-). In other
words the two projects share a lot of ideas but have very different goals.

How does it work?
-----------------

The generic guest agent infrastructure uses `the same mechanism`_ that the
official QEMU guest agent does:

- Inside the guest special character devices are created that allow reading and
  writing. These character devices are ``/dev/vport[0-9]p[0-9]``.

- On the host UNIX domain sockets are created that are connected to the
  character devices inside the guest. On Ubuntu Linux KVM/QEMU hosts,
  these UNIX domain sockets are created in the directory
  ``/var/lib/libvirt/qemu/channel/target``.

Contact
-------

The latest version of ``negotiator`` is available on PyPI_ and GitHub_. For bug
reports please create an issue on GitHub_. If you have questions, suggestions,
etc. feel free to send me an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2014 Peter Odding.

.. External references:
.. _environment variables: http://negotiator.readthedocs.org/en/latest/#negotiator_host.GuestChannel.prepare_environment
.. _GitHub: https://github.com/xolox/python-negotiator
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _negotiator-common: https://pypi.python.org/pypi/negotiator-common
.. _negotiator-guest: https://pypi.python.org/pypi/negotiator-guest
.. _negotiator-host: https://pypi.python.org/pypi/negotiator-host
.. _official guest agent: http://wiki.libvirt.org/page/Qemu_guest_agent
.. _peter@peterodding.com: peter@peterodding.com
.. _PyPI: https://pypi.python.org/pypi/negotiator-host
.. _the same mechanism: http://www.linux-kvm.org/page/VMchannel_Requirements
