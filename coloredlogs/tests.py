# Automated tests for the `coloredlogs' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: August 7, 2017
# URL: https://coloredlogs.readthedocs.io

"""Automated tests for the `coloredlogs` package."""

# Standard library modules.
import contextlib
import imp
import logging
import logging.handlers
import os
import random
import re
import string
import subprocess
import sys
import tempfile
import unittest

# External dependencies.
from humanfriendly.terminal import ansi_wrap
from mock import MagicMock

# The module we're testing.
import coloredlogs
import coloredlogs.cli
from coloredlogs import (
    CHROOT_FILES,
    ColoredFormatter,
    NameNormalizer,
    decrease_verbosity,
    find_defined_levels,
    find_handler,
    find_hostname,
    find_program_name,
    get_level,
    increase_verbosity,
    install,
    is_verbose,
    level_to_number,
    match_stream_handler,
    parse_encoded_styles,
    set_level,
    walk_propagation_tree,
)
from coloredlogs.syslog import SystemLogging, match_syslog_handler
from coloredlogs.converter import capture, convert

# External test dependencies.
from capturer import CaptureOutput
from verboselogs import VerboseLogger
from humanfriendly.compat import StringIO

# Compiled regular expression that matches a single line of output produced by
# the default log format (does not include matching of ANSI escape sequences).
PLAIN_TEXT_PATTERN = re.compile(r'''
    (?P<date> \d{4}-\d{2}-\d{2} )
    \s (?P<time> \d{2}:\d{2}:\d{2} )
    \s (?P<hostname> \S+ )
    \s (?P<logger_name> \w+ )
    \[ (?P<process_id> \d+ ) \]
    \s (?P<severity> [A-Z]+ )
    \s (?P<message> .* )
''', re.VERBOSE)

# Compiled regular expression that matches a single line of output produced by
# the default log format with milliseconds=True.
PATTERN_INCLUDING_MILLISECONDS = re.compile(r'''
    (?P<date> \d{4}-\d{2}-\d{2} )
    \s (?P<time> \d{2}:\d{2}:\d{2},\d{3} )
    \s (?P<hostname> \S+ )
    \s (?P<logger_name> \w+ )
    \[ (?P<process_id> \d+ ) \]
    \s (?P<severity> [A-Z]+ )
    \s (?P<message> .* )
''', re.VERBOSE)

# The pathname of the system log file on Ubuntu Linux (my laptops and Travis CI).
UNIX_SYSTEM_LOG = '/var/log/syslog'


def setUpModule():
    """Speed up the tests by disabling the demo's artificial delay."""
    os.environ['COLOREDLOGS_DEMO_DELAY'] = '0'
    coloredlogs.demo.DEMO_DELAY = 0


