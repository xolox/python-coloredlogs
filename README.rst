coloredlogs: Colored terminal output for Python's logging module
================================================================

.. image:: https://travis-ci.org/xolox/python-coloredlogs.svg?branch=master
   :target: https://travis-ci.org/xolox/python-coloredlogs

.. image:: https://coveralls.io/repos/xolox/python-coloredlogs/badge.png?branch=master
   :target: https://coveralls.io/r/xolox/python-coloredlogs?branch=master

The `coloredlogs` package enables colored terminal output for Python's logging_
module. The ColoredFormatter_ class inherits from `logging.Formatter`_ and uses
`ANSI escape sequences`_ to render your logging messages in color. It uses only
standard colors so it should work on any UNIX terminal. It's currently tested
on Python 2.6, 2.7, 3.4, 3.5, 3.6 and PyPy. On Windows `coloredlogs`
automatically pulls in Colorama_ as a dependency and enables ANSI escape
sequence translation using Colorama. Here is a screen shot of the demo that is
printed when the command ``coloredlogs --demo`` is executed:

.. image:: https://peterodding.com/code/python/coloredlogs/screenshots/terminal.png

Note that the screenshot above includes the custom logging level `VERBOSE`
defined by my verboselogs_ package: if you install both `coloredlogs` and
`verboselogs` it will Just Work (`verboselogs` is of course not required to use
`coloredlogs`).

.. contents::
   :local:

Format of log messages
----------------------

The ColoredFormatter_ class supports user defined log formats so you can use
any log format you like. The default log format is as follows::

 %(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s

This log format results in the following output::

 2015-10-23 03:32:22 peter-macbook coloredlogs.demo[30462] DEBUG message with level 'debug'
 2015-10-23 03:32:23 peter-macbook coloredlogs.demo[30462] VERBOSE message with level 'verbose'
 2015-10-23 03:32:24 peter-macbook coloredlogs.demo[30462] INFO message with level 'info'
 ...

You can customize the log format and styling using environment variables as
well as programmatically, please refer to the `online documentation`_ for
details.

Enabling millisecond precision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're switching from `logging.basicConfig()`_ to `coloredlogs.install()`_
you may notice that timestamps no longer include milliseconds. This is because
coloredlogs doesn't output milliseconds in timestamps unless you explicitly
tell it to. There are two ways to do that:

1. The easy way is to pass the `milliseconds` argument to
   `coloredlogs.install()`_::

    coloredlogs.install(milliseconds=True)

2. Alternatively you can change the log format `to include 'msecs'`_::

    %(asctime)s,%(msecs)03d %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s

   Here's what the call to `coloredlogs.install()`_ would then look like::

    coloredlogs.install(fmt='%(asctime)s,%(msecs)03d %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s')

   Customizing the log format also enables you to change the delimiter that
   separates seconds from milliseconds (the comma above).

Usage
-----

Here's an example of how easy it is to get started:

.. code-block:: python

   import coloredlogs, logging

   # Create a logger object.
   logger = logging.getLogger(__name__)

   # By default the install() function installs a handler on the root logger,
   # this means that log messages from your code and log messages from the
   # libraries that you use will all show up on the terminal.
   coloredlogs.install(level='DEBUG')

   # If you don't want to see log messages from libraries, you can pass a
   # specific logger object to the install() function. In this case only log
   # messages originating from that logger will show up on the terminal.
   coloredlogs.install(level='DEBUG', logger=logger)

   # Some examples.
   logger.debug("this is a debugging message")
   logger.info("this is an informational message")
   logger.warning("this is a warning message")
   logger.error("this is an error message")
   logger.critical("this is a critical message")

Colored output from cron
------------------------

When `coloredlogs` is used in a cron_ job, the output that's e-mailed to you by
cron won't contain any ANSI escape sequences because `coloredlogs` realizes
that it's not attached to an interactive terminal. If you'd like to have colors
e-mailed to you by cron there are two ways to make it happen:

.. contents::
   :local:

You can use this feature without using `coloredlogs` in your Python modules,
but please note that only normal text, bold text and text with one of the
foreground colors black, red, green, yellow, blue, magenta, cyan and white
(these are the portable ANSI color codes) are supported.

Modifying your crontab
~~~~~~~~~~~~~~~~~~~~~~

Here's an example of a minimal crontab::

    MAILTO="your-email-address@here"
    CONTENT_TYPE="text/html"
    * * * * * root coloredlogs --to-html your-command

The ``coloredlogs`` program is installed when you install the `coloredlogs`
Python package. When you execute ``coloredlogs --to-html your-command`` it runs
``your-command`` under the external program ``script`` (you need to have this
installed). This makes ``your-command`` think that it's attached to an
interactive terminal which means it will output ANSI escape sequences which
will then be converted to HTML by the ``coloredlogs`` program. Yes, this is a
bit convoluted, but it works great :-)

Modifying your Python code
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ColoredCronMailer_ class provides a context manager that automatically
enables HTML output when the ``$CONTENT_TYPE`` variable has been correctly set
in the crontab.

This requires my capturer_ package which you can install using ``pip install
'coloredlogs[cron]'``. The ``[cron]`` extra will pull in capturer_ 2.4 or newer
which is required to capture the output while silencing it - otherwise you'd
get duplicate output in the emails sent by ``cron``.

The context manager can also be used to retroactively silence output that has
already been produced, this can be useful to avoid spammy cron jobs that have
nothing useful to do but still email their output to the system administrator
every few minutes :-).

Contact
-------

The latest version of `coloredlogs` is available on PyPI_ and GitHub_. The
`online documentation`_ is available on Read The Docs. For bug reports please
create an issue on GitHub_. If you have questions, suggestions, etc. feel free
to send me an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2017 Peter Odding.


.. External references:
.. _ANSI escape sequences: https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
.. _capturer: https://pypi.python.org/pypi/capturer
.. _Colorama: https://pypi.python.org/pypi/colorama
.. _ColoredCronMailer: https://coloredlogs.readthedocs.io/en/latest/#coloredlogs.converter.ColoredCronMailer
.. _ColoredFormatter: https://coloredlogs.readthedocs.io/en/latest/#coloredlogs.ColoredFormatter
.. _coloredlogs.install(): https://coloredlogs.readthedocs.io/en/latest/#coloredlogs.install
.. _cron: https://en.wikipedia.org/wiki/Cron
.. _GitHub: https://github.com/xolox/python-coloredlogs
.. _logging.basicConfig(): https://docs.python.org/2/library/logging.html#logging.basicConfig
.. _logging.Formatter: https://docs.python.org/2/library/logging.html#logging.Formatter
.. _logging: https://docs.python.org/2/library/logging.html
.. _MIT license: https://en.wikipedia.org/wiki/MIT_License
.. _online documentation: https://coloredlogs.readthedocs.io/
.. _peter@peterodding.com: peter@peterodding.com
.. _PyPI: https://pypi.python.org/pypi/coloredlogs
.. _to include 'msecs': https://stackoverflow.com/questions/6290739/python-logging-use-milliseconds-in-time-format
.. _verboselogs: https://pypi.python.org/pypi/verboselogs
