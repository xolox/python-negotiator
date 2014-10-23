# Scriptable KVM/QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 24, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_common.utils`` - Miscellaneous functions
=====================================================
"""

import signal


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


def format_call(function, *args, **kw):
    """
    Format a Python function call into a human readable string.

    :param function: The name of the function that's called (a string).
    :param args: The positional arguments to the function (if any).
    :param kw: The keyword arguments to the function (if any).
    """
    formatted_arguments = []
    for argument in args:
        formatted_arguments.append(repr(argument))
    for keyword, value in kw.items():
        formatted_arguments.append("%s=%r" % (keyword, value))
    return "%s(%s)" % (function, ', '.join(formatted_arguments))


class TimeOut(object):

    """Context manager that enforces timeouts using UNIX alarm signals."""

    def __init__(self, num_seconds):
        """
        Initialize the context manager.

        :param num_seconds: The number of seconds after which to interrupt the
                            running operation (an integer).
        """
        self.num_seconds = num_seconds

    def __enter__(self):
        """Schedule the timeout."""
        self.previous_handler = signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(self.num_seconds)

    def __exit__(self, exc_type, exc_value, traceback):
        """Clear the timeout and restore the previous signal handler."""
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.previous_handler)

    def signal_handler(self, signum, frame):
        """Raise :py:class:`TimeOutError` when the timeout elapses."""
        raise TimeOutError()


class TimeOutError(Exception):

    """Exception raised by the :py:class:`TimeOut` context manager."""
