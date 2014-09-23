# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 23, 2014
# URL: https://negotiator.readthedocs.org

"""
Usage: negotiator-guest [OPTIONS]

Start the negotiator-guest daemon.

Supported options:

  -d, --daemon

    Start the guest daemon. When using this command line option the
    `negotiator-guest' program never returns (unless an unexpected error
    condition occurs).

  -c, --character-device=PATH

    By default the appropriate character device is automatically selected based
    on /sys/class/virtio-ports/*/name. If the automatic selection doesn't work,
    you can set the absolute pathname of the character device that's used to
    communicate with the negotiator-host daemon running on the KVM/QEMU host.

  -v, --verbose

    Make more noise (enables debugging).

  -q, --quiet

    Only show warnings and errors.

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import getopt
import logging
import sys

# External dependencies.
import coloredlogs

# Modules included in our project.
from negotiator_guest import GuestAgent

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``negotiator-guest`` program."""
    # Initialize logging to the terminal.
    coloredlogs.install(level=logging.INFO)
    # Parse the command line arguments.
    start_daemon = False
    character_device = None
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'dc:vqh', [
            'daemon', 'character-device=', 'verbose', 'quiet', 'help'
        ])
        for option, value in options:
            if option in ('-d', '--daemon'):
                start_daemon = True
            elif option in ('-c', '--character-device'):
                character_device = value
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage()
                sys.exit(0)
        if not start_daemon:
            usage()
            sys.exit(0)
    except Exception:
        logger.exception("Failed to parse command line arguments!")
        sys.exit(1)
    # Start the guest daemon.
    try:
        guest_daemon = GuestAgent(character_device=character_device)
        guest_daemon.enter_main_loop()
    except Exception:
        logger.exception("Caught a fatal exception! Terminating ..")
        sys.exit(1)


def usage():
    """Print a user friendly usage message to the terminal."""
    print(__doc__.strip())
