Changelog
=========

The purpose of this document is to list all of the notable changes to this
project. The format was inspired by `Keep a Changelog`_. This project adheres
to `semantic versioning`_.

.. contents::
   :local:

.. _Keep a Changelog: http://keepachangelog.com/
.. _semantic versioning: http://semver.org/

`Release 10.0`_ (2018-05-13)
----------------------------

Proper format string parsing, support for ``style='{'`` (`#11`_, `#17`_, `#52`_).

Until now coloredlogs has required differently colored fields in logging format
strings to be delimited by whitespace, leading to various issues:

- Back in December 2015 issue `#11`_ was reported by someone who had expected
  to be able to style fields without whitespace in between differently.

- Until `#52`_ was merged (released as 9.2 in April 2018) any whitespace would
  be collapsed to a single space, simply as a side effect of splitting on
  whitespace.

- This implementation was so naive that it didn't support whitespace as a
  padding character in ``%()`` formatting directives, because it wasn't able to
  distinguish formatting directives from surrounding text.

In order to properly fix `#11`_ I'm now introducing a very different approach
that does distinguish formatting directives from their surrounding text, which
means whitespace is no longer required. However in order to reduce the
conceptual incompatibilities between the old versus new approach whitespace is
still significant, as follows:

1. First the logging format string is separated into formatting directives
   versus surrounding text (which means whitespace used as a padding character
   in a ``%()`` formatting directive is considered to be part of the formatting
   directive, as it should).

2. Then formatting directives and surrounding text are grouped based on
   whitespace delimiters (in the surrounding text).

3. For each group styling is selected as follows:

   1. If the group contains a single formatting directive that has a style
      defined then the whole group is styled accordingly. This is the behavior
      which provides (some level of) conceptual backwards compatibility.

   2. If the group contains multiple formatting directives that have styles
      defined then each formatting directive is styled individually and
      surrounding text isn't styled (this behavior is backwards incompatible
      but arguably an improvement over the old behavior).

While I was working on the improved format string parsing I figured it was
easiest to include support for ``style='{'`` (requested in `#17`_) from the
start in the new implementation, given that I was redoing the affected code
anyway.

.. _Release 10.0: https://github.com/xolox/python-coloredlogs/compare/9.3.1...10.0
.. _#11: https://github.com/xolox/python-coloredlogs/issues/11
.. _#17: https://github.com/xolox/python-coloredlogs/issues/17

`Release 9.3.1`_ (2018-04-30)
-----------------------------

Bug fix: Restore MacOS compatibility after publishing release 9.3.

The following build failure became apparent to me just minutes after
publishing release 9.3 so I decided to change the implementation:
https://travis-ci.org/xolox/python-coloredlogs/jobs/372806733

.. _Release 9.3.1: https://github.com/xolox/python-coloredlogs/compare/9.3...9.3.1

`Release 9.3`_ (2018-04-29)
---------------------------

Enable flexible millisecond formatting using the ``%f`` directive (`#45`_).

.. _Release 9.3: https://github.com/xolox/python-coloredlogs/compare/9.2...9.3
.. _#45: https://github.com/xolox/python-coloredlogs/issues/45

`Release 9.2`_ (2018-04-27)
---------------------------

- Merged pull request `#47`_: Switch to ``logging.getLogRecordFactory()``. In
  the merge commit I added a small performance enhancement by checking for the
  existence of ``logging.getLogRecordFactory()`` just once, when a
  ``ColoredFormatter`` object is instantiated.

- Merged pull request `#52`_: Don't change whitespace in format strings. In the
  merge commit I promoted the inline function to an instance method so that it
  can be reused by sub classes of ``ColoredFormatter``.

.. _Release 9.2: https://github.com/xolox/python-coloredlogs/compare/9.1...9.2
.. _#47: https://github.com/xolox/python-coloredlogs/pull/47
.. _#52: https://github.com/xolox/python-coloredlogs/pull/52

`Release 9.1`_ (2018-04-26)
---------------------------

