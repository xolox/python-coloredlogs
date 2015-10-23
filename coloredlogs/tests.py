# Automated tests for the `coloredlogs' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 23, 2015
# URL: https://coloredlogs.readthedocs.org

"""Automated tests for the `coloredlogs` package."""

# Standard library modules.
import logging
import os
import random
import re
import string
import sys
import tempfile
import unittest

# External dependencies.
from humanfriendly.terminal import ansi_wrap

# The module we're testing.
import coloredlogs
import coloredlogs.cli
import coloredlogs.converter

# External test dependencies.
from capturer import CaptureOutput
from verboselogs import VerboseLogger
from humanfriendly.compat import StringIO

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

    """Container for the `coloredlogs` tests."""

    def setUp(self):
        """Start each test from a known state."""
        # Reset global state.
        coloredlogs.install()
        coloredlogs.set_level(logging.INFO)
        # Reset local state.
        self.stream = StringIO()
        self.handler = coloredlogs.ColoredStreamHandler(stream=self.stream, isatty=False)
        self.logger_name = ''.join(random.choice(string.ascii_letters) for i in range(25))
        self.logger = VerboseLogger(self.logger_name)
        self.logger.addHandler(self.handler)
        # Speed up the tests by disabling the demo's artificial delay.
        os.environ['COLOREDLOGS_DEMO_DELAY'] = '0'
        coloredlogs.demo.DEMO_DELAY = 0

    def test_find_hostname(self):
        """Make sure :func:`~coloredlogs.find_hostname()` works correctly."""
        assert coloredlogs.find_hostname()
        # Create a temporary file as a placeholder for e.g. /etc/debian_chroot.
        fd, temporary_file = tempfile.mkstemp()
        try:
            with open(temporary_file, 'w') as handle:
                handle.write('first line\n')
                handle.write('second line\n')
            coloredlogs.CHROOT_FILES.insert(0, temporary_file)
            # Make sure the chroot file is being read.
            assert coloredlogs.find_hostname() == 'first line'
        finally:
            # Clean up.
            coloredlogs.CHROOT_FILES.pop(0)
            os.unlink(temporary_file)
        # Test that unreadable chroot files don't break coloredlogs.
        try:
            coloredlogs.CHROOT_FILES.insert(0, temporary_file)
            # Make sure that a usable value is still produced.
            assert coloredlogs.find_hostname()
        finally:
            # Clean up.
            coloredlogs.CHROOT_FILES.pop(0)

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
        defined_levels = coloredlogs.find_defined_levels()
        level_values = defined_levels.values()
        for number in (0, 10, 20, 30, 40, 50):
            assert number in level_values

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
        assert len(self.stream.getvalue().strip()) == 0
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

    def test_html_conversion(self):
        """Check the conversion from ANSI escape sequences to HTML."""
        ansi_encoded_text = 'I like %s - www.eelstheband.com' % ansi_wrap('birds', bold=True, color='blue')
        assert ansi_encoded_text == 'I like \x1b[1;34mbirds\x1b[0m - www.eelstheband.com'
        html_encoded_text = coloredlogs.converter.convert(ansi_encoded_text)
        assert html_encoded_text == (
            'I&nbsp;like&nbsp;<span style="font-weight: bold; color: blue;">birds</span>&nbsp;-&nbsp;'
            '<a href="http://www.eelstheband.com" style="color: inherit;">www.eelstheband.com</a>'
        )

    def test_output_interception(self):
        """Test capturing of output from external commands."""
        expected_output = 'testing, 1, 2, 3 ..'
        assert coloredlogs.converter.capture(['sh', '-c', 'echo -n %s' % expected_output]) == expected_output

    def test_cli_demo(self):
        """Test the command line colored logging demonstration."""
        with CaptureOutput() as capturer:
            main('coloredlogs', '--demo')
            output = capturer.get_text()
        # Make sure the output contains all of the expected logging level names.
        for name in 'debug', 'info', 'warning', 'error', 'critical':
            assert name.upper() in output

    def test_cli_conversion(self):
        """Test the command line HTML conversion."""
        output = main('coloredlogs', '--convert', 'coloredlogs', '--demo', capture=True)
        # Make sure the output is encoded as HTML.
        assert '<span' in output

    def test_implicit_usage_message(self):
        """Test that the usage message is shown when no actions are given."""
        assert 'Usage:' in main('coloredlogs', capture=True)

    def test_explicit_usage_message(self):
        """Test that the usage message is shown when ``--help`` is given."""
        assert 'Usage:' in main('coloredlogs', '--help', capture=True)


def main(*arguments, **options):
    """Simple wrapper to run the command line interface."""
    capture = options.get('capture', False)
    saved_argv = sys.argv
    saved_stdout = sys.stdout
    try:
        sys.argv = arguments
        if capture:
            sys.stdout = StringIO()
        coloredlogs.cli.main()
        if capture:
            return sys.stdout.getvalue()
    finally:
        sys.argv = saved_argv
        sys.stdout = saved_stdout
