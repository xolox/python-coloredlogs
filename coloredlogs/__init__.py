# Colored terminal output for Python's logging module.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 23, 2017
# URL: https://coloredlogs.readthedocs.io

"""
Colored terminal output for Python's :mod:`logging` module.

.. contents::
   :local:

Getting started
===============

The easiest way to get started is by importing :mod:`coloredlogs` and calling
:mod:`coloredlogs.install()` (similar to :func:`logging.basicConfig()`):

 >>> import coloredlogs, logging
 >>> coloredlogs.install(level='DEBUG')
 >>> logger = logging.getLogger('some.module.name')
 >>> logger.info("this is an informational message")
 2015-10-22 19:13:52 peter-macbook some.module.name[28036] INFO this is an informational message

The :mod:`~coloredlogs.install()` function creates a :class:`ColoredFormatter`
that injects `ANSI escape sequences`_ into the log output.

.. _ANSI escape sequences: https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

Environment variables
=====================

The following environment variables can be used to configure the
:mod:`coloredlogs` module without writing any code:

=============================  ============================  ==================================
Environment variable           Default value                 Type of value
=============================  ============================  ==================================
``$COLOREDLOGS_AUTO_INSTALL``  'false'                       a boolean that controls whether
                                                             :func:`auto_install()` is called
``$COLOREDLOGS_LOG_LEVEL``     'INFO'                        a log level name
``$COLOREDLOGS_LOG_FORMAT``    :data:`DEFAULT_LOG_FORMAT`    a log format string
``$COLOREDLOGS_DATE_FORMAT``   :data:`DEFAULT_DATE_FORMAT`   a date/time format string
``$COLOREDLOGS_LEVEL_STYLES``  :data:`DEFAULT_LEVEL_STYLES`  see :func:`parse_encoded_styles()`
``$COLOREDLOGS_FIELD_STYLES``  :data:`DEFAULT_FIELD_STYLES`  see :func:`parse_encoded_styles()`
=============================  ============================  ==================================

Examples of customization
=========================

Here we'll take a look at some examples of how you can customize
:mod:`coloredlogs` using environment variables.

.. contents::
   :local:

Changing the log format
-----------------------

The simplest customization is to change the log format, for example:

.. code-block:: sh

   $ export COLOREDLOGS_LOG_FORMAT='[%(hostname)s] %(asctime)s - %(message)s'
   $ coloredlogs --demo
   [peter-macbook] 2015-10-22 23:42:28 - message with level 'debug'
   [peter-macbook] 2015-10-22 23:42:29 - message with level 'verbose'
   ...

Here's what that looks like in a terminal (I always work in terminals with a
black background and white text):

.. image:: images/custom-log-format.png
   :alt: Screen shot of colored logging with custom log format.
   :align: center
   :width: 80%

Changing the date/time format
-----------------------------

You can also change the date/time format, for example you can remove the date
part and leave only the time:

.. code-block:: sh

   $ export COLOREDLOGS_LOG_FORMAT='%(asctime)s - %(message)s'
   $ export COLOREDLOGS_DATE_FORMAT='%H:%M:%S'
   $ coloredlogs --demo
   23:45:22 - message with level 'debug'
   23:45:23 - message with level 'verbose'
   ...

Here's what it looks like in a terminal:

.. image:: images/custom-datetime-format.png
   :alt: Screen shot of colored logging with custom date/time format.
   :align: center
   :width: 80%

Changing the colors/styles
--------------------------

Finally you can customize the colors and text styles that are used:

.. code-block:: sh

   $ export COLOREDLOGS_LOG_FORMAT='%(asctime)s - %(message)s'
   $ export COLOREDLOGS_DATE_FORMAT='%H:%M:%S'
   $ export COLOREDLOGS_FIELD_STYLES='' # no styles
   $ export COLOREDLOGS_LEVEL_STYLES='warning=yellow;error=red;critical=red,bold'
   $ coloredlogs --demo
   23:45:22 - message with level 'debug'
   23:45:23 - message with level 'verbose'
   ...

The difference isn't apparent from the above text but take a look at the
following screen shot:

.. image:: images/custom-colors.png
   :alt: Screen shot of colored logging with custom colors.
   :align: center
   :width: 80%

.. _notes about log levels:

Some notes about log levels
===========================

With regards to the handling of log levels, the :mod:`coloredlogs` package
differs from Python's :mod:`logging` module in two aspects:

1. While the :mod:`logging` module uses the default logging level
   :data:`logging.WARNING`, the :mod:`coloredlogs` package has always used
   :data:`logging.INFO` as its default log level.

2. When logging to the terminal or system log is initialized by
   :func:`install()` or :func:`.enable_system_logging()` the effective
   level [#]_ of the selected logger [#]_ is compared against the requested
   level [#]_ and if the effective level is more restrictive than the requested
   level, the logger's level will be set to the requested level (this happens
   in :func:`adjust_level()`). The reason for this is to work around a
   combination of design choices in Python's :mod:`logging` module that can
   easily confuse people who aren't already intimately familiar with it:

   - All loggers are initialized with the level :data:`logging.NOTSET`.

   - When a logger's level is set to :data:`logging.NOTSET` the
     :func:`~logging.Logger.getEffectiveLevel()` method will
     fall back to the level of the parent logger.

   - The parent of all loggers is the root logger and the root logger has its
     level set to :data:`logging.WARNING` by default (after importing the
     :mod:`logging` module).

   Effectively all user defined loggers inherit the default log level
   :data:`logging.WARNING` from the root logger, which isn't very intuitive for
   those who aren't already familiar with the hierarchical nature of the
   :mod:`logging` module.

   By avoiding this potentially confusing behavior (see `#14`_, `#18`_, `#21`_,
   `#23`_ and `#24`_), while at the same time allowing the caller to specify a
   logger object, my goal and hope is to provide sane defaults that can easily
   be changed when the need arises.

   .. [#] Refer to :func:`logging.Logger.getEffectiveLevel()` for details.
   .. [#] The logger that is passed as an argument by the caller or the root
          logger which is selected as a default when no logger is provided.
   .. [#] The log level that is passed as an argument by the caller or the
          default log level :data:`logging.INFO` when no level is provided.

   .. _#14: https://github.com/xolox/python-coloredlogs/issues/14
   .. _#18: https://github.com/xolox/python-coloredlogs/issues/18
   .. _#21: https://github.com/xolox/python-coloredlogs/pull/21
   .. _#23: https://github.com/xolox/python-coloredlogs/pull/23
   .. _#24: https://github.com/xolox/python-coloredlogs/issues/24

Classes and functions
=====================
"""

