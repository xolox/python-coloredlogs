#!/usr/bin/env python

"""
Colored terminal output for Python's logging module.

Author: Peter Odding <peter@peterodding.com>
Last Change: June 6, 2013
URL: https://pypi.python.org/pypi/coloredlogs

The ColoredStreamHandler class enables colored terminal output for a logger
created with Python's logging module. The log handler formats log messages
including timestamps, logger names and severity levels. It uses ANSI escape
sequences to highlight timestamps and debug messages in green and error and
warning messages in red. The handler does not use ANSI escape sequences when
output redirection applies, for example when the standard error stream is being
redirected to a file. Here's an example of its use:

    # Configure your logger.
    import logging, coloredlogs
    log = logging.getLogger('your-module')
    log.addHandler(coloredlogs.ColoredStreamHandler())

    # Some examples.
    log.setLevel(logging.DEBUG)
    log.debug("this is a debugging message")
    log.info("this is an informational message")
    log.warn("this is a warning message")
    log.error("this is an error message")
    log.fatal("this is a fatal message")
    log.critical("this is a critical message")
"""

import copy
import logging
import os
import re
import socket
import sys
import time

# Portable color codes from http://en.wikipedia.org/wiki/ANSI_escape_code#Colors.
ansi_color_codes = dict(black=0, red=1, green=2, yellow=3, blue=4, magenta=5, cyan=6, white=7)

def ansi_text(message, color='black', bold=False):
    """ Wrap text in escape sequences for the given color and/or style. """
    return '\x1b[%i;3%im%s\x1b[0m' % (bold and 1 or 0, ansi_color_codes[color], message)

class ColoredStreamHandler(logging.StreamHandler):

    def __init__(self, stream=sys.stderr, isatty=None, show_name=False, show_severity=True, show_timestamps=True, show_hostname=True):
        logging.StreamHandler.__init__(self, stream)
        self.show_timestamps = show_timestamps
        self.show_hostname = show_hostname
        self.show_name = show_name
        self.show_severity = show_severity
        self.isatty = isatty if isatty is not None else stream.isatty()
        if show_hostname:
            self.hostname = re.sub('\.local$', '', socket.gethostname())
        if show_name:
            self.pid = os.getpid()

    def emit(self, record):
        """
        Called by the logging module for each log record. Formats the log
        message and passes it onto logging.StreamHandler.emit().
        """
        # Colorize the log message text.
        severity = record.levelname
        message = str(record.msg)
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
        LogRecord was created (as returned by time.time()). By default this
        returns a string in the format "YYYY-MM-DD HH:MM:SS".
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))

    def render_name(self, name):
        """
        Format the name of the logger. Receives the name of the logger used to
        log the call. By default this returns a string in the format
        "NAME[PID]" (where PID is the process ID reported by os.getpid()).
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

if __name__ == '__main__':

    # If my verbose logger is installed, we'll use that for the demo.
    try:
        from verboselogs import VerboseLogger as DemoLogger
    except ImportError:
        from logging import getLogger as DemoLogger

    # Initialize the logger.
    logger = DemoLogger('coloredlogs-demo')
    logger.addHandler(ColoredStreamHandler(show_name=True))
    logger.setLevel(logging.DEBUG)

    # Print some examples with different timestamps.
    for level in ['debug', 'verbose', 'info', 'warn', 'error', 'critical']:
        if hasattr(logger, level):
            getattr(logger, level)("message with level %r", level)
            time.sleep(1)

    # Show how exceptions are logged.
    try:
        class RandomException(Exception):
            pass
        raise RandomException, "Something went horribly wrong!"
    except Exception, e:
        logger.exception(e)
    logger.info("Done, exiting ..")
    sys.exit(0)
