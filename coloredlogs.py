#!/usr/bin/env python

"""
Colored terminal output for Python's logging module.

Author: Peter Odding <peter@peterodding.com>
Last Change: May 16, 2013

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
        self.hostname = re.sub('\.local$', '', socket.gethostname())
        self.pid = os.getpid()

    def emit(self, record):
        """
        Called by the logging module for each log record. Formats the log
        message and passes it onto logging.StreamHandler.emit().
        """
        # The plain-text fields of the formatted log message.
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.created))
        name = record.name
        severity = record.levelname
        message = str(record.msg)
        # Apply escape sequences to color the fields?
        name = self.wrap_color('blue', '%s[%s]' % (name, self.pid))
        timestamp = self.wrap_color('green', timestamp)
        if severity in ('WARNING', 'ERROR', 'CRITICAL'):
            message = self.wrap_color('red', message, bold=(severity in ('ERROR', 'CRITICAL')))
        elif severity == 'DEBUG':
            message = self.wrap_color('green', message)
        severity = self.wrap_color('black', severity, bold=True)
        # Compose the formatted log message as:
        # timestamp hostname name severity message
        parts = []
        if self.show_timestamps:
            parts.append(timestamp)
        if self.show_hostname:
            parts.append(self.wrap_color('magenta', self.hostname))
        if self.show_name:
            parts.append(name)
        if self.show_severity:
            parts.append(severity)
        parts.append(message)
        message = ' '.join(parts)
        # Copy the original record so we don't break other handlers.
        record = copy.copy(record)
        record.msg = message
        # Use the built-in stream handler to handle output.
        logging.StreamHandler.emit(self, record)

    def wrap_color(self, colorname, message, bold=False):
        """
        Wrap text in escape sequences for the given color [and style].
        """
        if self.isatty:
            return ansi_text(message, color=colorname, bold=bold)
        else:
            return message

if __name__ == '__main__':

    # Print some examples.
    import logging
    log = logging.getLogger('coloredlogs')
    log.addHandler(ColoredStreamHandler())
    log.setLevel(logging.DEBUG)
    for level in ['debug', 'info', 'warn', 'error', 'critical']:
        getattr(log, level)("level %s message", level)
        time.sleep(1)
    try:
        assert False, "Example exception"
    except AssertionError, e:
        log.exception(e)
    log.info("Done, exiting ..")
    sys.exit(0)