# Standard library modules.
import collections
import logging
import os
import re
import socket
import sys

# External dependencies.
from humanfriendly import coerce_boolean
from humanfriendly.compat import coerce_string, is_string
from humanfriendly.terminal import ANSI_COLOR_CODES, ansi_wrap, terminal_supports_colors
from humanfriendly.text import split

# Windows requires special handling and the first step is detecting it :-).
WINDOWS = sys.platform.startswith('win')

# Optional external dependency (only needed on Windows).
NEED_COLORAMA = WINDOWS

# Semi-standard module versioning.
__version__ = '7.3.1'

DEFAULT_LOG_LEVEL = logging.INFO
"""The default log level for :mod:`coloredlogs` (:data:`logging.INFO`)."""

DEFAULT_LOG_FORMAT = '%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s'
"""The default log format for :class:`ColoredFormatter` objects (a string)."""

DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
"""The default date/time format for :class:`ColoredFormatter` objects (a string)."""

CHROOT_FILES = ['/etc/debian_chroot']
"""A list of filenames that indicate a chroot and contain the name of the chroot."""

CAN_USE_BOLD_FONT = (not NEED_COLORAMA)
"""
Whether bold fonts can be used in default styles (a boolean).

This is disabled on Windows because in my (admittedly limited) experience the
ANSI escape sequence for bold font is simply not translated by Colorama,
instead it's printed to the terminal without any translation.
"""

DEFAULT_FIELD_STYLES = dict(
    asctime=dict(color='green'),
    hostname=dict(color='magenta'),
    levelname=dict(color='black', bold=CAN_USE_BOLD_FONT),
    programname=dict(color='cyan'),
    name=dict(color='blue'))
"""Mapping of log format names to default font styles."""

DEFAULT_LEVEL_STYLES = dict(
    spam=dict(color='green'),
    debug=dict(color='green'),
    verbose=dict(color='blue'),
    info=dict(),
    notice=dict(color='magenta'),
    warning=dict(color='yellow'),
    success=dict(color='green', bold=CAN_USE_BOLD_FONT),
    error=dict(color='red'),
    critical=dict(color='red', bold=CAN_USE_BOLD_FONT))
"""Mapping of log level names to default font styles."""


def auto_install():
    """
    Automatically call :func:`install()` when ``$COLOREDLOGS_AUTO_INSTALL`` is set.

    The `coloredlogs` package includes a `path configuration file`_ that
    automatically imports the :mod:`coloredlogs` module and calls
    :func:`auto_install()` when the environment variable
    ``$COLOREDLOGS_AUTO_INSTALL`` is set.

    This function uses :func:`~humanfriendly.coerce_boolean()` to check whether
    the value of ``$COLOREDLOGS_AUTO_INSTALL`` should be considered :data:`True`.

    .. _path configuration file: https://docs.python.org/2/library/site.html#module-site
    """
    if coerce_boolean(os.environ.get('COLOREDLOGS_AUTO_INSTALL', 'false')):
        install()


