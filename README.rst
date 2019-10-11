Scriptable KVM/QEMU guest agent implemented in Python
=====================================================

The Python packages negotiator-host_, negotiator-guest_ and negotiator-common_
together implement a scriptable KVM_/QEMU_ guest agent infrastructure in
Python. This infrastructure supports realtime bidirectional communication
between Linux_ hosts and guests which allows the hosts and guests to invoke
user defined commands on 'the other side'.

Because the user defines the commands that hosts and guests can execute, the
user controls the amount of influence that hosts and guests have over each
other (there are several built-in commands, these are all read only).

.. contents::

Status
------

Some points to consider:

- The Negotiator project does what I expect from it: realtime bidirectional
  communication between Linux based KVM/QEMU hosts and guests.

- The project doesn't have an automated test suite, although its functionality
  has been extensively tested during development and is being used in a
  production environment on more than 100 virtual machines (for non-critical
  tasks).

- The project has not been peer reviewed with regards to security. My primary
  use case is KVM/QEMU hosts and guests that trust each other to some extent
  (think private clouds, not shared hosting :-).

Installation
------------

The `negotiator` packages and their dependencies are compatible with Python 2.7
and newer and are all pure Python. This means you don't need a compiler
toolchain to install the `negotiator` packages. This is a design decision and
so won't be changed.

.. contents::
   :local:

On KVM/QEMU hosts
~~~~~~~~~~~~~~~~~

Here's how to install the negotiator-host_ package on your host(s):

.. code-block:: bash

   $ sudo pip install negotiator-host

If you prefer you can install the Python package in a virtual environment:

.. code-block:: bash

   $ sudo apt-get install --yes python-virtualenv
   $ virtualenv /tmp/negotiator-host
   $ source /tmp/negotiator-host/bin/activate
   $ pip install negotiator-host

After installation the ``negotiator-host`` program is available. The usage
message will help you get started, try the ``--help`` option. Now you need to
find a way to run the ``negotiator-host`` command as a daemon. I have good
experiences with supervisord_, here's how to set that up:

.. code-block:: bash

   $ sudo apt-get install --yes supervisor
   $ sudo tee /etc/supervisor/conf.d/negotiator-host.conf >/dev/null << EOF
   [program:negotiator-host]
   command = /usr/local/bin/negotiator-host --daemon
   autostart = True
   stdout_logfile = /var/log/negotiator-host.log
   stderr_logfile = /var/log/negotiator-host.log
   EOF
   $ sudo supervisorctl update negotiator-host

On KVM/QEMU guests
~~~~~~~~~~~~~~~~~~

Install the negotiator-guest_ package on your guest(s):

.. code-block:: bash

   $ sudo pip install negotiator-guest

If you prefer you can install the Python package in a virtual environment:

.. code-block:: bash

   $ sudo apt-get install --yes python-virtualenv
   $ virtualenv /tmp/negotiator-guest
   $ source /tmp/negotiator-guest/bin/activate
   $ pip install negotiator-guest

After installation you need to find a way to run the ``negotiator-guest``
command as a daemon. I have good experiences with supervisord_, here's how
to set that up:

.. code-block:: bash

   $ sudo apt-get install --yes supervisor
   $ sudo tee /etc/supervisor/conf.d/negotiator-guest.conf >/dev/null << EOF
   [program:negotiator-guest]
   command = /usr/local/bin/negotiator-guest --daemon
   autostart = True
   stdout_logfile = /var/log/negotiator-guest.log
   stderr_logfile = /var/log/negotiator-guest.log
   EOF
   $ sudo supervisorctl update negotiator-guest

Getting started
---------------

If the instructions below are not enough to get you started, take a look at the
*Debugging* section below for hints about what to do when things don't work as
expected.

