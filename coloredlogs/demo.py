# Demonstration of the coloredlogs package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 14, 2015
# URL: https://coloredlogs.readthedocs.org

"""A simple demonstration of the `coloredlogs` package."""

# Standard library modules.
import logging
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


def demonstrate_colored_logging():
    """A simple demonstration of the `coloredlogs` package."""
    # Initialize colored output to the terminal.
    coloredlogs.install()
    coloredlogs.set_level(logging.DEBUG)
    # Print some examples with different timestamps.
    for level in ['debug', 'verbose', 'info', 'warn', 'error', 'critical']:
        if hasattr(logger, level):
            getattr(logger, level)("message with level %r", level)
            time.sleep(1)
    # Show how exceptions are logged.
    try:
        class RandomException(Exception):
            pass
        raise RandomException("Something went horribly wrong!")
    except Exception as e:
        logger.exception(e)
    logger.info("Done, exiting ..")
