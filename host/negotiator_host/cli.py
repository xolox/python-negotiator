# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://negotiator.readthedocs.org

"""
Usage: negotiator-host [OPTIONS] GUEST_NAME

Communicate from a KVM/QEMU host system with running guest systems using a
guest agent daemon running inside the guests.

Supported options:

  -d, --find-distributor-id

    Find the distributor ID (a string like 'Ubuntu') of GUEST_NAME using the
    lsb_release command and report the result on standard output.

  -r, --find-distribution-release

    Find the distribution release (a string like '12.04') of GUEST_NAME using
    the lsb_release command and report the result on standard output.

  -c, --find-distribution-codename

    Find the distribution codename (a string like 'precise') of GUEST_NAME
    using the lsb_release command and report the result on standard output.

  -i, --find-ip-addresses

    Find the IP addresses of GUEST_NAME. The IP addresses are reported in CIDR
    notation on standard output, each on a separate line.

  -e, --execute=COMMAND

    Execute the given command inside GUEST_NAME. The standard output stream of
    the command inside the guest is intercepted and copied to the standard
    output stream on the host. If the command exits with a nonzero status code
    the negotiator-host program will also exit with a nonzero status code.

  -v, --verbose

    Make more noise (enables debugging).

  -q, --quiet

    Only show warnings and errors.

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import functools
import getopt
import logging
import shlex
import sys

# External dependencies.
import coloredlogs

# Modules included in our package.
from negotiator_host import GuestChannel

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``negotiator-host`` program."""
    # Initialize logging to the terminal.
    coloredlogs.install(level=logging.INFO)
    # Parse the command line arguments.
    actions = []
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'drcie:vqh', [
            'find-distributor-id', 'find-distribution-release',
            'find-distribution-codename', 'find-ip-addresses', 'execute=',
            'verbose', 'quiet', 'help'
        ])
        for option, value in options:
            if option in ('-d', '--find-distributor-id'):
                assert len(arguments) >= 1, "Please provide the name of a guest as the 1st positional argument!"
                actions.append(functools.partial(print_result, arguments[0], 'find_distributor_id'))
            elif option in ('-r', '--find-distribution-release'):
                assert len(arguments) >= 1, "Please provide the name of a guest as the 1st positional argument!"
                actions.append(functools.partial(print_result, arguments[0], 'find_distribution_release'))
            elif option in ('-c', '--find-distribution-codename'):
                assert len(arguments) >= 1, "Please provide the name of a guest as the 1st positional argument!"
                actions.append(functools.partial(print_result, arguments[0], 'find_distribution_codename'))
            elif option in ('-i', '--find-ip-addresses'):
                assert len(arguments) >= 1, "Please provide the name of a guest as the 1st positional argument!"
                actions.append(functools.partial(print_result, arguments[0], 'find_ip_addresses'))
            elif option in ('-e', '--execute'):
                assert len(arguments) >= 1, "Please provide the name of a guest as the 1st positional argument!"
                actions.append(functools.partial(execute_command, arguments[0], value))
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage()
                sys.exit(0)
        if not actions:
            usage()
            sys.exit(0)
    except Exception:
        logger.exception("Failed to parse command line arguments!")
        sys.exit(1)
    # Execute the requested action(s).
    try:
        for action in actions:
            action()
    except Exception:
        logger.exception("Caught a fatal exception! Terminating ..")
        sys.exit(1)


def usage():
    """Print a user friendly usage message to the terminal."""
    print(__doc__.strip())


def print_result(guest_name, method_name):
    """Print the result of a remote method invoked on the named guest's channel."""
    channel = GuestChannel(guest_name=guest_name)
    method = getattr(channel, method_name)
    result = method()
    if isinstance(result, list):
        print('\n'.join(channel.find_ip_addresses()))
    else:
        print(result)


def execute_command(guest_name, command_line):
    """Execute a command inside the named guest."""
    channel = GuestChannel(guest_name=guest_name)
    try:
        print(channel.execute(*shlex.split(command_line), capture=True))
    except Exception:
        logger.exception("Caught unexpected exception during remote command execution!")
        sys.exit(1)
