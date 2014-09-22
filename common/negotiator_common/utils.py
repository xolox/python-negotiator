# Generic QEMU guest agent in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://negotiator.readthedocs.org

"""
``negotiator_common.utils`` - Miscellaneous functions
=====================================================
"""


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