def install(level=None, **kw):
    """
    Enable colored terminal output for Python's :mod:`logging` module.

    :param level: The default logging level (an integer or a string with a
                  level name, defaults to :data:`DEFAULT_LOG_LEVEL`).
    :param logger: The logger to which the stream handler should be attached (a
                   :class:`~logging.Logger` object, defaults to the root logger).
    :param fmt: Set the logging format (a string like those accepted by
                :class:`~logging.Formatter`, defaults to
                :data:`DEFAULT_LOG_FORMAT`).
    :param overridefmt: A dictionary with custom level logging formats
                :defaults to data:`DEFAULT_LOG_FORMAT`).
    :param datefmt: Set the date/time format (a string, defaults to
                    :data:`DEFAULT_DATE_FORMAT`).
    :param milliseconds: :data:`True` to show milliseconds like :mod:`logging`
                         does by default, :data:`False` to hide milliseconds
                         (the default is :data:`False`, see `#16`_).
    :param level_styles: A dictionary with custom level styles (defaults to
                         :data:`DEFAULT_LEVEL_STYLES`).
    :param field_styles: A dictionary with custom field styles (defaults to
                         :data:`DEFAULT_FIELD_STYLES`).
    :param stream: The stream where log messages should be written to (a
                   file-like object). This defaults to :data:`None` which
                   means :class:`StandardErrorHandler` is used.
    :param isatty: :data:`True` to use a :class:`ColoredFormatter`,
                   :data:`False` to use a normal :class:`~logging.Formatter`
                   (defaults to auto-detection using
                   :func:`~humanfriendly.terminal.terminal_supports_colors()`).
    :param reconfigure: If :data:`True` (the default) multiple calls to
                        :func:`coloredlogs.install()` will each override
                        the previous configuration.
    :param use_chroot: Refer to :class:`HostNameFilter`.
    :param programname: Refer to :class:`ProgramNameFilter`.
    :param syslog: If :data:`True` then :func:`.enable_system_logging()` will
                   be called without arguments (defaults to :data:`False`). The
                   `syslog` argument may also be a number or string, in this
                   case it is assumed to be a logging level which is passed on
                   to :func:`.enable_system_logging()`.

    The :func:`coloredlogs.install()` function is similar to
    :func:`logging.basicConfig()`, both functions take a lot of optional
    keyword arguments but try to do the right thing by default:

    1. If `reconfigure` is :data:`True` (it is by default) and an existing
       :class:`~logging.StreamHandler` is found that is connected to either
       :data:`~sys.stdout` or :data:`~sys.stderr` the handler will be removed.
       This means that first calling :func:`logging.basicConfig()` and then
       calling :func:`coloredlogs.install()` will replace the stream handler
       instead of adding a duplicate stream handler. If `reconfigure` is
       :data:`False` and an existing handler is found no further steps are
       taken (to avoid installing a duplicate stream handler).

    2. A :class:`~logging.StreamHandler` is created and connected to the stream
       given by the `stream` keyword argument (:data:`sys.stderr` by
       default). The stream handler's level is set to the value of the `level`
       keyword argument.

    3. A :class:`ColoredFormatter` is created if the `isatty` keyword argument
       allows it (or auto-detection allows it), otherwise a normal
       :class:`~logging.Formatter` is created. The formatter is initialized
       with the `fmt` and `datefmt` keyword arguments (or their computed
       defaults).

    4. :func:`HostNameFilter.install()` and :func:`ProgramNameFilter.install()`
       are called to enable the use of additional fields in the log format.

    5. If the logger's level is too restrictive it is relaxed (refer to `notes
       about log levels`_ for details).

    6. The formatter is added to the handler and the handler is added to the
       logger.

    .. _issue 16: https://github.com/xolox/python-coloredlogs/issues/16
    """
    logger = kw.get('logger') or logging.getLogger()
    reconfigure = kw.get('reconfigure', True)
    stream = kw.get('stream', None)
    # Get the log level from an argument, environment variable or default and
    # convert the names of log levels to numbers to enable numeric comparison.
    if level is None:
        level = os.environ.get('COLOREDLOGS_LOG_LEVEL', DEFAULT_LOG_LEVEL)
    level = level_to_number(level)
    # Remove any existing stream handler that writes to stdout or stderr, even
    # if the stream handler wasn't created by coloredlogs because multiple
    # stream handlers (in the same hierarchy) writing to stdout or stderr would
    # create duplicate output.  `None' is a synonym for the possibly dynamic
    # value of the stderr attribute of the sys module.
    match_streams = ([sys.stdout, sys.stderr]
                     if stream in [sys.stdout, sys.stderr, None]
                     else [stream])
    match_handler = lambda handler: match_stream_handler(handler, match_streams)
    handler, logger = replace_handler(logger, match_handler, reconfigure)
    # Make sure reconfiguration is allowed or not relevant.
    if not (handler and not reconfigure):
        # Make it easy to enable system logging.
        syslog_enabled = kw.get('syslog')
        # We ignore the value `None' because it means the caller didn't opt in
        # to system logging and `False' because it means the caller explicitly
        # opted out of system logging.
        #
        # We never enable system logging on Windows because it is my impression
        # that SysLogHandler isn't intended to be used on Windows; I've had
        # reports of coloredlogs spewing extremely verbose errno 10057 warning
        # messages to the console (once for each log message I suppose).
        if syslog_enabled not in (None, False) and not WINDOWS:
            from coloredlogs.syslog import enable_system_logging
            if syslog_enabled is True:
                # If the caller passed syslog=True then we leave the choice of
                # default log level up to the coloredlogs.syslog module.
                enable_system_logging()
            else:
                # Values other than (None, True, False) are assumed to
                # represent a logging level for system logging.
                enable_system_logging(level=syslog_enabled)
        # Figure out whether we can use ANSI escape sequences.
        use_colors = kw.get('isatty', None)
        if use_colors or use_colors is None:
            if NEED_COLORAMA:
                try:
                    # On Windows we can only use ANSI escape
                    # sequences if Colorama is available.
                    import colorama
                    colorama.init()
                    use_colors = True
                except ImportError:
                    # If Colorama isn't available then we specifically
                    # shouldn't emit ANSI escape sequences!
                    use_colors = False
            elif use_colors is None:
                # Auto-detect terminal support on other platforms.
                use_colors = terminal_supports_colors(stream)
        # Create a stream handler.
        handler = logging.StreamHandler(stream) if stream else StandardErrorHandler()
        handler.setLevel(level)
        # Prepare the arguments to the formatter. The caller is
        # allowed to customize `fmt' and/or `datefmt' as desired.
        formatter_options = dict(fmt=kw.get('fmt'), datefmt=kw.get('datefmt'),
                                 overridefmt=kw.get('overridefmt'))
        # Come up with a default log format?
        if not formatter_options['fmt']:
            # Use the log format defined by the environment variable
            # $COLOREDLOGS_LOG_FORMAT or fall back to the default.
            formatter_options['fmt'] = os.environ.get('COLOREDLOGS_LOG_FORMAT') or DEFAULT_LOG_FORMAT
        # If the caller didn't specify a date/time format we'll use the format
        # defined by the environment variable $COLOREDLOGS_DATE_FORMAT (or fall
        # back to the default).
        if not formatter_options['datefmt']:
            formatter_options['datefmt'] = os.environ.get('COLOREDLOGS_DATE_FORMAT') or DEFAULT_DATE_FORMAT
        # Python's logging module shows milliseconds by default through special
        # handling in the logging.Formatter.formatTime() method [1]. Because
        # coloredlogs always defines a `datefmt' it bypasses this special
        # handling, which is fine because ever since publishing coloredlogs
        # I've never needed millisecond precision ;-). However there are users
        # of coloredlogs that do want milliseconds to be shown [2] so we
        # provide a shortcut to make it easy.
        #
        # [1] https://stackoverflow.com/questions/6290739/python-logging-use-milliseconds-in-time-format
        # [2] https://github.com/xolox/python-coloredlogs/issues/16
        if kw.get('milliseconds') and '%(msecs)' not in formatter_options['fmt']:
            formatter_options['fmt'] = formatter_options['fmt'].replace(
                '%(asctime)s', '%(asctime)s,%(msecs)03d',
            )
        # Do we need to make %(hostname) available to the formatter?
        HostNameFilter.install(
            handler=handler,
            fmt=formatter_options['fmt'],
            use_chroot=kw.get('use_chroot', True),
        )
        # Do we need to make %(programname) available to the formatter?
        ProgramNameFilter.install(
            handler=handler,
            fmt=formatter_options['fmt'],
            programname=kw.get('programname'),
        )
        # Inject additional formatter arguments specific to ColoredFormatter?
        if use_colors:
            for name, environment_name in (('field_styles', 'COLOREDLOGS_FIELD_STYLES'),
                                           ('level_styles', 'COLOREDLOGS_LEVEL_STYLES')):
                value = kw.get(name)
                if value is None:
                    # If no styles have been specified we'll fall back
                    # to the styles defined by the environment variable.
                    environment_value = os.environ.get(environment_name)
                    if environment_value is not None:
                        value = parse_encoded_styles(environment_value)
                if value is not None:
                    formatter_options[name] = value
        # Create a (possibly colored) formatter.
        if not use_colors:
            formatter_options.pop('overridefmt', None)
        formatter_type = ColoredFormatter if use_colors else logging.Formatter

        handler.setFormatter(formatter_type(**formatter_options))
        # Adjust the level of the selected logger.
        adjust_level(logger, level)
        # Install the stream handler.
        logger.addHandler(handler)


