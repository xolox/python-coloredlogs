# Automated tests for the `coloredlogs' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 3, 2014
# URL: https://github.com/xolox/python-coloredlogs

# Standard library modules.
import logging
import random
import re
import string
import unittest

# StringIO.StringIO() vs io.StringIO().
try:
    # Python 2.x.
    from StringIO import StringIO
except ImportError:
    # Python 3.x.
    from io import StringIO

# The module we're testing.
import coloredlogs
import coloredlogs.converter

# External test dependency required to test support for custom log levels.
import verboselogs

# Compiled regular expression that matches a single line of output produced by
# ColoredStreamHandler (does not include matching of ANSI escape sequences).
PLAIN_TEXT_PATTERN = re.compile(r'''
    (?P<date> \d{4}-\d{2}-\d{2} )
    \s (?P<time> \d{2}:\d{2}:\d{2} )
    \s (?P<hostname> \S+ )
    \s (?P<logger_name> \w+ )
    \[ (?P<process_id> \d+ ) \]
    \s (?P<severity> [A-Z]+ )
    \s (?P<message> .* )
''', re.VERBOSE)

class ColoredLogsTestCase(unittest.TestCase):

    def setUp(self):
        """Start each test from a known state."""
        # Reset global state.
        coloredlogs.install()
        coloredlogs.set_level(logging.INFO)
        # Reset local state.
        self.stream = StringIO()
        self.handler = coloredlogs.ColoredStreamHandler(stream=self.stream, isatty=False)
        self.logger_name = ''.join(random.choice(string.ascii_letters) for i in range(25))
        self.logger = verboselogs.VerboseLogger(self.logger_name)
        self.logger.addHandler(self.handler)

    def test_is_verbose(self):
        """Make sure is_verbose() does what it should :-)."""
        assert coloredlogs.root_handler.level == logging.INFO
        assert not coloredlogs.is_verbose()
        coloredlogs.set_level(logging.VERBOSE)
        assert coloredlogs.is_verbose()

    def test_increase_verbosity(self):
        """Make sure increase_verbosity() respects default and custom levels."""
        assert coloredlogs.root_handler.level == logging.INFO
        coloredlogs.increase_verbosity()
        assert coloredlogs.root_handler.level == logging.VERBOSE
        coloredlogs.increase_verbosity()
        assert coloredlogs.root_handler.level == logging.DEBUG
        coloredlogs.increase_verbosity()
        assert coloredlogs.root_handler.level == logging.NOTSET
        coloredlogs.increase_verbosity()
        assert coloredlogs.root_handler.level == logging.NOTSET

    def test_decrease_verbosity(self):
        """Make sure decrease_verbosity() respects default and custom levels."""
        assert coloredlogs.root_handler.level == logging.INFO
        coloredlogs.decrease_verbosity()
        assert coloredlogs.root_handler.level == logging.WARNING
        coloredlogs.decrease_verbosity()
        assert coloredlogs.root_handler.level == logging.ERROR
        coloredlogs.decrease_verbosity()
        assert coloredlogs.root_handler.level == logging.CRITICAL
        coloredlogs.decrease_verbosity()
        assert coloredlogs.root_handler.level == logging.CRITICAL

    def test_level_discovery(self):
        """Make sure find_defined_levels() always reports the levels defined in Python's standard library."""
        for number in (0, 10, 20, 30, 40, 50):
            assert number in coloredlogs.find_defined_levels()

    def test_missing_isatty_method(self):
        """Make sure ColoredStreamHandler() doesn't break because of a missing isatty() method."""
        # This should not raise any exceptions in the constructor.
        coloredlogs.ColoredStreamHandler(stream=object())

    def test_non_string_messages(self):
        """Make sure ColoredStreamHandler() doesn't break because of non-string messages."""
        # This should not raise any exceptions; all of these values can be cast to strings.
        for value in (True, False, 0, 42, (), []):
            self.logger.info(value)

    def test_plain_text_output_format(self):
        """Inspect the plain text output of coloredlogs."""
        # Test that filtering on severity works.
        self.handler.level = logging.INFO
        self.logger.debug("No one should see this message.")
        assert len(self.stream.getvalue().strip()) ==  0
        # Test that the default output format looks okay in plain text.
        self.handler.level = logging.DEBUG
        for method, severity in ((self.logger.debug, 'DEBUG'),
                                 (self.logger.info, 'INFO'),
                                 (self.logger.verbose, 'VERBOSE'),
                                 (self.logger.warning, 'WARN'),
                                 (self.logger.error, 'ERROR'),
                                 (self.logger.critical, 'CRITICAL')):
            # Prepare the text.
            text = "This is a message with severity %r." % severity.lower()
            # Log the message with the given severity.
            method(text)
            # Get the line of output generated by the handler.
            output = self.stream.getvalue()
            lines = output.splitlines()
            last_line = lines[-1]
            assert text in last_line
            assert severity in last_line
            assert PLAIN_TEXT_PATTERN.match(last_line)

    def test_ansi_encoding(self):
        assert coloredlogs.ansi_text('bold', bold=True) == '\x1b[1mbold\x1b[0m'
        assert coloredlogs.ansi_text('faint', faint=True) == '\x1b[2mfaint\x1b[0m'
        assert coloredlogs.ansi_text('underline', underline=True) == '\x1b[4munderline\x1b[0m'
        assert coloredlogs.ansi_text('inverse', inverse=True) == '\x1b[7minverse\x1b[0m'
        assert coloredlogs.ansi_text('strike through', strike_through=True) == '\x1b[9mstrike through\x1b[0m'
        try:
            coloredlogs.ansi_text('invalid color', color='foobar')
            assert False
        except Exception:
            pass

    def test_html_conversion(self):
        ansi_encoded_text = 'I like %s - www.eelstheband.com' % coloredlogs.ansi_text('birds', bold=True, color='blue')
        assert ansi_encoded_text == 'I like \x1b[1;34mbirds\x1b[0m - www.eelstheband.com'
        html_encoded_text = coloredlogs.converter.convert(ansi_encoded_text)
        assert html_encoded_text == 'I&nbsp;like&nbsp;<span style="font-weight: bold; color: blue;">birds</span>&nbsp;-&nbsp;<a href="http://www.eelstheband.com" style="color: inherit;">www.eelstheband.com</a>'

    def test_output_interception(self):
        expected_output = 'testing, 1, 2, 3 ..'
        assert coloredlogs.converter.capture(['sh', '-c', 'echo -n %s' % expected_output]) == expected_output
