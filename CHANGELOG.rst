Changelog
=========

The purpose of this document is to list all of the notable changes to this
project. The format was inspired by `Keep a Changelog`_. This project adheres
to `semantic versioning`_.

.. contents::
   :local:

.. _Keep a Changelog: http://keepachangelog.com/
.. _semantic versioning: http://semver.org/

`Release 0.9`_ (2019-03-03)
---------------------------

Refactored channel discovery to use ``virsh list`` and ``virsh dumpxml``:

- The recent addition of Ubuntu 18.04 support proved once again that the
  old channel discovery strategy was error prone and hard to maintain.

- Since then it had come to my attention that on Ubuntu 18.04 guest names
  embedded in pathnames of UNIX sockets may be truncated in which case the
  domain id provides the only way to match a UNIX socket to its guest.

- Despite the previous point, I also wanted to maintain compatibility with
  libvirt releases that don't embed the domain id in the pathnames. Doing so
  based on the old channel discovery strategy would have become messy.

So I decided to take a big step back and opted for a new strategy that will
hopefully prove to be more robust and future proof. Thanks to `@tarmack`_ for
initially suggesting this approach.

.. _Release 0.9: https://github.com/xolox/python-negotiator/compare/0.8.6...0.9
.. _@tarmack: https://github.com/tarmack

`Release 0.8.6`_ (2019-02-25)
-----------------------------

Follow-up to making channel discovery compatible with Ubuntu 18.04:

- `Release 0.8.5`_ updated ``negotiator-host --daemon``.
- `Release 0.8.6`_ updates ``negotiator-host --list-commands`` and similar commands.

.. _Release 0.8.6: https://github.com/xolox/python-negotiator/compare/0.8.5...0.8.6

`Release 0.8.5`_ (2019-02-23)
-----------------------------

- Made channel discovery compatible with Ubuntu 18.04.
- Added this changelog, restructured the documentation.
- Embedded CLI usage messages in readme and documentation.
- Updated ``supervisord`` configuration examples to use
  ``stderr_logfile`` instead of ``redirect_stderr``.
- Other minor changes not touching the code base.

.. _Release 0.8.5: https://github.com/xolox/python-negotiator/compare/0.8.4...0.8.5

`Release 0.8.4`_ (2016-04-08)
-----------------------------

Follow-up to previous commit (Ubuntu 16.04 support).

.. _Release 0.8.4: https://github.com/xolox/python-negotiator/compare/0.8.3...0.8.4

`Release 0.8.3`_ (2016-04-08)
-----------------------------

Make channel discovery compatible with Ubuntu 16.04.

.. _Release 0.8.3: https://github.com/xolox/python-negotiator/compare/0.8.2...0.8.3

`Release 0.8.2`_ (2015-10-29)
-----------------------------

Make platform support more explicit in the documentation (Linux only, basically :-P).

.. _Release 0.8.2: https://github.com/xolox/python-negotiator/compare/0.8.1...0.8.2

`Release 0.8.1`_ (2014-12-30)
-----------------------------

Improve guest channel (re)spawning on hosts (improves robustness).

.. _Release 0.8.1: https://github.com/xolox/python-negotiator/compare/0.8...0.8.1

`Release 0.8`_ (2014-11-01)
---------------------------

Proper sub process cleanup, more robust blocking read emulation.

.. _Release 0.8: https://github.com/xolox/python-negotiator/compare/0.7...0.8

`Release 0.7`_ (2014-10-24)
---------------------------

Support for (custom) remote call timeouts with a default of 10s.

.. _Release 0.7: https://github.com/xolox/python-negotiator/compare/0.6.1...0.7

`Release 0.6.1`_ (2014-09-28)
-----------------------------

Bug fix for Python 2.6 compatibility (``count()`` does not take keyword arguments).

.. _Release 0.6.1: https://github.com/xolox/python-negotiator/compare/0.6...0.6.1

`Release 0.6`_ (2014-09-26)
---------------------------

- Implemented blocking reads inside guests (don't ask me how, please ...).
- Improved getting started instructions on adding virtual devices.
- Rebranded ``s/generic/scriptable/g`` and improved the readme a bit.

.. _Release 0.6: https://github.com/xolox/python-negotiator/compare/0.5.2...0.6

`Release 0.5.2`_ (2014-09-24)
-----------------------------

Add syntax highlighting to the code and configuration samples in the readme
and explicitly link to the online documentation available on Read the Docs.

.. _Release 0.5.2: https://github.com/xolox/python-negotiator/compare/0.5.1...0.5.2

`Release 0.5.1`_ (2014-09-24)
-----------------------------

- Minor improvements and fixes to the documentation.
- Properly documented the environment variables exposed to host commands.
- Added trove classifiers to the ``setup.py`` scripts.
- Bumped the version to release updated documentation to PyPI.

.. _Release 0.5.1: https://github.com/xolox/python-negotiator/compare/0.5...0.5.1

`Release 0.5`_ (2014-09-24)
---------------------------

- Support for proper bidirectional user defined command execution on both sides.
- Improved the ``negotiator-guest`` usage message (by mentioning character device detection).

.. _Release 0.5: https://github.com/xolox/python-negotiator/compare/0.2.1...0.5

`Release 0.2.1`_ (2014-09-22)
-----------------------------

Fixed a typo in the readme, fixed a bug in the makefile and bumped the version
so I could push a new release to PyPI because the readme was missing there (due
to the makefile bug).

.. _Release 0.2.1: https://github.com/xolox/python-negotiator/compare/0.2...0.2.1

`Release 0.2`_ (2014-09-22)
---------------------------

- Added automatic character device selection.
- Created online documentation on Read the Docs.

.. _Release 0.2: https://github.com/xolox/python-negotiator/compare/0.1...0.2

`Release 0.1`_ (2014-09-22)
---------------------------

The initial commit and release.

.. _Release 0.1: https://github.com/xolox/python-negotiator/tree/0.1