- Added ``license`` key to ``setup.py`` script (`#53`_).
- Added this changelog (requested in `#55`_).

.. _Release 9.1: https://github.com/xolox/python-coloredlogs/compare/9.0...9.1
.. _#53: https://github.com/xolox/python-coloredlogs/pull/53
.. _#55: https://github.com/xolox/python-coloredlogs/issues/55

`Release 9.0`_ (2018-01-17)
---------------------------

Added support for background colors and 256 color mode (`#35`_).

Most of the changes required for this were actually implemented in the
humanfriendly_ package (see issue `#35`_). The changes in coloredlogs
are mostly related to the ANSI to HTML conversion.

One unrelated change was made, that was to use faint green for the ``SPAM`` log
level (to distinguish it from ``DEBUG``).

New features in ANSI to HTML conversion:

- Support for bright and faint colors.
- Support for underlined, strike-through and inverse text styles.

Bug fixes in ANSI to HTML conversion:

- The scheme of URLs is no longer stripped from visible output.
- Support for ``\x1b[m`` as a short hand for ``\x1b[0m`` (I only learned about
  this today when I didn't understand the empty ANSI escape sequence at the end
  of each line emitted by ``hg log``).
- Ensure that the pattern for URLs doesn't capture ANSI sequences.

- Documenting how it all works. This will follow in the next commit
  which is going to be a rather big one (hence why I see some value
  in keeping it separate from the implementation changes).

Miscellaneous changes:

- Add installation instructions to readme.
- Improve screenshots in documentation.
- Automate taking of screen shots :-).

.. _Release 9.0: https://github.com/xolox/python-coloredlogs/compare/8.0...9.0
.. _#35: https://github.com/xolox/python-coloredlogs/issues/35
.. _humanfriendly: https://humanfriendly.readthedocs.io/

`Release 8.0`_ (2018-01-05)
---------------------------

Set the default date format in a new ``formatTime()`` method (`#42`_).

I decided to bump the major version number because this change is technically
backwards incompatible, even though it concerns a minor detail (``datefmt``
being set to its default value in the initializer). Then again, this change
does improve compatibility with the behavior of the ``logging.Formatter`` class
in Python's standard library, so there's that :-).

.. _Release 8.0: https://github.com/xolox/python-coloredlogs/compare/7.3.3...8.0
.. _#42: https://github.com/xolox/python-coloredlogs/pull/42

`Release 7.3.3`_ (2018-01-05)
-----------------------------

Bug fix for ``coloredlogs --demo`` so that it always displays the ``DEBUG`` message (`#41`_).

.. _Release 7.3.3: https://github.com/xolox/python-coloredlogs/compare/7.3.2...7.3.3
.. _#41: https://github.com/xolox/python-coloredlogs/pull/41

`Release 7.3.2`_ (2018-01-05)
-----------------------------

Bug fixes and improvements to ANSI to HTML conversion:

- Make sure that conversion of empty input produces no output.
- Strip bogus ``^D`` from output captured on MacOS.
- Increase test coverage on MacOS via Travis CI.

.. _Release 7.3.2: https://github.com/xolox/python-coloredlogs/compare/7.3.1...7.3.2

`Release 7.3.1`_ (2017-11-23)
-----------------------------

Bug fix for ``get_install_requires()`` in ``setup.py`` script (fixes `#43`_).

.. _Release 7.3.1: https://github.com/xolox/python-coloredlogs/compare/7.3...7.3.1
.. _#43: https://github.com/xolox/python-coloredlogs/issues/43

`Release 7.3`_ (2017-08-07)
---------------------------

Added support for the ``SUCCESS`` log level (related to `#27`_ and `verboselogs
issue #4 <https://github.com/xolox/python-verboselogs/issues/4>`_).

.. _Release 7.3: https://github.com/xolox/python-coloredlogs/compare/7.2...7.3
.. _#27: https://github.com/xolox/python-coloredlogs/issues/27

