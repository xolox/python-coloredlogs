coloredlogs: Colored stream handler for Python's logging module
===============================================================

.. image:: https://travis-ci.org/xolox/python-coloredlogs.svg?branch=master
   :target: https://travis-ci.org/xolox/python-coloredlogs

The ``coloredlogs.ColoredStreamHandler`` class is a simple logging handler that
inherits from `logging.StreamHandler`_ and uses `ANSI escape sequences`_ to
render your logging messages in color. It uses only standard colors so it
should work on any UNIX terminal. It's currently tested on Python 2.6, 2.7 and
3.4. This module does not support non-UNIX terminals (e.g. the Windows
console). Here is a screen shot of the demo that is printed when the command
``python -m coloredlogs.demo`` is executed:

.. image:: https://peterodding.com/code/python/coloredlogs/screenshots/terminal.png

Note that the screenshot above includes the custom logging level ``VERBOSE``
defined by my verboselogs_ module: if you install both ``coloredlogs`` and
``verboselogs`` it will Just Work (``verboselogs`` is of course not
required to use ``coloredlogs``).

The logging handler does not use ANSI escape sequences when output redirection
applies (for example when the standard error stream is being redirected to a
file or another program) so if you like the format (see below) you can use it
for your log files as well.

Format of log messages
----------------------

As can be seen in the screenshot above, the logging handler includes four
fields in every logged message by default:

1. A timestamp indicating when the event was logged. This field is visible by
   default. To hide it you can pass the keyword argument
   ``show_timestamps=False`` when you create the handler.
2. The hostname of the system on which the event was logged. This field is
   visible by default. To hide it you can pass the keyword argument
   ``show_hostname=False`` when you create the handler.
3. The name of the logger that logged the event. This field is visible by
   default. To hide it you can pass the keyword argument ``show_name=False``
   when you create the handler.
4. The human friendly name of the log level / severity.
5. The message that was logged.

Usage
-----

Here's an example of how you would use the logging handler::

   # Create a logger object.
   import logging
   logger = logging.getLogger('your-module')

   # Initialize coloredlogs.
   import coloredlogs
   coloredlogs.install(level=logging.DEBUG)

   # Some examples.
   logger.debug("this is a debugging message")
   logger.info("this is an informational message")
   logger.warn("this is a warning message")
   logger.error("this is an error message")
   logger.fatal("this is a fatal message")
   logger.critical("this is a critical message")

You can change the formatting of the output to a limited amount by subclassing
``ColoredStreamHandler`` and overriding the method(s) of your choice. For
details take a look at the `source code`_ (it's only +/- 160 lines of code,
including documentation).

For people who like Vim
-----------------------

Although the logging handler was originally meant for interactive use, it can
also be used to generate log files. In this case the ANSI escape sequences are
not used so the log file will contain plain text and no colors. If you use Vim_
and ``coloredlogs`` and would like to view your log files in color, you can try
the two Vim scripts included in the ``coloredlogs`` source distributions and
git repository:

.. image:: https://peterodding.com/code/python/coloredlogs/screenshots/vim.png

For people who like cron
------------------------

When ``coloredlogs`` is used in a cron_ job, the output that's e-mailed to you
by cron won't contain any ANSI escape sequences because ``coloredlogs``
realizes that it's not attached to an interactive terminal. If you'd like to
have colors e-mailed to you by cron there's a simple way to set it up::

    MAILTO="your-email-address@here"
    CONTENT_TYPE="text/html"
    * * * * * root ansi2html your-command

The ``ansi2html`` program is installed when you install ``coloredlogs``. It
runs ``your-command`` under the external program ``script`` (you need to have
this installed to get ``ansi2html`` working). This makes ``your-command`` think
that it's attached to an interactive terminal which means it will output ANSI
escape sequences and ``ansi2html`` converts these to HTML. Yes, this is a bit
convoluted, but it works great :-)

You can use ``ansi2html`` without ``coloredlogs``, but please note that it only
supports normal text, bold text and text with one of the foreground colors
black, red, green, yellow, blue, magenta, cyan and white (these are the
portable ANSI color codes).

Contact
-------

The latest version of ``coloredlogs`` is available on PyPi_ and GitHub_. For
bug reports please create an issue on GitHub_. If you have questions,
suggestions, etc. feel free to send me an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2013 Peter Odding.

.. External references:
.. _ANSI escape sequences: http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
.. _cron: https://en.wikipedia.org/wiki/Cron
.. _GitHub: https://github.com/xolox/python-coloredlogs
.. _logging.StreamHandler: http://docs.python.org/2/library/logging.handlers.html#streamhandler
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _peter@peterodding.com: peter@peterodding.com
.. _PyPi: https://pypi.python.org/pypi/coloredlogs
.. _source code: https://github.com/xolox/python-coloredlogs/blob/master/coloredlogs/__init__.py
.. _verboselogs: https://pypi.python.org/pypi/verboselogs
.. _Vim: http://www.vim.org/
