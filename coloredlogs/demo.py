# Demonstration of the coloredlogs package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 23, 2015
# URL: https://coloredlogs.readthedocs.org

"""A simple demonstration of the `coloredlogs` package."""

# Standard library modules.
import os
import time

# Modules included in our package.
import coloredlogs

# If my verbose logger is installed, we'll use that for the demo.
try:
    from verboselogs import VerboseLogger as getLogger
except ImportError:
    from logging import getLogger

# Initialize a logger for this module.
logger = getLogger(__name__)

DEMO_DELAY = float(os.environ.get('COLOREDLOGS_DEMO_DELAY', '1'))
"""The number of seconds between each message emitted by :func:`demonstrate_colored_logging()`."""


def demonstrate_colored_logging():
    """A simple demonstration of the `coloredlogs` package."""
    # Initialize colored output to the terminal, default to the
    # DEBUG logging level but enable the user the customize it.
    coloredlogs.install(level=os.environ.get('COLOREDLOGS_LOG_LEVEL', 'DEBUG'))
    # Print some examples with different timestamps.
    for level in ['debug', 'verbose', 'info', 'warn', 'error', 'critical']:
        if hasattr(logger, level):
            getattr(logger, level)("message with level %r", level)
            time.sleep(DEMO_DELAY)
    # Show how exceptions are logged.
    try:
        class RandomException(Exception):
            pass
        raise RandomException("Something went horribly wrong!")
    except Exception as e:
        logger.exception(e)
        time.sleep(DEMO_DELAY)
    logger.info("Done, exiting ..")
