coloredlogs: Colored stream handler for the logging module
==========================================================

The ``ColoredStreamHandler`` class defined in the ``coloredlogs`` module is a simple logging handler that inherits from `logging.StreamHandler`_ but adds `ANSI escape sequences`_ to render your logging messages in color. It uses only standard colors so it should work on any UNIX terminal. Currently this module does not support non-UNIX terminals (e.g. the Windows console).

The log handler formats log messages including timestamps, logger names and severity levels. It uses ANSI escape sequences to highlight timestamps and debug messages in green and error and warning messages in red. The handler does not use ANSI escape sequences when output redirection applies, for example when the standard error stream is being redirected to a file. Here's an example of its use:

Here's a small demonstration of the logging handler::

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

Contact
-------

If you have questions, bug reports, suggestions, etc. please send an e-mail to `peter@peterodding.com`_. The latest version of ``coloredlogs`` will always be `available on PyPi`_.

License
-------

This software is licensed under the `MIT license`_.

© 2013 Peter Odding.

.. External references:
.. _ANSI escape sequences: http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
.. _logging.StreamHandler: http://docs.python.org/2/library/logging.handlers.html#streamhandler
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _peter@peterodding.com: peter@peterodding.com
.. _available on PyPi: https://pypi.python.org/pypi/coloredlogs
