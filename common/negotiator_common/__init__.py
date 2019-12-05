# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 11, 2019
# URL: https://negotiator.readthedocs.org

"""
Common shared functionality between the `negotiator` host and guest.

This Python module contains the functionality that is shared between the
negotiator-host_ and negotiator-guest_ packages. By moving all of the shared
functionality to a separate Python package and using Python package
dependencies to pull in the negotiator-common_ package we stimulate code reuse
while avoiding code duplication.

.. _negotiator-common: https://pypi.python.org/pypi/negotiator-common
.. _negotiator-guest: https://pypi.python.org/pypi/negotiator-guest
.. _negotiator-host: https://pypi.python.org/pypi/negotiator-host
"""

# Standard library modules.
import json
import logging
import os

# External dependencies.
from executor import execute
from humanfriendly import Timer, compact

# Modules included in our project.
from negotiator_common.utils import format_call
from negotiator_common.config import BUILTIN_COMMANDS_DIRECTORY, USER_COMMANDS_DIRECTORY

# Semi-standard module versioning.
__version__ = '0.12'

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class NegotiatorInterface(object):

    """
    Common logic shared between the host/guest components.

    This class defines the protocol that's used to communicate between the
    Python programs running on the hosts and guests.
    """

    def __init__(self, handle, label):
        """
        Initialize a negotiator host or guest agent.

        :param handle: A file like object connected to the other side.
        :param label: A string describing the file like object (used in logging).

        This constructor is intended to be called by sub classes to provide the
        base class with the context it needs to set up bidirectional
        communication between the host and guest agents.
        """
        self.conn_handle = handle
        self.conn_label = label
        # Somewhere in the Python installation process the executable bits of
        # the built-in scripts get lost. This is a pragmatic hack to compensate
        # for that.
        for entry in os.listdir(BUILTIN_COMMANDS_DIRECTORY):
            pathname = os.path.join(BUILTIN_COMMANDS_DIRECTORY, entry)
            if os.path.isfile(pathname) and not os.access(pathname, os.X_OK):
                logger.debug("Making %s executable ..", pathname)
                os.chmod(pathname, 0o755)

    def raw_read(self, num_bytes):
        """
        Read the given number of bytes from the remote side.

        :param num_bytes: The number of bytes to read (an integer).
        :returns: The data read from the remote side (a string).
        """
        logger.debug("Preparing to read %i bytes from %s ..", num_bytes, self.conn_label)
        data = self.conn_handle.read(num_bytes)
        logger.debug("Read %i bytes from %s: %r", len(data), self.conn_label, data)
        return data

    def raw_readline(self):
        """
        Read a newline terminated string from the remote side.

        :returns: The data read from the remote side (a string).
        """
        logger.debug("Preparing to read line from %s ..", self.conn_label)
        data = self.conn_handle.readline()
        logger.debug("Read %i bytes from %s: %r", len(data), self.conn_label, data)
        return data

    def raw_write(self, data):
        """
        Write a string of data to the remote side.

        :param data: The data to write tot the remote side (a string).
        """
        logger.debug("Preparing to write %i bytes to %s ..", len(data), self.conn_label)
        self.conn_handle.write(data)
        self.conn_handle.flush()
        logger.debug("Finished writing %i bytes to %s.", len(data), self.conn_label)

    def read(self):
        """
        Wait for a JSON encoded message from the remote side.

        The basic communication protocol is really simple:

        1. First an ASCII encoded integer number is received, terminated by a
           newline.
        2. Second the number of bytes given by step 1 is read and interpreted
           as a JSON encoded value. This step is not terminated by a newline.

        That's it :-).

        :returns: The JSON value decoded to a Python value.
        :raises: :exc:`ProtocolError` when the remote side violates the
                 defined protocol.
        """
        logger.debug("Waiting for message from other side ..")
        # Wait for a line containing an integer byte count.
        line = self.raw_readline().strip()
        if not line.isdigit():
            # Complain loudly about protocol errors :-).
            raise ProtocolError(compact("""
                Received invalid input from remote side! I was expecting a
                byte count, but what I got instead was the line {input}!
            """, input=repr(line)))
        else:
            # First we get a line containing a byte count, then we read
            # that number of bytes from the remote side and decode it as a
            # JSON encoded message.
            num_bytes = int(line, 10)
            logger.debug("Reading message of %i bytes ..", num_bytes)
            encoded_value = self.raw_read(num_bytes)
            try:
                decoded_value = json.loads(encoded_value)
                logger.debug("Parsed message: %s", decoded_value)
                return decoded_value
            except Exception as e:
                logger.exception("Failed to parse JSON formatted message!")
                raise ProtocolError(compact("""
                    Failed to decode message from remote side as JSON!
                    Tried to decode message {message}. Original error:
                    {error}.
                """, message=repr(encoded_value), error=str(e)))

    def write(self, value):
        """
        Send a Python value to the other side.

        :param value: Any Python value that can be encoded as JSON.
        """
        encoded_message = json.dumps(value)
        num_bytes = len(encoded_message)
        logger.debug("Sending message of %i bytes: %s", num_bytes, encoded_message)
        self.raw_write("%i\n%s" % (num_bytes, encoded_message))

    def call_remote_method(self, method, *args, **kw):
        """
        Call a method on the remote object.

        :param method: The name of the method to call (a string).
        :param args: The positional arguments for the method.
        :param kw: The keyword arguments for the method.
        :returns: The return value of the remote method.
        """
        timer = Timer()
        logger.debug("Calling remote method %s ..", format_call(method, *args, **kw))
        self.write(dict(method=method, args=args, kw=kw))
        response = self.read()
        if response['success']:
            logger.debug("Remote method call succeeded in %s and returned %r!", timer, response['result'])
            return response['result']
        else:
            logger.warning("Remote method call failed after %s: %s", timer, response['error'])
            raise RemoteMethodFailed(response['error'])

    def enter_main_loop(self):
        """
        Wait for requests from the other side.

        The communication protocol for remote procedure calls is as follows:

        - Every request is a dictionary containing at least a ``command`` key
          with a string value (the name of the method to invoke).

        - The value of the optional ``arguments`` key gives a list of
          positional arguments to pass to the method.

        - The value of the optional ``keyword-arguments`` key gives a
          dictionary of keyword arguments to pass to the method.

        Responses are structured as follows:

        - Every response is a dictionary containing at least a ``success`` key
          with a boolean value.

        - If ``success=True`` the key ``result`` gives the return value of the
          method.

        - If ``success=False`` the key ``error`` gives a string explaining what
          went wrong.

        :raises: :exc:`ProtocolError` when the remote side violates the
                 defined protocol.
        """
        while True:
            request = self.read()
            method_name = request.get('method')
            method = getattr(self, method_name, None)
            args = request.get('args', [])
            kw = request.get('kw', {})
            if method and not method_name.startswith('_'):
                try:
                    logger.info("Remote is calling local method %s ..", format_call(method_name, *args, **kw))
                    result = method(*args, **kw)
                    logger.info("Local method call was successful and returned result %r.", result)
                    self.write(dict(success=True, result=result))
                except Exception as e:
                    logger.exception("Swallowing unexpected exception during local method call so we don't crash!")
                    self.write(dict(success=False, error=str(e)))
            else:
                logger.warning("Remote tried to call unsupported method %s!", method_name)
                self.write(dict(success=False, error="Method %s not supported" % method_name))

    def list_commands(self):
        """
        Find the names of the user defined commands.

        :returns: A list of executable names (strings).
        """
        commands = set()
        for directory in (BUILTIN_COMMANDS_DIRECTORY, USER_COMMANDS_DIRECTORY):
            if os.path.isdir(directory):
                for entry in os.listdir(directory):
                    pathname = os.path.join(directory, entry)
                    if os.path.isfile(pathname) and os.access(pathname, os.X_OK):
                        commands.add(entry)
        return list(commands)

    def prepare_environment(self):
        """
        Prepare environment variables for command execution.

        This method can be overridden by sub classes to prepare environment
        variables for external command execution.
        """

    def execute(self, *command, **options):
        """
        Execute a user defined or built-in command.

        :param command: The command name and any arguments (one or more strings).
        :param input: The input to feed to the command on its standard input
                      stream (a string or ``None``).
        :returns: The output of the command (a string) or ``None`` if the
                  command exited with a nonzero exit code.
        """
        self.prepare_environment()
        command_name = os.path.basename(command[0])
        user_command = os.path.join(USER_COMMANDS_DIRECTORY, command_name)
        builtin_command = os.path.join(BUILTIN_COMMANDS_DIRECTORY, command_name)
        command = list(command)
        command[0] = user_command if os.path.isfile(user_command) else builtin_command
        return execute(*command, input=options.get('input', None), capture=True, logger=logger)


class ProtocolError(Exception):

    """Exception that is raised when the communication protocol is violated."""


class RemoteMethodFailed(Exception):

    """Exception that is raised when a remote method call failed."""
