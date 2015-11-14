# Colored terminal output for Python's logging module.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 14, 2015
# URL: https://coloredlogs.readthedocs.org

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

.. _ANSI escape sequences: http://en.wikipedia.org/wiki/ANSI_escape_code#Colors

Environment variables
=====================

The following environment variables can be used to configure the
:mod:`coloredlogs` module without writing any code:

=============================  ============================  ==================================
Environment variable           Default value                 Type of value
=============================  ============================  ==================================
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

Classes and functions
=====================
"""

# Semi-standard module versioning.
__version__ = '4.0'

# Standard library modules.
import collections
import copy
import logging
import os
import re
import socket
import sys
import time

# External dependencies.
from humanfriendly.compat import coerce_string, is_string
from humanfriendly.terminal import ANSI_COLOR_CODES, ansi_wrap, terminal_supports_colors
from humanfriendly.text import split

# Optional external dependency (only needed on Windows).
NEED_COLORAMA = sys.platform.startswith('win')
HAVE_COLORAMA = False
if NEED_COLORAMA:
    try:
        import colorama
        HAVE_COLORAMA = True
    except ImportError:
        pass

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
    debug=dict(color='green'),
    info=dict(),
    verbose=dict(color='blue'),
    warning=dict(color='yellow'),
    error=dict(color='red'),
    critical=dict(color='red', bold=CAN_USE_BOLD_FONT))
"""Mapping of log level names to default font styles."""

LEGACY_FORMAT_SPECIFIERS = (
    ('show_timestamps', '%(asctime)s'),
    ('show_hostname', '%(hostname)s'),
    ('show_name', '%(name)s[%(process)d]'),
    ('show_severity', '%(levelname)s'),
    # This is not actually a legacy format specifier (i.e. it was previously
    # impossible to opt out of) but by defining it here we can keep the code
    # that interacts with LEGACY_FORMAT_SPECIFIERS free from special cases.
    ('show_message', '%(message)s'),
)
"""
Legacy keyword arguments and the corresponding log formats.

This is a sequence of tuples with two values each:

1. The name of a legacy keyword argument.
2. The log format corresponding to the argument.