def increase_verbosity():
    """
    Increase the verbosity of the root handler by one defined level.

    Understands custom logging levels like defined by my ``verboselogs``
    module.
    """
    defined_levels = sorted(set(find_defined_levels().values()))
    current_index = defined_levels.index(get_level())
    selected_index = max(0, current_index - 1)
    set_level(defined_levels[selected_index])


def decrease_verbosity():
    """
    Decrease the verbosity of the root handler by one defined level.

    Understands custom logging levels like defined by my ``verboselogs``
    module.
    """
    defined_levels = sorted(set(find_defined_levels().values()))
    current_index = defined_levels.index(get_level())
    selected_index = min(current_index + 1, len(defined_levels) - 1)
    set_level(defined_levels[selected_index])


def is_verbose():
    """
    Check whether the log level of the root handler is set to a verbose level.

    :returns: ``True`` if the root handler is verbose, ``False`` if not.
    """
    return get_level() < DEFAULT_LOG_LEVEL


def get_level():
    """
    Get the logging level of the root handler.

    :returns: The logging level of the root handler (an integer) or
              :data:`DEFAULT_LOG_LEVEL` (if no root handler exists).
    """
    handler, logger = find_handler(logging.getLogger(), match_stream_handler)
    return handler.level if handler else DEFAULT_LOG_LEVEL


def set_level(level):
    """
    Set the logging level of the root handler.

    :param level: The logging level to filter on (an integer or string).

    If no root handler exists yet this automatically calls :func:`install()`.
    """
    handler, logger = find_handler(logging.getLogger(), match_stream_handler)
    if handler and logger:
        # Change the level of the existing handler.
        handler.setLevel(level_to_number(level))
        # Adjust the level of the selected logger.
        adjust_level(logger, level)
    else:
        # Create a new handler with the given level.
        install(level=level)


