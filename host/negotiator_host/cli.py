# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: March 3, 2019
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

  -t, --timeout=SECONDS

    Set the number of seconds before a remote call without a response times
    out. A value of zero disables the timeout (in this case the command can
    hang indefinitely). The default is 10 seconds.

  -d, --daemon

    Start the host daemon that answers real time requests from guests.

  -v, --verbose

    Increase logging verbosity (can be repeated).

  -q, --quiet

    Decrease logging verbosity (can be repeated).

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
from humanfriendly import Timer
from humanfriendly.terminal import usage, warning

# Modules included in our project.
from negotiator_common.config import DEFAULT_TIMEOUT
from negotiator_common.utils import TimeOut
from negotiator_host import GuestDiscoveryError, HostDaemon, GuestChannel, find_supported_guests

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``negotiator-host`` program."""
    # Initialize logging to the terminal and system log.
    coloredlogs.install(syslog=True)
    # Parse the command line arguments.
    actions = []
    context = Context()
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'gce:t:dvqh', [
            'list-guests', 'list-commands', 'execute=', 'timeout=', 'daemon',
            'verbose', 'quiet', 'help'
        ])
        for option, value in options:
            if option in ('-g', '--list-guests'):
                actions.append(context.print_guest_names)
            elif option in ('-c', '--list-commands'):
                assert len(arguments) == 1, \
                    "Please provide the name of a guest as the 1st and only positional argument!"
                actions.append(functools.partial(context.print_commands, arguments[0]))
            elif option in ('-e', '--execute'):
                assert len(arguments) == 1, \
                    "Please provide the name of a guest as the 1st and only positional argument!"
                actions.append(functools.partial(context.execute_command, arguments[0], value))
            elif option in ('-t', '--timeout'):
                context.timeout = int(value)
            elif option in ('-d', '--daemon'):
                actions.append(HostDaemon)
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage(__doc__)
                sys.exit(0)
        if not actions:
            usage(__doc__)
            sys.exit(0)
    except Exception:
        warning("Failed to parse command line arguments!")
        sys.exit(1)
    # Execute the requested action(s).
    try:
        for action in actions:
            action()
    except GuestDiscoveryError as e:
        # Don't spam the logs with tracebacks when the libvirt daemon is down.
        logger.error("%s", e)
        sys.exit(1)
    except Exception:
        # Do log a traceback for `unexpected' exceptions.
        logger.exception("Caught a fatal exception! Terminating ..")
        sys.exit(1)


class Context(object):

    """Enables :func:`main()` to inject a custom timeout into partially applied actions."""

    def __init__(self):
        """Initialize a context for executing commands on the host."""
        self.timeout = DEFAULT_TIMEOUT

    def print_guest_names(self):
        """Print the names of the guests that Negotiator can connect with."""
        guests = find_supported_guests()
        if guests:
            print('\n'.join(sorted(guests)))

    def print_commands(self, guest_name):
        """Print the commands supported by the guest."""
        with TimeOut(self.timeout):
            channel = GuestChannel(guest_name=guest_name)
            print('\n'.join(sorted(channel.call_remote_method('list_commands'))))

    def execute_command(self, guest_name, command_line):
        """Execute a command inside the named guest."""
        with TimeOut(self.timeout):
            timer = Timer()
            channel = GuestChannel(guest_name=guest_name)
            output = channel.call_remote_method('execute', *shlex.split(command_line), capture=True)
            logger.debug("Took %s to execute remote command.", timer)
            print(output.rstrip())
