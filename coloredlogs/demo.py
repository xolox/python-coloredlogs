# Demonstration of the coloredlogs package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: August 7, 2017
# URL: https://coloredlogs.readthedocs.io

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
    """Interactively demonstrate the :mod:`coloredlogs` package."""
    # Initialize colored output to the terminal, default to the
    # DEBUG logging level but enable the user the customize it.
    coloredlogs.install(level=os.environ.get('COLOREDLOGS_LOG_LEVEL', 'SPAM'))
    # Print some examples with different timestamps.
    for level in ['spam', 'debug', 'verbose', 'info', 'success', 'notice', 'warning', 'error', 'critical']:
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


def demonstrate_colored_logging_with_different_formatters():
    """Interactively demonstrate the :mod:`coloredlogs` package with different formatters"""
    # Initialize colored output to the terminal, default to the
    # DEBUG logging level but enable the user the customize it.

    FORMATS = {
        "INFO": {'fmt': "%(asctime)s - %(levelname)s - "
                        "%(module)s - %(message)s"},
        "DEBUG": {'fmt': "%(asctime)s - %(levelname)s - "
                         "%(module)s::%(funcName)s @ %(lineno)d - %(message)s"},
        "WARNING": {'fmt': "%(asctime)s - %(message)s"}
        # "WARNING": {}
    }
    FIELD_STYLES = dict(
        asctime=dict(color='green'),
        hostname=dict(color='magenta'),
        levelname=dict(color='blue', bold=False),
        programname=dict(color='cyan'),
        name=dict(color='blue'),
        module=dict(color='cyan'),
        lineno=dict(color='magenta')
    )

    LEVEL_STYLES = {
        'DEBUG': {"color": "blue"},
        'INFO': {"color": "green"},
        'WARNING': {"color": "yellow"},
        'ERROR': {"color": "red"},
        'CRITICAL': {"color": 'red'},
        'FATAL': {"color": 'red'}
    }

    coloredlogs.install(level=os.environ.get('COLOREDLOGS_LOG_LEVEL', 'DEBUG'),
                        field_styles=FIELD_STYLES,
                        level_styles=LEVEL_STYLES,
                        overridefmt=FORMATS)
    # Print some examples with different timestamps.
    for level in ['spam', 'debug', 'verbose', 'info', 'notice', 'warn',
                  'error', 'critical']:
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


demonstrate_colored_logging()
demonstrate_colored_logging_with_different_formatters()