def adjust_level(logger, level):
    """
    Increase a logger's verbosity up to the requested level.

    :param logger: The logger to change (a :class:`~logging.Logger` object).
    :param level: The log level to enable (a string or number).

    This function is used by functions like :func:`install()`,
    :func:`increase_verbosity()` and :func:`.enable_system_logging()` to adjust
    a logger's level so that log messages up to the requested log level are
    propagated to the configured output handler(s).

    It uses :func:`logging.Logger.getEffectiveLevel()` to check whether
    `logger` propagates or swallows log messages of the requested `level` and
    sets the logger's level to the requested level if it would otherwise
    swallow log messages.

    Effectively this function will "widen the scope of logging" when asked to
    do so but it will never "narrow the scope of logging". This is because I am
    convinced that filtering of log messages should (primarily) be decided by
    handlers.
    """
    level = level_to_number(level)
    if logger.getEffectiveLevel() > level:
        logger.setLevel(level)


def find_defined_levels():
    """
    Find the defined logging levels.

    :returns: A dictionary with level names as keys and integers as values.

    Here's what the result looks like by default (when
    no custom levels or level names have been defined):

    >>> find_defined_levels()
    {'NOTSET': 0,
     'DEBUG': 10,
     'INFO': 20,
     'WARN': 30,
     'WARNING': 30,
     'ERROR': 40,
     'FATAL': 50,
     'CRITICAL': 50}
    """
    defined_levels = {}
    for name in dir(logging):
        if name.isupper():
            value = getattr(logging, name)
            if isinstance(value, int):
                defined_levels[name] = value
    return defined_levels


def level_to_number(value):
    """
    Coerce a logging level name to a number.

    :param value: A logging level (integer or string).
    :returns: The number of the log level (an integer).

    This function translates log level names into their numeric values. The
    :mod:`logging` module does this for us on Python 2.7 and 3.4 but fails to
    do so on Python 2.6 which :mod:`coloredlogs` still supports.
    """
    if is_string(value):
        try:
            defined_levels = find_defined_levels()
            value = defined_levels[value.upper()]
        except KeyError:
            # Don't fail on unsupported log levels.
            value = DEFAULT_LOG_LEVEL
    return value


def find_level_aliases():
    """
    Find log level names which are aliases of each other.

    :returns: A dictionary that maps aliases to their canonical name.

    .. note:: Canonical names are chosen to be the alias with the longest
              string length so that e.g. ``WARN`` is an alias for ``WARNING``
              instead of the other way around.

    Here's what the result looks like by default (when
    no custom levels or level names have been defined):

    >>> from coloredlogs import find_level_aliases
    >>> find_level_aliases()
    {'WARN': 'WARNING', 'FATAL': 'CRITICAL'}
    """
    mapping = collections.defaultdict(list)
    for name, value in find_defined_levels().items():
        mapping[value].append(name)
    aliases = {}
    for value, names in mapping.items():
        if len(names) > 1:
            names = sorted(names, key=lambda n: len(n))
            canonical_name = names.pop()
            for alias in names:
                aliases[alias] = canonical_name
    return aliases


def parse_encoded_styles(text, normalize_key=None):
    """
    Parse text styles encoded in a string into a nested data structure.

    :param text: The encoded styles (a string).
    :returns: A dictionary in the structure of the :data:`DEFAULT_FIELD_STYLES`
              and :data:`DEFAULT_LEVEL_STYLES` dictionaries.

    Here's an example of how this function works:

    >>> from coloredlogs import parse_encoded_styles
    >>> from pprint import pprint
    >>> encoded_styles = 'debug=green;warning=yellow;error=red;critical=red,bold'
    >>> pprint(parse_encoded_styles(encoded_styles))
    {'debug': {'color': 'green'},
     'warning': {'color': 'yellow'},
     'error': {'color': 'red'},
     'critical': {'bold': True, 'color': 'red'}}
    """
    parsed_styles = {}
    for token in split(text, ';'):
        name, _, styles = token.partition('=')
        parsed_styles[name] = dict(('color', word) if word in ANSI_COLOR_CODES else
                                   (word, True) for word in split(styles, ','))
    return parsed_styles


def find_hostname(use_chroot=True):
    """
    Find the host name to include in log messages.

    :param use_chroot: Use the name of the chroot when inside a chroot?
                       (boolean, defaults to :data:`True`)
    :returns: A suitable host name (a string).

    Looks for :data:`CHROOT_FILES` that have a nonempty first line (taken to be
    the chroot name). If none are found then :func:`socket.gethostname()` is
    used as a fall back.
    """
    for chroot_file in CHROOT_FILES:
        try:
            with open(chroot_file) as handle:
                first_line = next(handle)
                name = first_line.strip()
                if name:
                    return name
        except Exception:
            pass
    return socket.gethostname()


def find_program_name():
    """
    Select a suitable program name to embed in log messages.

    :returns: One of the following strings (in decreasing order of preference):

              1. The base name of the currently running Python program or
                 script (based on the value at index zero of :data:`sys.argv`).
              2. The base name of the Python executable (based on
                 :data:`sys.executable`).
              3. The string 'python'.
    """
    # Gotcha: sys.argv[0] is '-c' if Python is started with the -c option.
    return ((os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] != '-c' else '') or
            (os.path.basename(sys.executable) if sys.executable else '') or
            'python')