class ColoredLogsTestCase(unittest.TestCase):

    """Container for the `coloredlogs` tests."""

    def test_level_to_number(self):
        """Make sure :func:`level_to_number()` works as intended."""
        # Make sure the default levels are translated as expected.
        assert level_to_number('debug') == logging.DEBUG
        assert level_to_number('info') == logging.INFO
        assert level_to_number('warning') == logging.WARNING
        assert level_to_number('error') == logging.ERROR
        assert level_to_number('fatal') == logging.FATAL
        # Make sure bogus level names don't blow up.
        assert level_to_number('bogus-level') == logging.INFO

    def test_find_hostname(self):
        """Make sure :func:`~find_hostname()` works correctly."""
        assert find_hostname()
        # Create a temporary file as a placeholder for e.g. /etc/debian_chroot.
        fd, temporary_file = tempfile.mkstemp()
        try:
            with open(temporary_file, 'w') as handle:
                handle.write('first line\n')
                handle.write('second line\n')
            CHROOT_FILES.insert(0, temporary_file)
            # Make sure the chroot file is being read.
            assert find_hostname() == 'first line'
        finally:
            # Clean up.
            CHROOT_FILES.pop(0)
            os.unlink(temporary_file)
        # Test that unreadable chroot files don't break coloredlogs.
        try:
            CHROOT_FILES.insert(0, temporary_file)
            # Make sure that a usable value is still produced.
            assert find_hostname()
        finally:
            # Clean up.
            CHROOT_FILES.pop(0)

    def test_host_name_filter(self):
        """Make sure :func:`install()` integrates with :class:`~coloredlogs.HostNameFilter()`."""
        install(fmt='%(hostname)s')
        with CaptureOutput() as capturer:
            logging.info("A truly insignificant message ..")
            output = capturer.get_text()
            assert find_hostname() in output

    def test_program_name_filter(self):
        """Make sure :func:`install()` integrates with :class:`~coloredlogs.ProgramNameFilter()`."""
        install(fmt='%(programname)s')
        with CaptureOutput() as capturer:
            logging.info("A truly insignificant message ..")
            output = capturer.get_text()
            assert find_program_name() in output

    def test_colorama_enabled(self):
        """Test that colorama is enabled (through mocking)."""
        init_function = MagicMock()
        with mocked_colorama_module(init_function):
            # Configure logging to the terminal.
            coloredlogs.install()
            # Ensure that our mock method was called.
            assert init_function.called

    def test_colorama_missing(self):
        """Test that colorama is missing (through mocking)."""
        def init_function():
            raise ImportError
        with mocked_colorama_module(init_function):
            # Configure logging to the terminal. It is expected that internally
            # an ImportError is raised, but the exception is caught and colored
            # output is disabled.
            coloredlogs.install()
            # Find the handler that was created by coloredlogs.install().
            handler, logger = find_handler(logging.getLogger(), match_stream_handler)
            # Make sure that logging to the terminal was initialized.
            assert isinstance(handler.formatter, logging.Formatter)
            # Make sure colored logging is disabled.
            assert not isinstance(handler.formatter, ColoredFormatter)

    def test_system_logging(self):
        """Make sure the :mod:`coloredlogs.syslog` module works."""
        expected_message = random_string(50)
        with SystemLogging(programname='coloredlogs-test-suite') as syslog:
            logging.info("%s", expected_message)
            if syslog and os.path.isfile('/var/log/syslog'):
                with open('/var/log/syslog') as handle:
                    assert any(expected_message in line for line in handle)

    def test_syslog_shortcut_simple(self):
        """Make sure that ``coloredlogs.install(syslog=True)`` works."""
        with cleanup_handlers():
            expected_message = random_string(50)
            coloredlogs.install(syslog=True)
            logging.info("%s", expected_message)
            if os.path.isfile(UNIX_SYSTEM_LOG):
                with open(UNIX_SYSTEM_LOG) as handle:
                    assert any(expected_message in line for line in handle)

    def test_syslog_shortcut_enhanced(self):
        """Make sure that ``coloredlogs.install(syslog='warning')`` works."""
        with cleanup_handlers():
            the_expected_message = random_string(50)
            not_an_expected_message = random_string(50)
            coloredlogs.install(syslog='warning')
            logging.info("%s", not_an_expected_message)
            logging.warning("%s", the_expected_message)
            if os.path.isfile(UNIX_SYSTEM_LOG):
                with open(UNIX_SYSTEM_LOG) as handle:
                    assert any(the_expected_message in line for line in handle)
                    assert not any(not_an_expected_message in line for line in handle)

    def test_name_normalization(self):
        """Make sure :class:`~coloredlogs.NameNormalizer` works as intended."""
        nn = NameNormalizer()
        for canonical_name in ['debug', 'info', 'warning', 'error', 'critical']:
            assert nn.normalize_name(canonical_name) == canonical_name
            assert nn.normalize_name(canonical_name.upper()) == canonical_name
        assert nn.normalize_name('warn') == 'warning'
        assert nn.normalize_name('fatal') == 'critical'

    def test_style_parsing(self):
        """Make sure :func:`~coloredlogs.parse_encoded_styles()` works as intended."""
        encoded_styles = 'debug=green;warning=yellow;error=red;critical=red,bold'
        decoded_styles = parse_encoded_styles(encoded_styles, normalize_key=lambda k: k.upper())
        assert sorted(decoded_styles.keys()) == sorted(['debug', 'warning', 'error', 'critical'])
        assert decoded_styles['debug']['color'] == 'green'
        assert decoded_styles['warning']['color'] == 'yellow'
        assert decoded_styles['error']['color'] == 'red'
        assert decoded_styles['critical']['color'] == 'red'
        assert decoded_styles['critical']['bold'] is True

    def test_is_verbose(self):
        """Make sure is_verbose() does what it should :-)."""
        set_level(logging.INFO)
        assert not is_verbose()
        set_level(logging.DEBUG)
        assert is_verbose()
        set_level(logging.VERBOSE)
        assert is_verbose()

    def test_increase_verbosity(self):
        """Make sure increase_verbosity() respects default and custom levels."""
        # Start from a known state.
        set_level(logging.INFO)
        assert get_level() == logging.INFO
        # INFO -> VERBOSE.
        increase_verbosity()
        assert get_level() == logging.VERBOSE
        # VERBOSE -> DEBUG.
        increase_verbosity()
        assert get_level() == logging.DEBUG
        # DEBUG -> SPAM.
        increase_verbosity()
        assert get_level() == logging.SPAM
        # SPAM -> NOTSET.
        increase_verbosity()
        assert get_level() == logging.NOTSET
        # NOTSET -> NOTSET.
        increase_verbosity()
        assert get_level() == logging.NOTSET

    def test_decrease_verbosity(self):
        """Make sure decrease_verbosity() respects default and custom levels."""
        # Start from a known state.
        set_level(logging.INFO)
        assert get_level() == logging.INFO
        # INFO -> NOTICE.
        decrease_verbosity()
        assert get_level() == logging.NOTICE
        # NOTICE -> WARNING.
        decrease_verbosity()
        assert get_level() == logging.WARNING
        # WARNING -> SUCCESS.
        decrease_verbosity()
        assert get_level() == logging.SUCCESS
        # SUCCESS -> ERROR.
        decrease_verbosity()
        assert get_level() == logging.ERROR
        # ERROR -> CRITICAL.
        decrease_verbosity()
        assert get_level() == logging.CRITICAL
        # CRITICAL -> CRITICAL.
        decrease_verbosity()
        assert get_level() == logging.CRITICAL

    def test_level_discovery(self):
        """Make sure find_defined_levels() always reports the levels defined in Python's standard library."""
        defined_levels = find_defined_levels()
        level_values = defined_levels.values()
        for number in (0, 10, 20, 30, 40, 50):
            assert number in level_values

    def test_walk_propagation_tree(self):
        """Make sure walk_propagation_tree() properly walks the tree of loggers."""
        root, parent, child, grand_child = self.get_logger_tree()
        # Check the default mode of operation.
        loggers = list(walk_propagation_tree(grand_child))
        assert loggers == [grand_child, child, parent, root]
        # Now change the propagation (non-default mode of operation).
        child.propagate = False
        loggers = list(walk_propagation_tree(grand_child))
        assert loggers == [grand_child, child]

    def test_find_handler(self):
        """Make sure find_handler() works as intended."""
        root, parent, child, grand_child = self.get_logger_tree()
        # Add some handlers to the tree.
        stream_handler = logging.StreamHandler()
        syslog_handler = logging.handlers.SysLogHandler()
        child.addHandler(stream_handler)
        parent.addHandler(syslog_handler)
        # Make sure the first matching handler is returned.
        matched_handler, matched_logger = find_handler(grand_child, lambda h: isinstance(h, logging.Handler))
        assert matched_handler is stream_handler
        # Make sure the first matching handler of the given type is returned.
        matched_handler, matched_logger = find_handler(child, lambda h: isinstance(h, logging.handlers.SysLogHandler))
        assert matched_handler is syslog_handler

    def get_logger_tree(self):
        """Create and return a tree of loggers."""
        # Get the root logger.
        root = logging.getLogger()
        # Create a top level logger for ourselves.
        parent_name = random_string()
        parent = logging.getLogger(parent_name)
        # Create a child logger.
        child_name = '%s.%s' % (parent_name, random_string())
        child = logging.getLogger(child_name)
        # Create a grand child logger.
        grand_child_name = '%s.%s' % (child_name, random_string())
        grand_child = logging.getLogger(grand_child_name)
        return root, parent, child, grand_child

    def test_support_for_milliseconds(self):
        """Make sure milliseconds are hidden by default but can be easily enabled."""
        # Check that the default log format doesn't include milliseconds.
        stream = StringIO()
        install(reconfigure=True, stream=stream)
        logging.info("This should not include milliseconds.")
        assert all(map(PLAIN_TEXT_PATTERN.match, stream.getvalue().splitlines()))
        # Check that milliseconds can be enabled via a shortcut.
        stream = StringIO()
        install(milliseconds=True, reconfigure=True, stream=stream)
        logging.info("This should include milliseconds.")
        assert all(map(PATTERN_INCLUDING_MILLISECONDS.match, stream.getvalue().splitlines()))

    def test_plain_text_output_format(self):
        """Inspect the plain text output of coloredlogs."""
        logger = VerboseLogger(random_string(25))
        stream = StringIO()
        install(level=logging.NOTSET, logger=logger, stream=stream)
        # Test that filtering on severity works.
        logger.setLevel(logging.INFO)
        logger.debug("No one should see this message.")
        assert len(stream.getvalue().strip()) == 0
        # Test that the default output format looks okay in plain text.
        logger.setLevel(logging.NOTSET)
        for method, severity in ((logger.debug, 'DEBUG'),
                                 (logger.info, 'INFO'),
                                 (logger.verbose, 'VERBOSE'),
                                 (logger.warning, 'WARNING'),
                                 (logger.error, 'ERROR'),
                                 (logger.critical, 'CRITICAL')):
            # Prepare the text.
            text = "This is a message with severity %r." % severity.lower()
            # Log the message with the given severity.
            method(text)
            # Get the line of output generated by the handler.
            output = stream.getvalue()
            lines = output.splitlines()
            last_line = lines[-1]
            assert text in last_line
            assert severity in last_line
            assert PLAIN_TEXT_PATTERN.match(last_line)

    def test_html_conversion(self):
        """Check the conversion from ANSI escape sequences to HTML."""
        ansi_encoded_text = 'I like %s - www.eelstheband.com' % ansi_wrap('birds', bold=True, color='blue')
        assert ansi_encoded_text == 'I like \x1b[1;34mbirds\x1b[0m - www.eelstheband.com'
        html_encoded_text = convert(ansi_encoded_text)
        assert html_encoded_text == (
            '<code>I like <span style="font-weight:bold;color:blue">birds</span> - '
            '<a href="http://www.eelstheband.com" style="color:inherit">www.eelstheband.com</a></code>'
        )

    def test_output_interception(self):
        """Test capturing of output from external commands."""
        expected_output = 'testing, 1, 2, 3 ..'
        actual_output = capture(['echo', expected_output])
        assert actual_output.strip() == expected_output.strip()

    def test_auto_install(self):
        """Test :func:`coloredlogs.auto_install()`."""
        needle = random_string()
        command_line = [sys.executable, '-c', 'import logging; logging.info(%r)' % needle]
        # Sanity check that log messages aren't enabled by default.
        with CaptureOutput() as capturer:
            os.environ['COLOREDLOGS_AUTO_INSTALL'] = 'false'
            subprocess.call(command_line)
            output = capturer.get_text()
        assert needle not in output
        # Test that the $COLOREDLOGS_AUTO_INSTALL environment variable can be
        # used to automatically call coloredlogs.install() during initialization.
        with CaptureOutput() as capturer:
            os.environ['COLOREDLOGS_AUTO_INSTALL'] = 'true'
            subprocess.call(command_line)
            output = capturer.get_text()
        assert needle in output

    def test_cli_demo(self):
        """Test the command line colored logging demonstration."""
        with CaptureOutput() as capturer:
            main('coloredlogs', '--demo')
            output = capturer.get_text()
        # Make sure the output contains all of the expected logging level names.
        for name in 'debug', 'info', 'warning', 'error', 'critical':
            assert name.upper() in output

    def test_cli_demo_with_formatters(self):
        """Test the command line colored logging demonstration."""
        with CaptureOutput() as capturer:
            main('coloredlogs', '--demo-with-formatter')
            output = capturer.get_text()
        # Make sure the output contains all of the expected logging level names.
        for name in 'debug', 'info', 'error', 'critical':
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
    """Wrap the command line interface to make it easier to test."""
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