This information is used by :func:`generate_log_format()` to convert a legacy
call (intended for :class:`ColoredStreamHandler`) into a log format string that
can be used by :class:`ColoredFormatter`.
"""

# In coloredlogs 1.0 the coloredlogs.ansi_text() function was moved to
# humanfriendly.ansi_wrap(). Because the function signature remained the
# same the following alias enables us to preserve backwards compatibility.
ansi_text = ansi_wrap


def install(level=None, **kw):
    """
    Enable colored terminal output for Python's :mod:`logging` module.

    :param level: The default logging level (an integer or a string with a
                  level name, defaults to :data:`logging.INFO`).
    :param logger: The logger to which the stream handler should be attached (a
                   :class:`~logging.Logger` object, defaults to the root logger).
    :param fmt: Set the logging format (a string like those accepted by
                :class:`~logging.Formatter`, defaults to the result of
                :func:`generate_log_format()` for backwards compatibility).
    :param datefmt: Set the date/time format (a string, defaults to
                    :data:`DEFAULT_DATE_FORMAT`).
    :param level_styles: A dictionary with custom level styles (defaults to
                         :data:`DEFAULT_LEVEL_STYLES`).
    :param field_styles: A dictionary with custom field styles (defaults to
                         :data:`DEFAULT_FIELD_STYLES`).
    :param stream: The stream where log messages should be written to (a
                   file-like object, defaults to :data:`sys.stderr`).
    :param isatty: :data:`True` to use a :class:`ColoredFormatter`,
                   :data:`False` to use a normal :class:`~logging.Formatter`
                   (defaults to auto-detection using
                   :func:`~humanfriendly.terminal.terminal_supports_colors()`).
    :param reconfigure: If :data:`True` (the default) multiple calls to
                        :func:`coloredlogs.install()` will each override
                        the previous configuration.
    :param use_chroot: Refer to :class:`HostNameFilter`.
    :param programname: Refer to :class:`ProgramNameFilter`.
    :param syslog: If :data:`True` then :func:`~coloredlogs.syslog.enable_system_logging()`
                   will be called without arguments (defaults to :data:`False`).

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

    5. The formatter is added to the handler and the handler is added to the
       logger. The logger's level is set to :data:`logging.NOTSET` so that each
       handler gets to decide which records they filter. This makes it possible
       to have controllable verbosity on the terminal while logging at full
       verbosity to the system log or a file.
    """
    logger = kw.get('logger') or logging.getLogger()
    reconfigure = kw.get('reconfigure', True)
    stream = kw.get('stream', sys.stderr)
    # Remove any existing stream handler that writes to stdout or stderr, even
    # if the stream handler wasn't created by coloredlogs because multiple
    # stream handlers (in the same hierarchy) writing to stdout or stderr would
    # create duplicate output.
    standard_streams = (sys.stdout, sys.stderr)
    match_streams = standard_streams if stream in standard_streams else (stream,)
    match_handler = lambda handler: match_stream_handler(handler, match_streams)
    handler, logger = replace_handler(logger, match_handler, reconfigure)
    # Make sure reconfiguration is allowed or not relevant.
    if not (handler and not reconfigure):
        # Make it easy to enable system logging.
        if kw.get('syslog', False):
            from coloredlogs import syslog
            syslog.enable_system_logging()
        # Figure out whether we can use ANSI escape sequences.
        use_colors = kw.get('isatty', None)
        if use_colors or use_colors is None:
            if NEED_COLORAMA:
                if HAVE_COLORAMA:
                    # On Windows we can only use ANSI escape
                    # sequences if Colorama is available.
                    colorama.init()
                    use_colors = True
                else:
                    # If Colorama isn't available then we specifically
                    # shouldn't emit ANSI escape sequences!
                    use_colors = False
            elif use_colors is None:
                # Auto-detect terminal support on other platforms.
                use_colors = terminal_supports_colors(stream)
        # Create a stream handler.
        handler = logging.StreamHandler(stream)
        if level is None:
            level = os.environ.get('COLOREDLOGS_LOG_LEVEL') or 'INFO'
        handler.setLevel(level_to_number(level))
        # Prepare the arguments to the formatter. The caller is
        # allowed to customize `fmt' and/or `datefmt' as desired.
        formatter_options = dict(fmt=kw.get('fmt'), datefmt=kw.get('datefmt'))
        # Come up with a default log format?
        if not formatter_options['fmt']:
            if any(name in kw for name, fmt in LEGACY_FORMAT_SPECIFIERS):
                # Generate a log format based on legacy keyword arguments.
                formatter_options['fmt'] = generate_log_format(**kw)
            else:
                # Use the log format defined by the environment variable
                # $COLOREDLOGS_LOG_FORMAT (or fall back to the default).
                formatter_options['fmt'] = os.environ.get('COLOREDLOGS_LOG_FORMAT') or DEFAULT_LOG_FORMAT
        # If the caller didn't specify a date/time format we'll use the format
        # defined by the environment variable $COLOREDLOGS_DATE_FORMAT (or fall
        # back to the default).
        if not formatter_options['datefmt']:
            formatter_options['datefmt'] = os.environ.get('COLOREDLOGS_DATE_FORMAT') or DEFAULT_DATE_FORMAT
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
            # The `level_styles' argument belongs to ColoredFormatter (new)
            # while `severity_to_style' belongs to ColoredStreamHandler (old).
            # We accept both for backwards compatibility (the value's format
            # is the same, it's just the old name that was wrong :-).
            for from_name, to_name in (('level_styles', 'level_styles'),
                                       ('severity_to_style', 'level_styles'),
                                       ('field_styles', 'field_styles')):
                value = kw.get(from_name)
                if value:
                    formatter_options[to_name] = value
                    break
            # If no custom level styles have been configured we'll use the
            # custom level styles defined by the environment variable
            # $COLOREDLOGS_LEVEL_STYLES (if it has been set).
            if not formatter_options.get('level_styles'):
                override = os.environ.get('COLOREDLOGS_LEVEL_STYLES')
                if override is not None:
                    formatter_options['level_styles'] = parse_encoded_styles(override)
            # If no custom field styles have been configured we'll use the
            # custom field styles defined by the environment variable
            # $COLOREDLOGS_FIELD_STYLES (if it has been set).
            if not formatter_options.get('field_styles'):
                override = os.environ.get('COLOREDLOGS_FIELD_STYLES')
                if override is not None:
                    formatter_options['field_styles'] = parse_encoded_styles(override)
        # Create a (possibly colored) formatter.
        formatter_type = ColoredFormatter if use_colors else logging.Formatter
        handler.setFormatter(formatter_type(**formatter_options))
        # Install the stream handler.
        logger.setLevel(logging.NOTSET)
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
    return get_level() < logging.INFO


def get_level():
    """
    Get the logging level of the root handler.

    :returns: The logging level of the root handler (an integer) or
              :data:`logging.INFO` (if no root handler exists).
    """
    handler, logger = find_handler(logging.getLogger(), match_stream_handler)
    return handler.level if handler else logging.INFO


def set_level(level):
    """
    Set the logging level of the root handler.

    :param level: The logging level to filter on (an integer or string).

    If no root handler exists yet this automatically calls :func:`install()`.
    """
    handler, logger = find_handler(logging.getLogger(), match_stream_handler)
    if handler:
        # Change the level of the existing handler.
        handler.setLevel(level_to_number(level))
    else:
        # Create a new handler with the given level.
        install(level=level)


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
            value = logging.INFO
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


def generate_log_format(**kw):
    """
    Generate a log format based on "legacy" keyword arguments.

    :param kw: Any keyword arguments are matched against
               :data:`LEGACY_FORMAT_SPECIFIERS` to
               generate a log format string.
    :returns: A log format string.

    By default all of the fields defined in :data:`LEGACY_FORMAT_SPECIFIERS`
    are enabled, this means that if :func:`generate_log_format()` is called
    without any arguments the result will be the same as
    :data:`DEFAULT_LOG_FORMAT`.

    .. note:: In `coloredlogs` version 3.0 :class:`ColoredFormatter` was added
              and :func:`install()` was changed to use :class:`ColoredFormatter`
              instead of :class:`ColoredStreamHandler` (which has been deprecated).
              The :func:`generate_log_format()` function translates the keyword
              arguments accepted by :class:`ColoredStreamHandler` into a log
              format string that can be used by :class:`ColoredFormatter`. This
              enables :func:`install()` to preserve backwards compatibility
              while still switching from :class:`ColoredStreamHandler` to
              :class:`ColoredFormatter`.
    """
    return ' '.join(fmt for name, fmt in LEGACY_FORMAT_SPECIFIERS if kw.get(name, True))


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
    return ((os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] != '-c' else '')
            or (os.path.basename(sys.executable) if sys.executable else '')
            or 'python')


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
    try:
        for logger in walk_propagation_tree(logger):
            for handler in logger.handlers:
                if match_handler(handler):
                    return handler, logger
    except AttributeError:
        # If our use of undocumented implementation details (.handlers and
        # .formatter) breaks we don't want it to blow up in our face.
        pass
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

    """Log :class:`~logging.Formatter` that uses `ANSI escape sequences`_ to create colored logs."""

    def __init__(self, fmt=None, datefmt=None, level_styles=None, field_styles=None):
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
        if style:
            # Due to the way that Python's logging module is structured and
            # documented the only (IMHO) clean way to customize its behavior is
            # to change incoming LogRecord objects before they get to the base
            # formatter. However we don't want to break other formatters and
            # handlers, so we'll copy the log record.
            record = copy.copy(record)
            record.msg = ansi_wrap(coerce_string(record.msg), **style)
        # Delegate the remaining formatting to the base formatter.
        return logging.Formatter.format(self, record)


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


class ColoredStreamHandler(logging.StreamHandler):

    """
    Deprecated stream handler with hard coded log format.

    The :py:class:`ColoredStreamHandler` class implements a stream handler that
    injects `ANSI escape sequences`_ into the log output. This stream handler
    has a hard coded log format that can be customized to a limited extent
    through inheritance.

    .. warning:: This class remains only for backwards compatibility. If you're
                 writing new code consider using :func:`coloredlogs.install()`
                 and/or :class:`ColoredFormatter` instead.
    """

    # Alias preserved for backwards compatibility.
    default_severity_to_style = DEFAULT_LEVEL_STYLES

    def __init__(self, stream=None, level=logging.NOTSET, isatty=None,
                 show_name=True, show_severity=True, show_timestamps=True,
                 show_hostname=True, use_chroot=True, severity_to_style=None):
        """Initialize a :class:`ColoredStreamHandler` object."""
        stream = sys.stderr if stream is None else stream
        logging.StreamHandler.__init__(self, stream)
        self.nn = NameNormalizer()
        self.level = level
        self.show_timestamps = show_timestamps
        self.show_hostname = show_hostname
        self.show_name = show_name
        self.show_severity = show_severity
        self.severity_to_style = self.nn.normalize_keys(DEFAULT_LEVEL_STYLES)
        if severity_to_style:
            self.severity_to_style.update(self.nn.normalize_keys(severity_to_style))
        self.isatty = terminal_supports_colors(stream) if isatty is None else isatty
        if show_hostname:
            self.hostname = find_hostname()
        if show_name:
            self.pid = os.getpid()

    def emit(self, record):
        """
        Emit a formatted log record to the configured stream.

        Called by the :py:mod:`logging` module for each log record. Formats the
        log message and passes it onto :py:func:`logging.StreamHandler.emit()`.
        """
        # If the message doesn't need to be rendered we take a shortcut.
        if record.levelno < self.level:
            return
        # Make sure the log record's message is a string.
        message = coerce_string(record.msg)
        # Colorize the log message.
        message_style = self.nn.get(self.severity_to_style, record.levelname)
        if message_style:
            message = self.wrap_style(text=message, **message_style)
        # Compose the formatted log message as:
        #   timestamp hostname name severity message
        # Everything except the message text is optional.
        parts = []
        if self.show_timestamps:
            parts.append(self.wrap_style(text=self.render_timestamp(record.created), color='green'))
        if self.show_hostname:
            parts.append(self.wrap_style(text=self.hostname, color='magenta'))
        if self.show_name:
            parts.append(self.wrap_style(text=self.render_name(record.name), color='blue'))
        if self.show_severity:
            parts.append(self.wrap_style(text=record.levelname, color='black', bold=True))
        parts.append(message)
        message = ' '.join(parts)
        # Copy the original record so we don't break other handlers.
        record = copy.copy(record)
        record.msg = message
        # Use the built-in stream handler to handle output.
        logging.StreamHandler.emit(self, record)

    def render_timestamp(self, created):
        """
        Format the time stamp of the log record.

        Receives the time when the LogRecord was created (as returned by
        :py:func:`time.time()`). By default this returns a string in the format
        ``YYYY-MM-DD HH:MM:SS``.

        Subclasses can override this method to customize date/time formatting.
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))

    def render_name(self, name):
        """
        Format the name of the logger.

        Receives the name of the logger used to log the call. By default this
        returns a string in the format ``NAME[PID]`` (where PID is the process
        ID reported by :py:func:`os.getpid()`).

        Subclasses can override this method to customize logger name formatting.
        """
        return '%s[%s]' % (name, self.pid)

    def wrap_style(self, text, **kw):
        """Wrapper for :py:func:`ansi_text()` that's disabled when ``isatty=False``."""
        return ansi_wrap(text, **kw) if self.isatty else text
