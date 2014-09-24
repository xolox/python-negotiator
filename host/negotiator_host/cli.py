# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 24, 2014
# URL: https://negotiator.readthedocs.org

"""
Usage: negotiator-host [OPTIONS] GUEST_NAME

Communicate from a KVM/QEMU host system with running guest systems using a
guest agent daemon running inside the guests.

Supported options:

  -g, --list-guests

    List the names of the guests that have the appropriate channel.

  -c, --list-commands

    List the commands that the guest exposes to its host.

  -e, --execute=COMMAND

    Execute the given command inside GUEST_NAME. The standard output stream of
    the command inside the guest is intercepted and copied to the standard
    output stream on the host. If the command exits with a nonzero status code
    the negotiator-host program will also exit with a nonzero status code.

  -d, --daemon

    Start the host daemon that answers real time requests from guests.

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
from negotiator_common.config import CHANNELS_DIRECTORY, HOST_TO_GUEST_CHANNEL_NAME
from negotiator_host import HostDaemon, GuestChannel, find_available_channels

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``negotiator-host`` program."""
    # Initialize logging to the terminal.
    coloredlogs.install(level=logging.INFO)
    # Parse the command line arguments.
    actions = []
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'gce:dvqh', [
            'list-guests', 'list-commands', 'execute=', 'daemon', 'verbose',
            'quiet', 'help'
        ])
        for option, value in options:
            if option in ('-g', '--list-guests'):
                actions.append(print_guest_names)
            elif option in ('-c', '--list-commands'):
                assert len(arguments) == 1, \
                    "Please provide the name of a guest as the 1st and only positional argument!"
                actions.append(functools.partial(print_commands, arguments[0]))
            elif option in ('-e', '--execute'):
                assert len(arguments) == 1, \
                    "Please provide the name of a guest as the 1st and only positional argument!"
                actions.append(functools.partial(execute_command, arguments[0], value))
            elif option in ('-d', '--daemon'):
                actions.append(HostDaemon)
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


def print_guest_names():
    """Print the names of the guests that Negotiator can connect with."""
    channels = find_available_channels(CHANNELS_DIRECTORY, HOST_TO_GUEST_CHANNEL_NAME)
    print('\n'.join(sorted(channels.keys())))


def print_commands(guest_name):
    """Print the commands supported by the guest."""
    channel = GuestChannel(guest_name=guest_name)
    print('\n'.join(sorted(channel.call_remote_method('list_commands'))))


def print_result(guest_name, method_name):
    """Print the result of a remote method invoked on the named guest's channel."""
    channel = GuestChannel(guest_name=guest_name)
    method = getattr(channel, method_name)
    result = method()
    if isinstance(result, list):
        result = '\n'.join(result)
    print(result.rstrip())


def execute_command(guest_name, command_line):
    """Execute a command inside the named guest."""
    channel = GuestChannel(guest_name=guest_name)
    try:
        output = channel.call_remote_method('execute', *shlex.split(command_line), capture=True)
        print(output.rstrip())
    except Exception:
        logger.exception("Caught unexpected exception during remote command execution!")
        sys.exit(1)