1. First you have to add two virtual devices to your QEMU guest. You can do so
   by editing the guest's XML definition file. On Ubuntu Linux KVM/QEMU hosts
   these files are found in the directory ``/etc/libvirt/qemu``. Open the file
   in your favorite text editor (Vim? :-) and add the the following XML snippet
   inside the ``<devices>`` section:

   .. code-block:: xml

      <channel type='unix'>
         <source mode='bind' path='/var/lib/libvirt/qemu/channel/target/GUEST_NAME.negotiator-host-to-guest.0' />
         <target type='virtio' name='negotiator-host-to-guest.0' />
      </channel>

      <channel type='unix'>
         <source mode='bind' path='/var/lib/libvirt/qemu/channel/target/GUEST_NAME.negotiator-guest-to-host.0' />
         <target type='virtio' name='negotiator-guest-to-host.0' />
      </channel>

   Replace ``GUEST_NAME`` with the name of your guest in both places. If you
   use libvirt 1.0.6 or newer (you can check with ``virsh --version``) you can
   omit the ``path='...'`` attribute because libvirt will fill it in
   automatically when it reloads the guest's XML definition file (in step 2).

2. After adding the configuration snippet you have to activate it:

   .. code-block:: bash

      $ sudo virsh define /etc/libvirt/qemu/GUEST_NAME.xml

3. Now you need to shut down the guest and then start it again:

   .. code-block:: bash

      $ sudo virsh shutdown --mode acpi GUEST_NAME
      $ sudo virsh start GUEST_NAME

   Note that just rebooting the guest will not add the new virtual devices, you
   have to actually stop the guest and then start it again!

4. Now go and create some scripts in ``/usr/lib/negotiator/commands`` and try
   to execute them from the other side! Once you start writing your own
   commands it's useful to know that commands on the KVM/QEMU host side have
   access to some `environment variables`_.

Usage
-----

This section documents the command line interfaces of the programs running on
hosts and guests. For information on the Python API please refer to the online
documentation on `Read the Docs`_.

.. contents::
   :local:

The negotiator-host program
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. A DRY solution to avoid duplication of the `negotiator-host --help' text:
..
.. [[[cog
.. from humanfriendly.usage import inject_usage
.. inject_usage('negotiator_host.cli')
.. ]]]

**Usage:** `negotiator-host [OPTIONS] GUEST_NAME`

Communicate from a KVM/QEMU host system with running guest systems using a
guest agent daemon running inside the guests.

**Supported options:**

.. csv-table::
   :header: Option, Description
   :widths: 30, 70


   "``-g``, ``--list-guests``",List the names of the guests that have the appropriate channel.
   "``-c``, ``--list-commands``",List the commands that the guest exposes to its host.
   "``-e``, ``--execute=COMMAND``","Execute the given command inside GUEST_NAME. The standard output stream of
   the command inside the guest is intercepted and copied to the standard
   output stream on the host. If the command exits with a nonzero status code
   the negotiator-host program will also exit with a nonzero status code."
   "``-t``, ``--timeout=SECONDS``","Set the number of seconds before a remote call without a response times
   out. A value of zero disables the timeout (in this case the command can
   hang indefinitely). The default is 10 seconds."
   "``-d``, ``--daemon``",Start the host daemon that answers real time requests from guests.
   "``-v``, ``--verbose``",Increase logging verbosity (can be repeated).
   "``-q``, ``--quiet``",Decrease logging verbosity (can be repeated).
   "``-h``, ``--help``",Show this message and exit.

.. [[[end]]]

The negotiator-guest program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. A DRY solution to avoid duplication of the `negotiator-host --help' text:
..
.. [[[cog
.. from humanfriendly.usage import inject_usage
.. inject_usage('negotiator_guest.cli')
.. ]]]

**Usage:** `negotiator-guest [OPTIONS]`

Communicate from a KVM/QEMU guest system to its host or start the
guest daemon to allow the host to execute commands on its guests.

**Supported options:**

.. csv-table::
   :header: Option, Description
   :widths: 30, 70


   "``-l``, ``--list-commands``",List the commands that the host exposes to its guests.
   "``-e``, ``--execute=COMMAND``","Execute the given command on the KVM/QEMU host. The standard output stream
   of the command on the host is intercepted and copied to the standard output
   stream on the guest. If the command exits with a nonzero status code the
   negotiator-guest program will also exit with a nonzero status code."
   "``-d``, ``--daemon``","Start the guest daemon. When using this command line option the
   ""negotiator-guest"" program never returns (unless an unexpected error
   condition occurs)."
   "``-t``, ``--timeout=SECONDS``","Set the number of seconds before a remote call without a response times
   out. A value of zero disables the timeout (in this case the command can
   hang indefinitely). The default is 10 seconds."
   "``-c``, ``--character-device=PATH``","By default the appropriate character device is automatically selected based
   on /sys/class/virtio-ports/\*/name. If the automatic selection doesn't work,
   you can set the absolute pathname of the character device that's used to
   communicate with the negotiator-host daemon running on the KVM/QEMU host."
   "``-v``, ``--verbose``",Increase logging verbosity (can be repeated).
   "``-q``, ``--quiet``",Decrease logging verbosity (can be repeated).
   "``-h``, ``--help``",Show this message and exit.