def random_string(length=25):
    """Generate a random string."""
    return ''.join(random.choice(string.ascii_letters) for i in range(25))


@contextlib.contextmanager
def mocked_colorama_module(init_function):
    """Context manager to ease testing of colorama integration."""
    module_name = 'colorama'
    # Create a fake module shadowing colorama.
    fake_module = imp.new_module(module_name)
    setattr(fake_module, 'init', init_function)
    # Temporarily reconfigure coloredlogs to use colorama.
    need_colorama = coloredlogs.NEED_COLORAMA
    coloredlogs.NEED_COLORAMA = True
    # Install the fake colorama module.
    saved_module = sys.modules.get(module_name, None)
    sys.modules[module_name] = fake_module
    # We've finished setting up, yield control.
    yield
    # Restore the original setting.
    coloredlogs.NEED_COLORAMA = need_colorama
    # Clean up the mock module.
    if saved_module is not None:
        sys.modules[module_name] = saved_module
    else:
        sys.modules.pop(module_name, None)


@contextlib.contextmanager
def cleanup_handlers():
    """Context manager to cleanup output handlers."""
    # There's nothing to set up so we immediately yield control.
    yield
    # After the with block ends we cleanup any output handlers.
    for match_func in match_stream_handler, match_syslog_handler:
        handler, logger = find_handler(logging.getLogger(), match_func)
        if handler and logger:
            logger.removeHandler(handler)
