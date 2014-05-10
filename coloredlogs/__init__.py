"""
Colored terminal output for Python's logging module.

Author: Peter Odding <peter@peterodding.com>
Last Change: May 10, 2014
URL: https://github.com/xolox/python-coloredlogs
"""

# Semi-standard module versioning.
__version__ = '0.5'

# Standard library modules.
import copy
import logging
import os
import re
import socket
import sys
import time

# Portable color codes from http://en.wikipedia.org/wiki/ANSI_escape_code#Colors.
ansi_color_codes = dict(black=0, red=1, green=2, yellow=3, blue=4, magenta=5, cyan=6, white=7)

# The logging handler attached to the root logger (initialized by install()).
root_handler = None

def ansi_text(message, color='black', bold=False):
    """
    Wrap text in ANSI escape sequences for the given color and/or style.

    :param message: The text message (a string).
    :param color: The name of a color (one of the strings black, red, green,
                  yellow, blue, magenta, cyan or white).
    :param bold: ``True`` if the text should be bold, ``False`` otherwise.
    :returns: The text message wrapped in ANSI escape sequences.
    """
    return '\x1b[%i;3%im%s\x1b[0m' % (bold and 1 or 0, ansi_color_codes[color], message)

def install(level=logging.INFO, **kw):
    """
    Install a :py:class:`ColoredStreamHandler` for the root logger. Calling
    this function multiple times will never install more than one handler.

    :param level: The logging level to filter on (defaults to ``INFO``).
    :param kw: Optional keyword arguments for :py:class:`ColoredStreamHandler`.
    """
    global root_handler
    if not root_handler:
        # Create the root handler.
        root_handler = ColoredStreamHandler(level=level, **kw)
        # Install the root handler.
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.NOTSET)
        root_logger.addHandler(root_handler)

# TODO Move these functions into ColoredStreamHandler?

def increase_verbosity():
    """
    Increase the verbosity of the root handler by one defined level.
    Understands custom logging levels like defined by my ``verboselogs``
    module.
    """
    defined_levels = find_defined_levels()
    current_level = get_level()
    closest_level = min(defined_levels, key=lambda l: abs(l - current_level))
    set_level(defined_levels[max(0, defined_levels.index(closest_level) - 1)])

def is_verbose():
    """
    Check whether the log level of the root handler is set to a verbose level.

    :returns: ``True`` if the root handler is verbose, ``False`` if not.
    """
    return get_level() < logging.INFO

def get_level():
    """
    Get the logging level of the root handler.

    :returns: The logging level of the root handler (an integer).
    """
    install()
    return root_handler.level

def set_level(level):
    """
    Set the logging level of the root handler.

    :param level: The logging level to filter on (an integer).
    """
    install()
    root_handler.level = level

def find_defined_levels():
    """
    Find the defined logging levels.
    """
    defined_levels = set()
    for name in dir(logging):
        if name.isupper():
            value = getattr(logging, name)
            if isinstance(value, int):
                defined_levels.add(value)
    return sorted(defined_levels)

class ColoredStreamHandler(logging.StreamHandler):

    """
    The :py:class:`ColoredStreamHandler` class enables colored terminal output
    for a logger created with Python's :py:mod:`logging` module. The log
    handler formats log messages including timestamps, logger names and
    severity levels. It uses `ANSI escape sequences`_ to highlight timestamps
    and debug messages in green and error and warning messages in red. The
    handler does not use ANSI escape sequences when output redirection applies,
    for example when the standard error stream is being redirected to a file.
    Here's an example of its use::

        # Create a logger object.
        import logging
        logger = logging.getLogger('your-module')

        # Initialize coloredlogs.
        import coloredlogs
        coloredlogs.install()
        coloredlogs.set_level(logging.DEBUG)

        # Some examples.
        logger.debug("this is a debugging message")
        logger.info("this is an informational message")
        logger.warn("this is a warning message")
        logger.error("this is an error message")
        logger.fatal("this is a fatal message")
        logger.critical("this is a critical message")

    .. _ANSI escape sequences: http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    """

    def __init__(self, stream=sys.stderr, level=logging.NOTSET, isatty=None,
                 show_name=True, show_severity=True, show_timestamps=True,
                 show_hostname=True, use_chroot=True):
        logging.StreamHandler.__init__(self, stream)
        self.level = level
        self.show_timestamps = show_timestamps
        self.show_hostname = show_hostname
        self.show_name = show_name
        self.show_severity = show_severity
        if isatty is not None:
            self.isatty = isatty
        else:
            # Protect against sys.stderr.isatty() not being defined (e.g. in
            # the Python Interface to Vim).
            try:
                self.isatty = stream.isatty()
            except Exception:
                self.isatty = False
        if show_hostname:
            chroot_file = '/etc/debian_chroot'
            if use_chroot and os.path.isfile(chroot_file):
                with open(chroot_file) as handle:
                    self.hostname = handle.read().strip()
            else:
                self.hostname = re.sub(r'\.local$', '', socket.gethostname())
        if show_name:
            self.pid = os.getpid()

    def emit(self, record):
        """
        Called by the :py:mod:`logging` module for each log record. Formats the
        log message and passes it onto :py:func:`logging.StreamHandler.emit()`.
        """
        # If the message doesn't need to be rendered we take a shortcut.
        if record.levelno < self.level:
            return
        # Make sure the message is a string.
        message = record.msg
        try:
            if not isinstance(message, basestring):
                message = unicode(message)
        except NameError:
            if not isinstance(message, str):
                message = str(message)
        # Colorize the log message text.
        severity = record.levelname
        if severity == 'CRITICAL':
            message = self.wrap_color('red', message, bold=True)
        elif severity == 'ERROR':
            message = self.wrap_color('red', message)
        elif severity == 'WARNING':
            message = self.wrap_color('yellow', message)
        elif severity == 'VERBOSE':
            # The "VERBOSE" logging level is not defined by Python's logging
            # module; I've extended the logging module to support this level.
            message = self.wrap_color('blue', message)
        elif severity == 'DEBUG':
            message = self.wrap_color('green', message)
        # Compose the formatted log message as:
        #   timestamp hostname name severity message
        # Everything except the message text is optional.
        parts = []
        if self.show_timestamps:
            parts.append(self.wrap_color('green', self.render_timestamp(record.created)))
        if self.show_hostname:
            parts.append(self.wrap_color('magenta', self.hostname))
        if self.show_name:
            parts.append(self.wrap_color('blue', self.render_name(record.name)))
        if self.show_severity:
            parts.append(self.wrap_color('black', severity, bold=True))
        parts.append(message)
        message = ' '.join(parts)
        # Copy the original record so we don't break other handlers.
        record = copy.copy(record)
        record.msg = message
        # Use the built-in stream handler to handle output.
        logging.StreamHandler.emit(self, record)

    def render_timestamp(self, created):
        """
        Format the time stamp of the log record. Receives the time when the
        LogRecord was created (as returned by :py:func:`time.time()`). By
        default this returns a string in the format ``YYYY-MM-DD HH:MM:SS``.
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))

    def render_name(self, name):
        """
        Format the name of the logger. Receives the name of the logger used to
        log the call. By default this returns a string in the format
        ``NAME[PID]`` (where PID is the process ID reported by
        :py:func:`os.getpid()`).
        """
        return '%s[%s]' % (name, self.pid)

    def wrap_color(self, colorname, message, bold=False):
        """
        Wrap text in ANSI escape sequences for the given color [and optionally
        to enable bold font].
        """
        if self.isatty:
            return ansi_text(message, color=colorname, bold=bold)
        else:
            return message

# vim: ts=4 sw=4 et