.. [[[end]]]

Debugging
---------

This section contains hints about what to do when things don't work as
expected.

.. contents::
   :local:

Broken channels on KVM/QEMU hosts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Whether you want to get the official QEMU guest agent or the Negotiator project
running, you will need a working bidirectional channel. I'm testing Negotiator
on an Ubuntu 14.04 KVM/QEMU host and I needed several changes to get things
working properly:

.. code-block:: bash

   $ CHANNELS_DIRECTORY=/var/lib/libvirt/qemu/channel/target
   $ sudo mkdir -p $CHANNELS_DIRECTORY
   $ sudo chown libvirt-qemu:kvm $CHANNELS_DIRECTORY

The above should be done by the KVM/QEMU system packages if you ask me, but
anyway. On top of this if you are running Ubuntu with AppArmor enabled (the
default) you may need to apply the following patch:

.. code-block:: bash

   $ diff -u /etc/apparmor.d/abstractions/libvirt-qemu.orig /etc/apparmor.d/abstractions/libvirt-qemu
   --- /etc/apparmor.d/abstractions/libvirt-qemu.orig      2015-09-19 12:46:54.316593334 +0200
   +++ /etc/apparmor.d/abstractions/libvirt-qemu   2015-09-24 14:43:43.642064576 +0200
   @@ -49,6 +49,9 @@
      /run/shm/ r,
      owner /run/shm/spice.* rw,

   +  # Local modification to enable the QEMU guest agent.
   +  owner /var/lib/libvirt/qemu/channel/target/* rw,
   +
      # 'kill' is not required for sound and is a security risk. Do not enable
      # unless you absolutely need it.
      deny capability kill,

Again this should just be part of the KVM/QEMU system packages, but whatever.
The Negotiator project is playing with new-ish functionality so I pretty much
know to expect sharp edges :-)

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

The scriptable guest agent infrastructure uses `the same mechanism`_ that the
official QEMU guest agent does:

- Inside the guest special character devices are created that allow reading and
  writing. These character devices are ``/dev/vport[0-9]p[0-9]``.

- On the host UNIX domain sockets are created that are connected to the
  character devices inside the guest. On Ubuntu Linux KVM/QEMU hosts,
  these UNIX domain sockets are created in the directory
  ``/var/lib/libvirt/qemu/channel/target``.

Contact
-------

The latest version of `negotiator` is available on PyPI_ and GitHub_. You can
find the documentation on `Read The Docs`_. For bug reports please create an
issue on GitHub_. If you have questions, suggestions, etc. feel free to send me
an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2019 Peter Odding.

.. External references:
.. _environment variables: http://negotiator.readthedocs.org/en/latest/#negotiator_host.GuestChannel.prepare_environment
.. _GitHub: https://github.com/xolox/python-negotiator
.. _KVM: https://en.wikipedia.org/wiki/Kernel-based_Virtual_Machine
.. _Linux: https://en.wikipedia.org/wiki/Linux
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _negotiator-common: https://pypi.python.org/pypi/negotiator-common
.. _negotiator-guest: https://pypi.python.org/pypi/negotiator-guest
.. _negotiator-host: https://pypi.python.org/pypi/negotiator-host
.. _official guest agent: http://wiki.libvirt.org/page/Qemu_guest_agent
.. _peter@peterodding.com: peter@peterodding.com
.. _PyPI: https://pypi.python.org/pypi/negotiator-host
.. _QEMU: https://en.wikipedia.org/wiki/QEMU
.. _Read The Docs: http://negotiator.readthedocs.org/en/latest/
.. _supervisord: http://supervisord.org/
.. _the same mechanism: http://www.linux-kvm.org/page/VMchannel_Requirements