`Release 7.2`_ (2017-08-07)
---------------------------

Merged pull requests `#34`_, `#37`_ and `#38`_:

- Include the files needed to generate the Sphinx documentation in source distributions published to PyPI (`#34`_).
- Improve documentation by removing usage of deprecated ``logger.warn()`` function (`#37`_).
- Improve documentation by using module ``__name__`` variable for logger name (`#38`_).
- Also fixed the test suite after verboselogs 1.7 was released.

.. _Release 7.2: https://github.com/xolox/python-coloredlogs/compare/7.1...7.2
.. _#34: https://github.com/xolox/python-coloredlogs/pull/34
.. _#37: https://github.com/xolox/python-coloredlogs/pull/37
.. _#38: https://github.com/xolox/python-coloredlogs/pull/38

`Release 7.1`_ (2017-07-15)
---------------------------

Make it easy to output milliseconds and improve documentation on this (`#16`_).

.. _Release 7.1: https://github.com/xolox/python-coloredlogs/compare/7.0.1...7.1
.. _#16: https://github.com/xolox/python-coloredlogs/issues/16

`Release 7.0.1`_ (2017-07-15)
-----------------------------

Try to improve robustness during garbage collection (related to `#33`_).

.. _Release 7.0.1: https://github.com/xolox/python-coloredlogs/compare/7.0...7.0.1
.. _#33: https://github.com/xolox/python-coloredlogs/issues/33

`Release 7.0`_ (2017-05-18)
---------------------------

This release improves the robustness of ANSI to HTML conversion:

- Don't break ANSI to HTML conversion on output encoding errors.
- Gracefully handle unsupported colors in converter module.
- Make it even easier to integrate with ``cron``.
- Improved the HTML encoding of whitespace.
- Wrap generated HTML in ``<code>`` by default.
- Reduced the size of generated HTML (really CSS).
- Reduced internal duplication of constants.

.. _Release 7.0: https://github.com/xolox/python-coloredlogs/compare/6.4...7.0

`Release 6.4`_ (2017-05-17)
---------------------------

Mention ``colorama.init()`` in the documentation (fixes `#25`_).

.. _Release 6.4: https://github.com/xolox/python-coloredlogs/compare/6.3...6.4
.. _#25: https://github.com/xolox/python-coloredlogs/issues/25

`Release 6.3`_ (2017-05-17)
---------------------------

Bug fix: Avoid ``copy.copy()`` deadlocks (fixes `#29`_).

This was a rather obscure issue and I expect this not to to affect most users,
but the reported breakage was definitely not intended, so it was a bug I wanted
to fix.

.. _Release 6.3: https://github.com/xolox/python-coloredlogs/compare/6.2...6.3
.. _#29: https://github.com/xolox/python-coloredlogs/issues/29

`Release 6.2`_ (2017-05-17)
---------------------------

Enable runtime patching of ``sys.stderr`` (related to `#30`_ and `#31`_).

.. _Release 6.2: https://github.com/xolox/python-coloredlogs/compare/6.1...6.2
.. _#30: https://github.com/xolox/python-coloredlogs/issues/30
.. _#31: https://github.com/xolox/python-coloredlogs/pull/31

`Release 6.1`_ (2017-04-17)
---------------------------

- Bug fix: Adjust logger level in ``set_level()``, ``increase_verbosity()``, etc. (this is a follow up to release 6.0).
- Bug fix: Never enable system logging on Windows.
- Increase test coverage (using mocking).
- Document Python 3.6 support.

.. _Release 6.1: https://github.com/xolox/python-coloredlogs/compare/6.0...6.1

`Release 6.0`_ (2017-03-10)
---------------------------

Two backwards incompatible changes were made:

- Changed log level handling in ``coloredlogs.install()``.
- Changed the default system logging level from ``DEBUG`` to ``INFO``. To make
  it easier to restore the old behavior, ``coloredlogs.install(syslog='debug')``
  is now supported.

The old and problematic behavior was as follows:

- ``coloredlogs.install()`` would unconditionally change the log level of the
  root logger to ``logging.NOTSET`` (changing it from the root logger's default
  level ``logging.WARNING``) and the log levels of handler(s) would control
  which log messages were actually emitted.

- ``enable_system_logging()`` would never change the root logger's log level,
  which meant that when ``enable_system_logging()`` was used in isolation from
  ``install()`` the default log level would implicitly be set to
  ``logging.WARNING`` (the default log level of the root logger).

Over the years I've gotten a lot of feedback about the log level handling in
the coloredlogs package, it was clearly the number one cause of confusion for
users. Here are some examples:

- https://github.com/xolox/python-coloredlogs/issues/14
- https://github.com/xolox/python-coloredlogs/issues/18
- https://github.com/xolox/python-coloredlogs/pull/21
- https://github.com/xolox/python-coloredlogs/pull/23
- https://github.com/xolox/python-coloredlogs/issues/24

My hope is that with the changes I've made in the past days, the experience for
new users will be more 'Do What I Mean' and less 'What The Fuck is Going On
Here?!' :-). Of course only time (and feedback, or lack thereof) will tell
whether I've succeeded.

.. _Release 6.0: https://github.com/xolox/python-coloredlogs/compare/5.2...6.0

`Release 5.2`_ (2016-11-01)
---------------------------

Merged pull request `#19`_: Automatically call ``coloredlogs.install()`` if
``COLOREDLOGS_AUTO_INSTALL=true``.

While merging this pull request and writing tests for it I changed
the implementation quite a bit from the original pull request:

- The environment variable was renamed from ``COLOREDLOGS_AUTOUSE`` to
  ``COLOREDLOGS_AUTO_INSTALL`` (in order to make it consistent with the other
  environment variables) and added to the documentation.

- The ``coloredlogs.pth`` file was changed in order to reduce the amount of
  code required inside the ``*.pth`` file as much as possible and create room
  to grow this feature if required, by extending ``auto_install()``. I
  seriously dislike writing out complex code in a single line, especially when
  dealing with Python code :-).

- The ``coloredlogs.pth`` file has been added to ``MANIFEST.in`` to make sure
  that ``python setup.py sdist`` copies the ``*.pth`` file into the source
  distribution archives published to PyPI.

- The ``setup.py`` script was changed to figure out the location of the
  ``lib/pythonX.Y/site-packages`` directory using distutils instead of 'hard
  coding' the site-packages name (which I dislike for various reasons).

- The ``setup.py`` script was changed to preserve compatibility with universal
  wheel distributions using what looks like an undocumented hack found through
  trial and error (the other hacks I found were much worse :-). I ran into this
  incompatibility when running the tests under ``tox``, which runs ``pip
  install`` under the hood, which in turn runs ``python setup.py bdist_wheel``
  under the hood to enable wheel caching.

.. _Release 5.2: https://github.com/xolox/python-coloredlogs/compare/5.1.1...5.2
.. _#19: https://github.com/xolox/python-coloredlogs/pull/19

`Release 5.1.1`_ (2016-10-10)
-----------------------------

- Starting from this release wheel distributions are published to PyPI.
- Refactored makefile and setup script (checkers, docs, wheels, twine, etc).
- Replaced ``coloredlogs.readthedocs.org`` with ``coloredlogs.readthedocs.io`` everywhere.

.. _Release 5.1.1: https://github.com/xolox/python-coloredlogs/compare/5.1...5.1.1

`Release 5.1`_ (2016-10-09)
---------------------------

- Bug fix: Enable command capturing on MacOS (fixes `#12`_).
- Add styles for the ``SPAM`` and ``NOTICE`` levels added by my verboselogs_ package.
- Set up automated MacOS tests on Travis CI.
- Documented Python 3.5 support.

.. _Release 5.1: https://github.com/xolox/python-coloredlogs/compare/5.0...5.1
.. _#12: https://github.com/xolox/python-coloredlogs/issues/12