def replace_handler(logger, match_handler, reconfigure):
    """
    Prepare to replace a handler.

    :param logger: Refer to :func:`find_handler()`.
    :param match_handler: Refer to :func:`find_handler()`.
    :param reconfigure: :data:`True` if an existing handler should be replaced,
                        :data:`False` otherwise.
    :returns: A tuple of two values:

              1. The matched :class:`~logging.Handler` object or :data:`None`
                 if no handler was matched.
              2. The :class:`~logging.Logger` to which the matched handler was
                 attached or the logger given to :func:`replace_handler()`.
    """
    handler, other_logger = find_handler(logger, match_handler)
    if handler and other_logger and reconfigure:
        # Remove the existing handler from the logger that its attached to
        # so that we can install a new handler that behaves differently.
        other_logger.removeHandler(handler)
        # Switch to the logger that the existing handler was attached to so
        # that reconfiguration doesn't narrow the scope of logging.
        logger = other_logger
    return handler, logger


def find_handler(logger, match_handler):
    """
    Find a (specific type of) handler in the propagation tree of a logger.

    :param logger: The logger to check (a :class:`~logging.Logger` object).
    :param match_handler: A callable that receives a :class:`~logging.Handler`
                          object and returns :data:`True` to match a handler or
                          :data:`False` to skip that handler and continue
                          searching for a match.
    :returns: A tuple of two values:

              1. The matched :class:`~logging.Handler` object or :data:`None`
                 if no handler was matched.
              2. The :class:`~logging.Logger` object to which the handler is
                 attached or :data:`None` if no handler was matched.

    This function finds a logging handler (of the given type) attached to a
    logger or one of its parents (see :func:`walk_propagation_tree()`). It uses
    the undocumented :class:`~logging.Logger.handlers` attribute to find
    handlers attached to a logger, however it won't raise an exception if the
    attribute isn't available. The advantages of this approach are:

    - This works regardless of whether :mod:`coloredlogs` attached the handler
      or other Python code attached the handler.

    - This will correctly recognize the situation where the given logger has no
      handlers but :attr:`~logging.Logger.propagate` is enabled and the logger
      has a parent logger that does have a handler attached.
    """
    for logger in walk_propagation_tree(logger):
        for handler in getattr(logger, 'handlers', []):
            if match_handler(handler):
                return handler, logger
    return None, None


def match_stream_handler(handler, streams=[]):
    """
    Identify stream handlers writing to the given streams(s).

    :param handler: The :class:`~logging.Handler` class to check.
    :param streams: A sequence of streams to match (defaults to matching
                    :data:`~sys.stdout` and :data:`~sys.stderr`).
    :returns: :data:`True` if the handler is a :class:`~logging.StreamHandler`
              logging to the given stream(s), :data:`False` otherwise.

    This function can be used as a callback for :func:`find_handler()`.
    """
    return (isinstance(handler, logging.StreamHandler) and
            getattr(handler, 'stream') in (streams or (sys.stdout, sys.stderr)))


def walk_propagation_tree(logger):
    """
    Walk through the propagation hierarchy of the given logger.

    :param logger: The logger whose hierarchy to walk (a
                   :class:`~logging.Logger` object).
    :returns: A generator of :class:`~logging.Logger` objects.

    .. note:: This uses the undocumented :class:`logging.Logger.parent`
              attribute to find higher level loggers, however it won't
              raise an exception if the attribute isn't available.
    """
    while isinstance(logger, logging.Logger):
        # Yield the logger to our caller.
        yield logger
        # Check if the logger has propagation enabled.
        if logger.propagate:
            # Continue with the parent logger. We use getattr() because the
            # `parent' attribute isn't documented so properly speaking we
            # shouldn't break if it's not available.
            logger = getattr(logger, 'parent', None)
        else:
            # The propagation chain stops here.
            logger = None


