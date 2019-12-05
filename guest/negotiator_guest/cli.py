# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: December 5, 2019
# URL: https://negotiator.readthedocs.org

"""
Usage: negotiator-guest [OPTIONS]

Communicate from a KVM/QEMU guest system to its host or start the
guest daemon to allow the host to execute commands on its guests.

Supported options:

  -l, --list-commands

    List the commands that the host exposes to its guests.

  -e, --execute=COMMAND

    Execute the given command on the KVM/QEMU host. The standard output stream
    of the command on the host is intercepted and copied to the standard output
    stream on the guest. If the command exits with a nonzero status code the
    negotiator-guest program will also exit with a nonzero status code.

  -d, --daemon

    Start the guest daemon. When using this command line option the
    `negotiator-guest' program never returns (unless an unexpected error
    condition occurs).

  -t, --timeout=SECONDS

    Set the number of seconds before a remote call without a response times
    out. A value of zero disables the timeout (in this case the command can
    hang indefinitely). The default is 10 seconds.

  -c, --character-device=PATH

    By default the appropriate character device is automatically selected based
    on /sys/class/virtio-ports/*/name. If the automatic selection doesn't work,
    you can set the absolute pathname of the character device that's used to
    communicate with the negotiator-host daemon running on the KVM/QEMU host.

  -v, --verbose

    Increase logging verbosity (can be repeated).

  -q, --quiet

    Decrease logging verbosity (can be repeated).

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import getopt
import logging
import shlex
import sys

# External dependencies.
import coloredlogs
from humanfriendly import Timer
from humanfriendly.terminal import usage, warning

# Modules included in our project.
from negotiator_common.config import GUEST_TO_HOST_CHANNEL_NAME, HOST_TO_GUEST_CHANNEL_NAME, DEFAULT_TIMEOUT
from negotiator_common.utils import TimeOut
from negotiator_guest import GuestAgent, find_character_device

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``negotiator-guest`` program."""
    # Initialize logging to the terminal and system log.
    coloredlogs.install(syslog=True)
    # Parse the command line arguments.
    list_commands = False
    execute_command = None
    start_daemon = False
    timeout = DEFAULT_TIMEOUT
    character_device = None
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'le:dt:c:vqh', [
            'list-commands', 'execute=', 'daemon', 'timeout=',
            'character-device=', 'verbose', 'quiet', 'help'
        ])
        for option, value in options:
            if option in ('-l', '--list-commands'):
                list_commands = True
            elif option in ('-e', '--execute'):
                execute_command = value
            elif option in ('-d', '--daemon'):
                start_daemon = True
            elif option in ('-t', '--timeout'):
                timeout = int(value)
            elif option in ('-c', '--character-device'):
                character_device = value
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage(__doc__)
                sys.exit(0)
        if not (list_commands or execute_command or start_daemon):
            usage(__doc__)
            sys.exit(0)
    except Exception:
        warning("Error: Failed to parse command line arguments!")
        sys.exit(1)
    # Start the guest daemon.
    try:
        if not character_device:
            channel_name = HOST_TO_GUEST_CHANNEL_NAME if start_daemon else GUEST_TO_HOST_CHANNEL_NAME
            character_device = find_character_device(channel_name)
        if start_daemon:
            agent = GuestAgent(character_device)
            agent.enter_main_loop()
        elif list_commands:
            with TimeOut(timeout):
                agent = GuestAgent(character_device)
                print('\n'.join(agent.call_remote_method('list_commands')))
        elif execute_command:
            with TimeOut(timeout):
                timer = Timer()
                agent = GuestAgent(character_device)
                output = agent.call_remote_method('execute', *shlex.split(execute_command), capture=True)
                logger.debug("Took %s to execute remote command.", timer)
                print(output.rstrip())
    except Exception:
        logger.exception("Caught a fatal exception! Terminating ..")
        sys.exit(1)
