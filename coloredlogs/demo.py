# Demonstration of the coloredlogs package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 10, 2014
# URL: https://github.com/xolox/python-coloredlogs

# Standard library modules.
import logging
import time

# Modules included in our package.
import coloredlogs

# If my verbose logger is installed, we'll use that for the demo.
try:
    from verboselogs import VerboseLogger as DemoLogger
except ImportError:
    from logging import getLogger as DemoLogger

# Initialize the logger and handler.
logger = DemoLogger('coloredlogs')

def main():

    # Initialize colored output to the terminal.
    coloredlogs.install(level=logging.DEBUG)

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

if __name__ == '__main__':
    main()
