"""Stream replacement tests that do not require a pseudo-terminal."""

import logging
import sys
import unittest

from humanfriendly.compat import StringIO
from humanfriendly.testing import PatchedAttribute

import coloredlogs


class RecordingStream(StringIO):

    """Record when a stream is flushed."""

    def __init__(self):
        """Initialize an empty buffer."""
        StringIO.__init__(self)
        self.flush_count = 0

    def flush(self):
        """Count flushes without closing the stream."""
        self.flush_count += 1
        StringIO.flush(self)


@unittest.skipUnless(hasattr(logging.StreamHandler, 'setStream'), 'requires Python 3.7')
class StandardErrorHandlerTestCase(unittest.TestCase):

    """Check the standard StreamHandler stream replacement contract."""

    def test_replacement_flushes_and_returns_old_stream(self):
        """Replace stderr and keep the explicit stream across later redirects."""
        initial, replacement, redirected = RecordingStream(), StringIO(), StringIO()
        with PatchedAttribute(sys, 'stderr', initial):
            handler = coloredlogs.StandardErrorHandler()
            self.addCleanup(handler.close)
            self.assertIs(handler.setStream(replacement), initial)
        self.assertEqual(initial.flush_count, 1)
        with PatchedAttribute(sys, 'stderr', redirected):
            handler.handle(logging.makeLogRecord({'msg': 'replacement'}))
        self.assertEqual(replacement.getvalue(), 'replacement\n')
        self.assertEqual(redirected.getvalue(), '')
        self.assertFalse(initial.closed)

    def test_replacement_can_be_replaced_again(self):
        """Return and flush the previous explicit destination on each change."""
        handler = coloredlogs.StandardErrorHandler()
        self.addCleanup(handler.close)
        first, second = RecordingStream(), StringIO()
        handler.setStream(first)
        self.assertIs(handler.setStream(second), first)
        self.assertEqual(first.flush_count, 1)
        self.assertIs(handler.stream, second)

    def test_same_stream_is_a_noop(self):
        """Keep dynamic lookup when setStream receives the current stderr."""
        initial, redirected = RecordingStream(), StringIO()
        with PatchedAttribute(sys, 'stderr', initial):
            handler = coloredlogs.StandardErrorHandler()
            self.addCleanup(handler.close)
            self.assertIsNone(handler.setStream(initial))
            self.assertEqual(initial.flush_count, 0)
        with PatchedAttribute(sys, 'stderr', redirected):
            self.assertIs(handler.stream, redirected)

    def test_explicit_none_matches_standard_handler(self):
        """Do not interpret an explicitly assigned None as dynamic stderr."""
        handler = coloredlogs.StandardErrorHandler()
        self.addCleanup(handler.close)
        previous = handler.stream
        self.assertIs(handler.setStream(None), previous)
        self.assertIsNone(handler.stream)

    def test_installed_handler_can_redirect(self):
        """Use setStream on the handler created by install()."""
        logger = logging.Logger('stream-replacement')
        coloredlogs.install(logger=logger, fmt='%(message)s', isatty=False)
        handler, = logger.handlers
        self.addCleanup(handler.close)
        self.assertIsInstance(handler, coloredlogs.StandardErrorHandler)
        destination = StringIO()
        handler.setStream(destination)
        logger.info('installed')
        self.assertEqual(destination.getvalue(), 'installed\n')