`Release 5.0`_ (2015-11-14)
---------------------------

- Remove ``ColoredStreamHandler`` and related functionality, thereby breaking backwards compatibility.
- Remove Vim syntax script (impossible given user defined log formats :-).
- Improve test coverage.

.. _Release 5.0: https://github.com/xolox/python-coloredlogs/compare/4.0...5.0

`Release 4.0`_ (2015-11-14)
---------------------------

Enable reconfiguration (also: get rid of global root handler).

.. _Release 4.0: https://github.com/xolox/python-coloredlogs/compare/3.5...4.0

`Release 3.5`_ (2015-11-13)
---------------------------

- Bug fix: Never install duplicate syslog handlers.
- Added ``walk_propagation_tree()`` function (not useful in isolation :-).
- Added ``find_handler()`` function (still not very useful in isolation).

.. _Release 3.5: https://github.com/xolox/python-coloredlogs/compare/3.4...3.5

`Release 3.4`_ (2015-11-13)
---------------------------

Make it very easy to enable system logging.

.. _Release 3.4: https://github.com/xolox/python-coloredlogs/compare/3.3...3.4

`Release 3.3`_ (2015-11-13)
---------------------------

Easy to use UNIX system logging?! I know this is unrelated to the name of this
project - refer to the added documentation for more on that :-).

.. _Release 3.3: https://github.com/xolox/python-coloredlogs/compare/3.2...3.3

`Release 3.2`_ (2015-11-12)
---------------------------

- Enable ``%(programname)s`` based on ``sys.argv[0]``.
- Increase test coverage.

.. _Release 3.2: https://github.com/xolox/python-coloredlogs/compare/3.1.4...3.2

`Release 3.1.4`_ (2015-10-31)
-----------------------------

Bug fix: Don't use bold font on Windows (follow up to previous change).

.. _Release 3.1.4: https://github.com/xolox/python-coloredlogs/compare/3.1.3...3.1.4

`Release 3.1.3`_ (2015-10-27)
-----------------------------

Bug fix: Don't use bold font on Windows (not supported). For future reference,
I found this issue here: https://ci.appveyor.com/project/xolox/pip-accel/build/1.0.15

.. _Release 3.1.3: https://github.com/xolox/python-coloredlogs/compare/3.1.2...3.1.3

`Release 3.1.2`_ (2015-10-24)
-----------------------------

Bug fix for log format colorization (fixes `#9`_).

Rationale: I'm not validating the format, I just want to extract the referenced
field names, so looking for ``%(..)`` without a trailing type specifier (and
optional modifiers) is fine here.

.. _Release 3.1.2: https://github.com/xolox/python-coloredlogs/compare/3.1.1...3.1.2
.. _#9: https://github.com/xolox/python-coloredlogs/issues/9

`Release 3.1.1`_ (2015-10-23)
-----------------------------

Fixed broken Colorama reference in ``README.rst`` because it breaks the reStructuredText rendering on PyPI.

.. _Release 3.1.1: https://github.com/xolox/python-coloredlogs/compare/3.1...3.1.1

`Release 3.1`_ (2015-10-23)
---------------------------

Depend on and use Colorama on Windows (as suggested in `#2`_). I can't actually
test this because I don't have access to a Windows system, but I guess some day
someone will complain if this doesn't work as intended ;-).

.. _Release 3.1: https://github.com/xolox/python-coloredlogs/compare/3.0...3.1
.. _#2: https://github.com/xolox/python-coloredlogs/issues/2

`Release 3.0`_ (2015-10-23)
---------------------------

Major rewrite: Added ``ColoredFormatter``, deprecated ``ColoredStreamHandler``.