class ColoredFormatter(logging.Formatter):

    """
    Log :class:`~logging.Formatter` that uses `ANSI escape sequences`_ to create colored logs.

    .. note:: If you want to use :class:`ColoredFormatter` on Windows then you
              may need to call :func:`colorama.init()`. This is done for you
              when you call :func:`coloredlogs.install()`.
    """

    formatters = {}

    def __init__(self, fmt=None, datefmt=None, level_styles=None, field_styles=None, overridefmt=None):
        """
        Initialize a :class:`ColoredFormatter` object.

        :param fmt: A log format string (defaults to :data:`DEFAULT_LOG_FORMAT`).
        :param datefmt: A date/time format string (defaults to
                        :data:`DEFAULT_DATE_FORMAT`).
        :param level_styles: A dictionary with custom level styles
                             (defaults to :data:`DEFAULT_LEVEL_STYLES`).
        :param field_styles: A dictionary with custom field styles
                             (defaults to :data:`DEFAULT_FIELD_STYLES`).

        This initializer uses :func:`colorize_format()` to inject ANSI escape
        sequences in the log format string before it is passed to the
        initializer of the base class.
        """
        self.nn = NameNormalizer()
        # The default values of the following arguments are defined here so
        # that Sphinx doesn't embed the default values in the generated
        # documentation (because the result is awkward to read).
        fmt = fmt or DEFAULT_LOG_FORMAT

        datefmt = datefmt or DEFAULT_DATE_FORMAT
        # Initialize instance attributes.
        self.level_styles = self.nn.normalize_keys(DEFAULT_LEVEL_STYLES if level_styles is None else level_styles)
        self.field_styles = self.nn.normalize_keys(DEFAULT_FIELD_STYLES if field_styles is None else field_styles)
        # Rewrite the format string to inject ANSI escape sequences and
        # initialize the superclass with the rewritten format string.
        if overridefmt is not None and isinstance(overridefmt, dict):

            for level in ['INFO', 'WARNING', 'DEBUG',
                          'CRITICAL', 'ERROR', 'VERBOSE', 'FATAL']:
                try:
                    if overridefmt.get(level) is not None:
                        _fmt = overridefmt[level].get('fmt', fmt)
                        _datefmt = overridefmt[level].get('datefmt', datefmt)
                        self.formatters[level] = logging.Formatter(
                            self.colorize_format(_fmt),
                            _datefmt
                        )
                except Exception:
                    self.formatters.pop(level, None)

        logging.Formatter.__init__(self, self.colorize_format(fmt), datefmt)

    def colorize_format(self, fmt):
        """
        Rewrite a logging format string to inject ANSI escape sequences.

        :param fmt: The log format string.
        :returns: The logging format string with ANSI escape sequences.

        This method takes a logging format string like the ones you give to
        :class:`logging.Formatter`, splits it into whitespace separated tokens
        and then processes each token as follows:

        It looks for ``%(...)`` field names in the token (from left to right). For
        each field name it checks if the field name has a style defined in the
        `field_styles` dictionary. The first field name that has a style defined
        determines the style for the complete token.

        As an example consider the default log format (:data:`DEFAULT_LOG_FORMAT`)::

         %(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s

        The default field styles (:data:`DEFAULT_FIELD_STYLES`) define a style for the
        `name` field but not for the `process` field, however because both fields
        are part of the same whitespace separated token they'll be highlighted
        together in the style defined for the `name` field.
        """
        result = []
        for token in fmt.split():
            # Look for field names in the token.
            for match in re.finditer(r'%\((\w+)\)', token):
                # Check if a style is defined for the matched field name.
                style = self.nn.get(self.field_styles, match.group(1))
                if style:
                    # If a style is defined we apply it.
                    token = ansi_wrap(token, **style)
                    # The style of the first field name that has a style defined
                    # `wins' (within each whitespace separated token).
                    break
            result.append(token)
        return ' '.join(result)

    def format(self, record):
        """
        Apply level-specific styling to log records.

        :param record: A :class:`~logging.LogRecord` object.
        :returns: The result of :func:`logging.Formatter.format()`.

        This method injects ANSI escape sequences that are specific to the
        level of each log record (because such logic cannot be expressed in the
        syntax of a log format string). It works by making a copy of the log
        record, changing the `msg` field inside the copy and passing the copy
        into the :func:`~logging.Formatter.format()` method of the base
        class.
        """
        style = self.nn.get(self.level_styles, record.levelname)
        # After the introduction of the `Empty' class it was reported in issue
        # 33 that format() can be called when `Empty' has already been garbage
        # collected. This explains the (otherwise rather out of place) `Empty
        # is not None' check in the following `if' statement. The reasoning
        # here is that it's much better to log a message without formatting
        # then to raise an exception ;-).
        #
        # For more details refer to issue 33 on GitHub:
        # https://github.com/xolox/python-coloredlogs/issues/33
        if style and Empty is not None:
            # Due to the way that Python's logging module is structured and
            # documented the only (IMHO) clean way to customize its behavior is
            # to change incoming LogRecord objects before they get to the base
            # formatter. However we don't want to break other formatters and
            # handlers, so we copy the log record.
            #
            # In the past this used copy.copy() but as reported in issue 29
            # (which is reproducible) this can cause deadlocks. The following
            # Python voodoo is intended to accomplish the same thing as
            # copy.copy() without all of the generalization and overhead that
            # we don't need for our -very limited- use case.
            #
            # For more details refer to issue 29 on GitHub:
            # https://github.com/xolox/python-coloredlogs/issues/29
            copy = Empty()
            copy.__class__ = logging.LogRecord
            copy.__dict__.update(record.__dict__)
            copy.msg = ansi_wrap(coerce_string(record.msg), **style)
            record = copy
        # Delegate the remaining formatting to the base formatter.
        if self.formatters.get(record.levelname):
            return self.formatters.get(record.levelname).format(record)
        else:
            return logging.Formatter.format(self, record)


if sys.version_info[:2] <= (2, 6):
    # On Python 2.6 the logging.LogRecord class is an old-style class
    # which means our empty class also needs to be an old-style class.
    class Empty:
        """An empty class used to copy :class:`~logging.LogRecord` objects without reinitializing them."""
else:
    # On Python 2.7 and up logging.LogRecord is a new-style class.
    class Empty(object):
        """An empty class used to copy :class:`~logging.LogRecord` objects without reinitializing them."""


