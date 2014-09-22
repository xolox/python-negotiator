Generic KVM/QEMU guest agent implemented in Python
==================================================

The Python packages negotiator-host_, negotiator-guest_ and negotiator-common_
together implement a generic KVM/QEMU guest agent infrastructure in Python.
This infrastructure enables realtime bidirectional communication between hosts
and guests which allows user defined metadata to be transferred between them.

.. contents::

Status
------

Right now this project is a proof of concept. It can already be useful (it's
definitely useful for me) but it is still very primitive and it may have sharp
edges and/or eat your pets ;-)

I'm playing with the idea of converting the host's side of things to a daemon
that's always running and available to the guest agents to answer questions
about their host environment, however at the moment all communication is
initiated from the host towards the guests and I'm not yet sure how to
elegantly implement the architecture I'm envisioning.

Installation
------------

The ``negotiator`` packages and their dependencies are compatible with Python
2.6 and newer and are all pure Python. This means you don't need a compiler
toolchain to install the ``negotiator`` packages. This is a design decision and
so won't be changed.

On KVM/QEMU hosts
~~~~~~~~~~~~~~~~~

Here's how to install the `negotiator-host` package on your host(s)::

  sudo pip install negotiator-host

If you prefer you can install the Python package in a virtual environment::

  sudo apt-get install --yes python-virtualenv
  virtualenv /tmp/negotiator-host
  source /tmp/negotiator-host/bin/activate
  pip install negotiator-host

After installation the ``negotiator-host`` program is available. The usage
message will help you get started, try the ``--help`` option.

On KVM/QEMU guests
~~~~~~~~~~~~~~~~~~

Install the `negotiator-guest` package on your guest(s)::

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

1. First you have to add a virtual device to your QEMU guest. You can do so by
   editing the guest's XML definition file. On Ubuntu Linux KVM hosts these
   files are found in the directory ``/etc/libvirt/qemu``. Open the file in
   your favorite text editor (Vim? :-) and add the the following XML snippet
   inside the ``<devices>`` section::

     <channel type='unix'>
        <source mode='bind' />
        <target type='virtio' name='negotiator-channel.0' />
     </channel>

   .. note:: You don't have to supply a channel source path attribute, it
             should be filled in automatically by KVM/QEMU/libvirt when it
             notices that you've added the device (in step 2).

2. After adding the configuration snippet you have to activate it::

     virsh define /etc/libvirt/qemu/NAME-OF-GUEST.xml

3. Now you need to shut down the guest and then start it again::

     virsh shutdown --mode acpi NAME-OF-GUEST
     virsh start NAME-OF-GUEST

   .. note:: Just rebooting the guest will not add the new virtual device, you
             have to actually stop it and then start it again!

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

- Inside the guest a special character device is created that allows reading
  and writing. By default this character device is ``/dev/vport0p1``.

- On the host a UNIX socket is created that is connected to the character
  device inside the guest. On Ubuntu Linux KVM/QEMU hosts, these socket files
  are created in the directory ``/var/lib/libvirt/qemu/channel/target``.

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
.. _GitHub: https://github.com/xolox/python-negotiator
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _negotiator-common: https://pypi.python.org/pypi/negotiator-common
.. _negotiator-guest: https://pypi.python.org/pypi/negotiator-guest
.. _negotiator-host: https://pypi.python.org/pypi/negotiator-host
.. _official guest agent: http://wiki.libvirt.org/page/Qemu_guest_agent
.. _peter@peterodding.com: peter@peterodding.com
.. _PyPI: https://pypi.python.org/pypi/negotiator-host
.. _the same mechanism: http://www.linux-kvm.org/page/VMchannel_Requirements