- Fixed `#2`_ by switching from ``connected_to_terminal()`` to
  ``terminal_supports_colors()`` (the latter understands enough about Windows
  to know it doesn't support ANSI escape sequences).

- Fixed `#6`_ by adding support for user defined formats (even using a custom
  filter to enable the use of ``%(hostname)s`` :-).

- Fixed `#7`_ by adding support for user defined formats and making
  ``coloredlogs.install()`` an almost equivalent of ``logging.basicConfig()``.

This rewrite mostly resolves `pip-accel issue #59
<https://github.com/paylogic/pip-accel/issues/59>`_. Basically all that's
missing is a configuration option in pip-accel to make it easier to customize
the log format, although that can now be done by setting
``$COLOREDLOGS_LOG_FORMAT``.

.. _Release 3.0: https://github.com/xolox/python-coloredlogs/compare/2.0...3.0
.. _#2: https://github.com/xolox/python-coloredlogs/issues/2
.. _#6: https://github.com/xolox/python-coloredlogs/issues/6
.. _#7: https://github.com/xolox/python-coloredlogs/issues/7

`Release 2.0`_ (2015-10-14)
---------------------------

- Backwards incompatible: Change ``ansi2html`` to ``coloredlogs --convert`` (see `#8`_).
- Implement and enforce PEP-8 and PEP-257 compliance.
- Change Read the Docs links to use HTTPS.
- Move ad-hoc coverage configuration from ``Makefile`` to ``.coveragerc``.

.. _Release 2.0: https://github.com/xolox/python-coloredlogs/compare/1.0.1...2.0
.. _#8: https://github.com/xolox/python-coloredlogs/issues/8

`Release 1.0.1`_ (2015-06-02)
-----------------------------

- Bug fix for obscure ``UnicodeDecodeError`` in ``setup.py`` (only on Python 3).
- Document PyPy as a supported (tested) Python implementation.

.. _Release 1.0.1: https://github.com/xolox/python-coloredlogs/compare/1.0...1.0.1

`Release 1.0`_ (2015-05-27)
---------------------------

- Move ``coloredlogs.ansi_text()`` to ``humanfriendly.ansi_wrap()``.
- Update ``setup.py`` to add trove classifiers and stop importing ``__version__``.
- Start linking to Read the Docs as the project homepage.

.. _Release 1.0: https://github.com/xolox/python-coloredlogs/compare/0.8...1.0

`Release 0.8`_ (2014-10-03)
---------------------------

- Merged pull request `#5`_ which makes the severity to color mapping configurable.
- Added support for bold / faint / underline / inverse / strike through text
  styles. This extends the changes in pull request `#5`_ into a generic
  severity ↔ color / style mapping and adds support for five text styles.
- Added a coverage badge to the readme.

.. _Release 0.8: https://github.com/xolox/python-coloredlogs/compare/0.7.1...0.8
.. _#5: https://github.com/xolox/python-coloredlogs/pull/5

`Release 0.7.1`_ (2014-10-02)
-----------------------------

Bug fix: Restore Python 3.4 compatibility.

.. _Release 0.7.1: https://github.com/xolox/python-coloredlogs/compare/0.7...0.7.1

`Release 0.7`_ (2014-10-02)
---------------------------

- First stab at a proper test suite (already >= 90% coverage)
- Prepare to publish documentation on Read the Docs.

.. _Release 0.7: https://github.com/xolox/python-coloredlogs/compare/0.6...0.7

`Release 0.6`_ (2014-09-21)
---------------------------

Added ``decrease_verbosity()`` function (and simplify ``increase_verbosity()``).

.. _Release 0.6: https://github.com/xolox/python-coloredlogs/compare/0.5...0.6

`Release 0.5`_ (2014-05-10)
---------------------------

- Merge pull request `#4`_ adding Python 3 compatibility.
- Start using Travis CI (so I don't accidentally drop Python 3 compatibility).
- Document supported Python versions (2.6, 2.7 & 3.4).
- Move demo code to separate ``coloredlogs.demo`` module.

.. _Release 0.5: https://github.com/xolox/python-coloredlogs/compare/0.4.9...0.5
.. _#4: https://github.com/xolox/python-coloredlogs/pull/4

`Release 0.4.9`_ (2014-05-03)
-----------------------------

Make the ``ansi2html`` command a bit more user friendly.

.. _Release 0.4.9: https://github.com/xolox/python-coloredlogs/compare/0.4.8...0.4.9

`Release 0.4.8`_ (2013-10-19)
-----------------------------

Make it possible to use ``/etc/debian_chroot`` instead of ``socket.gethostname()``.

.. _Release 0.4.8: https://github.com/xolox/python-coloredlogs/compare/0.4.7...0.4.8

`Release 0.4.7`_ (2013-09-29)
-----------------------------

Added ``is_verbose()`` function (another easy shortcut :-).

.. _Release 0.4.7: https://github.com/xolox/python-coloredlogs/compare/0.4.6...0.4.7

`Release 0.4.6`_ (2013-08-07)
-----------------------------

Added ``increase_verbosity()`` function (just an easy shortcut).

.. _Release 0.4.6: https://github.com/xolox/python-coloredlogs/compare/0.4.5...0.4.6

`Release 0.4.5`_ (2013-08-07)
-----------------------------

``ColoredStreamHandler`` now supports filtering on log level.

.. _Release 0.4.5: https://github.com/xolox/python-coloredlogs/compare/0.4.4...0.4.5

`Release 0.4.4`_ (2013-08-07)
-----------------------------

Bug fix: Protect against ``sys.stderr.isatty()`` not being defined.

.. _Release 0.4.4: https://github.com/xolox/python-coloredlogs/compare/0.4.3...0.4.4

`Release 0.4.3`_ (2013-07-21)
-----------------------------

Change: Show the logger name by default.

.. _Release 0.4.3: https://github.com/xolox/python-coloredlogs/compare/0.4.2...0.4.3

`Release 0.4.2`_ (2013-07-21)
-----------------------------

Added ``coloredlogs.install()`` function.

.. _Release 0.4.2: https://github.com/xolox/python-coloredlogs/compare/0.4.1...0.4.2

`Release 0.4.1`_ (2013-07-20)
-----------------------------

Bug fix for ``ansi2html``: Don't leave ``typescript`` files behind.

.. _Release 0.4.1: https://github.com/xolox/python-coloredlogs/compare/0.4...0.4.1

`Release 0.4`_ (2013-07-20)
---------------------------

Added ``ansi2html`` program to convert colored text to HTML.

.. _Release 0.4: https://github.com/xolox/python-coloredlogs/compare/0.3.1...0.4

`Release 0.3.1`_ (2013-07-01)
-----------------------------

Bug fix: Support Unicode format strings (issue `#3`_).

.. _Release 0.3.1: https://github.com/xolox/python-coloredlogs/compare/0.3...0.3.1
.. _#3: https://github.com/xolox/python-coloredlogs/issues/3

`Release 0.3`_ (2013-06-06)
---------------------------

Merge pull request `#1`_: Refactor timestamp and name formatting into their own
methods so callers can override the format. I made the following significant
changes during merging:

- Added docstrings & mention subclassing in ``README.md``
- Don't call ``os.getpid()`` when the result won't be used.
- Don't call ``render_*()`` methods when results won't be used.

.. _Release 0.3: https://github.com/xolox/python-coloredlogs/compare/0.2...0.3
.. _#1: https://github.com/xolox/python-coloredlogs/pull/1

`Release 0.2`_ (2013-05-31)
---------------------------

- Change text styles (seems like an improvement to me)
- Integration with my just released verboselogs_ module.
- Improve the readme (with screenshots).
- Add PyPI link to ``coloredlogs.py``.
- Add URL to ``setup.py``.
- Vim syntax mode for colored logs!

.. _Release 0.2: https://github.com/xolox/python-coloredlogs/compare/0.1...0.2
.. _verboselogs: https://pypi.python.org/pypi/verboselogs

`Release 0.1`_ (2013-05-16)
---------------------------

Initial commit.

.. _Release 0.1: https://github.com/xolox/python-coloredlogs/tree/0.1