class HostNameFilter(logging.Filter):

    """
    Log filter to enable the ``%(hostname)s`` format.

    Python's :mod:`logging` module doesn't expose the system's host name while
    I consider this to be a valuable addition. Fortunately it's very easy to
    expose additional fields in format strings: :func:`filter()` simply sets
    the ``hostname`` attribute of each :class:`~logging.LogRecord` object it
    receives and this is enough to enable the use of the ``%(hostname)s``
    expression in format strings.

    You can install this log filter as follows::

     >>> import coloredlogs, logging
     >>> handler = logging.StreamHandler()
     >>> handler.addFilter(coloredlogs.HostNameFilter())
     >>> handler.setFormatter(logging.Formatter('[%(hostname)s] %(message)s'))
     >>> logger = logging.getLogger()
     >>> logger.addHandler(handler)
     >>> logger.setLevel(logging.INFO)
     >>> logger.info("Does it work?")
     [peter-macbook] Does it work?

    Of course :func:`coloredlogs.install()` does all of this for you :-).
    """

    @classmethod
    def install(cls, handler, fmt=None, use_chroot=True):
        """
        Install the :class:`HostNameFilter` on a log handler (only if needed).

        :param handler: The logging handler on which to install the filter.
        :param fmt: The log format string to check for ``%(hostname)``.
        :param use_chroot: Refer to :func:`find_hostname()`.

        If `fmt` is given the filter will only be installed if `fmt` contains
        ``%(programname)``. If `fmt` is not given the filter is installed
        unconditionally.
        """
        if not (fmt and '%(hostname)' not in fmt):
            handler.addFilter(cls(use_chroot))

    def __init__(self, use_chroot=True):
        """
        Initialize a :class:`HostNameFilter` object.

        :param use_chroot: Refer to :func:`find_hostname()`.
        """
        self.hostname = find_hostname(use_chroot)

    def filter(self, record):
        """Set each :class:`~logging.LogRecord`'s `hostname` field."""
        # Modify the record.
        record.hostname = self.hostname
        # Don't filter the record.
        return 1


class ProgramNameFilter(logging.Filter):

    """
    Log filter to enable the ``%(programname)s`` format.

    Python's :mod:`logging` module doesn't expose the name of the currently
    running program while I consider this to be a useful addition. Fortunately
    it's very easy to expose additional fields in format strings:
    :func:`filter()` simply sets the ``programname`` attribute of each
    :class:`~logging.LogRecord` object it receives and this is enough to enable
    the use of the ``%(programname)s`` expression in format strings.

    Refer to :class:`HostNameFilter` for an example of how to manually install
    these log filters.
    """

    @classmethod
    def install(cls, handler, fmt, programname=None):
        """
        Install the :class:`ProgramNameFilter` (only if needed).

        :param fmt: The log format string to check for ``%(programname)``.
        :param handler: The logging handler on which to install the filter.
        :param programname: Refer to :func:`__init__()`.
        """
        if not (fmt and '%(programname)' not in fmt):
            handler.addFilter(cls(programname))

    def __init__(self, programname=None):
        """
        Initialize a :class:`ProgramNameFilter` object.

        :param programname: The program name to use (defaults to the result of
                            :func:`find_program_name()`).
        """
        self.programname = programname or find_program_name()

    def filter(self, record):
        """Set each :class:`~logging.LogRecord`'s `programname` field."""
        # Modify the record.
        record.programname = self.programname
        # Don't filter the record.
        return 1


class StandardErrorHandler(logging.StreamHandler):

    """
    A :class:`~logging.StreamHandler` that gets the value of :data:`sys.stderr` for each log message.

    The :class:`StandardErrorHandler` class enables `monkey patching of
    sys.stderr <https://github.com/xolox/python-coloredlogs/pull/31>`_. It's
    basically the same as the ``logging._StderrHandler`` class present in
    Python 3 but it will available regardless of Python version. This handler
    is used by :func:`coloredlogs.install()` to improve compatibility with the
    Python standard library.
    """

    def __init__(self, level=logging.NOTSET):
        """Initialize a :class:`StandardErrorHandler` object."""
        logging.Handler.__init__(self, level)

    @property
    def stream(self):
        """Get the value of :data:`sys.stderr` (a file-like object)."""
        return sys.stderr


class NameNormalizer(object):

    """Responsible for normalizing field and level names."""

    def __init__(self):
        """Initialize a :class:`NameNormalizer` object."""
        self.aliases = dict((k.lower(), v.lower()) for k, v in find_level_aliases().items())

    def normalize_name(self, name):
        """
        Normalize a field or level name.

        :param name: The field or level name (a string).
        :returns: The normalized name (a string).

        Transforms all strings to lowercase and resolves level name aliases
        (refer to :func:`find_level_aliases()`) to their canonical name:

        >>> from coloredlogs import NameNormalizer
        >>> from humanfriendly import format_table
        >>> nn = NameNormalizer()
        >>> sample_names = ['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL']
        >>> print(format_table([(n, nn.normalize_name(n)) for n in sample_names]))
        -----------------------
        | DEBUG    | debug    |
        | INFO     | info     |
        | WARN     | warning  |
        | WARNING  | warning  |
        | ERROR    | error    |
        | FATAL    | critical |
        | CRITICAL | critical |
        -----------------------
        """
        name = name.lower()
        if name in self.aliases:
            name = self.aliases[name]
        return name

    def normalize_keys(self, value):
        """
        Normalize the keys of a dictionary using :func:`normalize_name()`.

        :param value: The dictionary to normalize.
        :returns: A dictionary with normalized keys.
        """
        return dict((self.normalize_name(k), v) for k, v in value.items())

    def get(self, normalized_dict, name):
        """
        Get a value from a dictionary after normalizing the key.

        :param normalized_dict: A dictionary produced by :func:`normalize_keys()`.
        :param name: A key to normalize and get from the dictionary.
        :returns: The value of the normalized key (if any).
        """
        return normalized_dict.get(self.normalize_name(name))
