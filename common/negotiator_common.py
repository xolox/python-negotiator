# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_common`` - Common shared functionality
===================================================

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
import time

# Semi-standard module versioning.
__version__ = '0.1'

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

    def raw_read(self, num_bytes):
        """
        Read the given number of bytes from the remote side.

        :param num_bytes: The number of bytes to read (an integer).
        :returns: The data read from the remote side (a string). If no data is
                  available this may return a value that evaluates to ``False``
                  instead of blocking.
        """
        logger.debug("Preparing to read %i bytes from %s ..", num_bytes, self.conn_label)
        data = self.conn_handle.read(num_bytes)
        logger.debug("Read %i bytes from %s: %r", len(data), self.conn_label, data)
        return data

    def raw_readline(self):
        """
        Read a newline terminated string from the remote side.

        :returns: The data read from the remote side (a string). If no data is
                  available this may return a value that evaluates to ``False``
                  instead of blocking.
        """
        logger.debug("Preparing to read line from %s ..", self.conn_label)
        data = self.conn_handle.readline()
        logger.debug("Read line from %s: %r", self.conn_label, data)
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
        :raises: :py:exc:`ProtocolError` when the remote side violates the
                 defined protocol.
        """
        logger.debug("Waiting for message from other side ..")
        while True:
            # Wait for a line containing an integer byte count.
            line = self.raw_readline().strip()
            # If there is no remote side the read call might not block and
            # instead return a value that evaluates to False.
            if not line:
                # Because we can't rely on the read call to block we have to
                # avoid taxing the CPU in a busy loop that performs thousands
                # of read calls per second :-).
                time.sleep(0.25)
            elif not line.isdigit():
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
        self.raw_write("%i\n" % num_bytes)
        self.raw_write(encoded_message)

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

        :raises: :py:exc:`ProtocolError` when the remote side violates the
                 defined protocol.
        """
        while True:
            request = self.read()
            command_name = request.get('command')
            arguments = request.get('arguments', [])
            keyword_arguments = request.get('keyword_arguments', {})
            method = getattr(self, command_name, None)
            if method and not command_name.startswith('_'):
                try:
                    self.write(dict(success=True, result=method(*arguments, **keyword_arguments)))
                except Exception as e:
                    logger.exception("Swallowing an unexpected exception so we don't crash!")
                    self.send(dict(success=False, error=str(e)))
            else:
                self.send(dict(success=False, error="Command %s not supported" % command_name))

    def __getattr__(self, name):
        """
        Automatically proxy method invocations to the other side.

        :param name: The name of the remote method (a string).
        :returns: A function that proxies to the other side.
        """
        def fake_method(*args, **kw):
            self.write(dict(command=name, arguments=args, keyword_arguments=kw))
            response = self.read()
            if response['success']:
                return response['result']
            else:
                raise Exception(response['error'])
        return fake_method


class ProtocolError(Exception):

    """Exception that is raised when the communication protocol is violated."""


def compact(text, **kw):
    """
    Compact whitespace and format any arguments into the given string.

    Trims leading and trailing whitespace, replaces runs of whitespace with a
    single space and formats any keyword arguments into the resulting string
    using :py:func:`str.format()`.

    :param text: The text to compact (a string).
    :param kw: Any keyword arguments to apply using :py:func:`str.format()`.
    :returns: The compacted, formatted string.
    """
    return ' '.join(text.split()).format(**kw)
