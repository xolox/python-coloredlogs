# Program to convert text with ANSI escape sequences to HTML.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: January 12, 2018
# URL: https://coloredlogs.readthedocs.io

"""Convert text with ANSI escape sequences to HTML."""

# Standard library modules.
import codecs
import os
import pipes
import re
import subprocess
import tempfile

# External dependencies.
from humanfriendly.terminal import (
    ANSI_CSI,
    ANSI_TEXT_STYLES,
    clean_terminal_output,
    output,
)

EIGHT_COLOR_PALETTE = (
    '#010101',  # black
    '#DE382B',  # red
    '#39B54A',  # green
    '#FFC706',  # yellow
    '#006FB8',  # blue
    '#762671',  # magenta
    '#2CB5E9',  # cyan
    '#CCC',     # white
)
"""
A tuple of strings mapping basic color codes to CSS colors.

The items in this tuple correspond to the eight basic color codes for black,
red, green, yellow, blue, magenta, cyan and white as defined in the original
standard for ANSI escape sequences. The CSS colors are based on the `Ubuntu
color scheme`_ described on Wikipedia and they are encoded as hexadecimal
values to get the shortest strings, which reduces the size (in bytes) of
conversion output.

.. _Ubuntu color scheme: https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
"""

BRIGHT_COLOR_PALETTE = (
    '#808080',  # black
    '#F00',     # red
    '#0F0',     # green
    '#FF0',     # yellow
    '#00F',     # blue
    '#F0F',     # magenta
    '#0FF',     # cyan
    '#FFF',     # white
)
"""
A tuple of strings mapping bright color codes to CSS colors.

This tuple maps the bright color variants of :data:`EIGHT_COLOR_PALETTE`.
"""

# Compiled regular expression that matches leading spaces (indentation).
INDENT_PATTERN = re.compile('^ +', re.MULTILINE)

# Compiled regular expression that matches strings we want to convert. Used to
# separate all special strings and literal output in a single pass (this allows
# us to properly encode the output without resorting to nasty hacks).
TOKEN_PATTERN = re.compile('''
    # Wrap the pattern in a capture group so that re.split() includes the
    # substrings that match the pattern in the resulting list of strings.
    (
        # Match URLs with supported schemes and domain names.
        (?: https?:// | www\\. )
        # Scan until the end of the URL by matching non-whitespace characters
        # that are also not escape characters.
        [^\s\x1b]+
        # Alternatively ...
        |
        # Match (what looks like) ANSI escape sequences.
        \x1b \[ .*? m
    )
''', re.UNICODE | re.VERBOSE)


def capture(command, encoding='UTF-8'):
    """
    Capture the output of an external command as if it runs in an interactive terminal.

    :param command: The command name and its arguments (a list of strings).
    :param encoding: The encoding to use to decode the output (a string).
    :returns: The output of the command.

    This function runs an external command under ``script`` (emulating an
    interactive terminal) to capture the output of the command as if it was
    running in an interactive terminal (including ANSI escape sequences).
    """
    with open(os.devnull, 'wb') as dev_null:
        # We start by invoking the `script' program in a form that is supported
        # by the Linux implementation [1] but fails command line validation on
        # the MacOS (BSD) implementation [2]: The command is specified using
        # the -c option and the typescript file is /dev/null.
        #
        # [1] http://man7.org/linux/man-pages/man1/script.1.html
        # [2] https://developer.apple.com/legacy/library/documentation/Darwin/Reference/ManPages/man1/script.1.html
        command_line = ['script', '-qc', ' '.join(map(pipes.quote, command)), '/dev/null']
        script = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=dev_null)
        stdout, stderr = script.communicate()
        if script.returncode == 0:
            # If `script' succeeded we assume that it understood our command line
            # invocation which means it's the Linux implementation (in this case
            # we can use standard output instead of a temporary file).
            output = stdout.decode(encoding)
        else:
            # If `script' failed we assume that it didn't understand our command
            # line invocation which means it's the MacOS (BSD) implementation
            # (in this case we need a temporary file because the command line
            # interface requires it).
            fd, temporary_file = tempfile.mkstemp(prefix='coloredlogs-', suffix='-capture.txt')
            try:
                command_line = ['script', '-q', temporary_file] + list(command)
                subprocess.Popen(command_line, stdout=dev_null, stderr=dev_null).wait()
                with codecs.open(temporary_file, 'r', encoding) as handle:
                    output = handle.read()
            finally:
                os.unlink(temporary_file)
            # On MacOS when standard input is /dev/null I've observed
            # the captured output starting with the characters '^D':
            #
            #   $ script -q capture.txt echo example </dev/null
            #   example
            #   $ xxd capture.txt
            #   00000000: 5e44 0808 6578 616d 706c 650d 0a         ^D..example..
            #
            # I'm not sure why this is here, although I suppose it has to do
            # with ^D in caret notation signifying end-of-file [1]. What I do
            # know is that this is an implementation detail that callers of the
            # capture() function shouldn't be bothered with, so we strip it.
            #
            # [1] https://en.wikipedia.org/wiki/End-of-file
            if output.startswith(b'^D'):
                output = output[2:]
    # Clean up backspace and carriage return characters and the 'erase line'
    # ANSI escape sequence and return the output as a Unicode string.
    return u'\n'.join(clean_terminal_output(output))


def convert(text, code=True, tabsize=4):
    """
    Convert text with ANSI escape sequences to HTML.

    :param text: The text with ANSI escape sequences (a string).
    :param code: Whether to wrap the returned HTML fragment in a
                 ``<code>...</code>`` element (a boolean, defaults
                 to :data:`True`).
    :param tabsize: Refer to :func:`str.expandtabs()` for details.
    :returns: The text converted to HTML (a string).
    """
    output = []
    compatible_text_styles = {
        # The following ANSI text styles have an obvious mapping to CSS.
        str(ANSI_TEXT_STYLES['bold']): 'font-weight:bold',
        str(ANSI_TEXT_STYLES['strike_through']): 'text-decoration:line-through',
        str(ANSI_TEXT_STYLES['underline']): 'text-decoration:underline',
    }
    for token in TOKEN_PATTERN.split(text):
        if token.startswith(('http://', 'https://', 'www.')):
            url = token if '://' in token else ('http://' + token)
            token = u'<a href="%s" style="color:inherit">%s</a>' % (html_encode(url), html_encode(token))
        elif token.startswith(ANSI_CSI):
            ansi_codes = token[len(ANSI_CSI):-1].split(';')
            # First we check for a reset code to close the previous <span>
            # element. As explained on Wikipedia [1] an absence of codes
            # implies a reset code as well: "No parameters at all in ESC[m acts
            # like a 0 reset code".
            # [1] https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_sequences
            if '0' in ansi_codes or not ansi_codes:
                output.append('</span>')
            # Now we're ready to generate the next <span> element (if any) in
            # the knowledge that we're emitting opening <span> and closing
            # </span> tags in the correct order.
            styles = []
            is_faint = str(ANSI_TEXT_STYLES['faint']) in ansi_codes
            is_inverse = str(ANSI_TEXT_STYLES['inverse']) in ansi_codes
            for code in ansi_codes:
                if code in compatible_text_styles:
                    styles.append(compatible_text_styles[code])
                elif code.isdigit() and len(code) == 2:
                    if code.startswith('3'):
                        color_palette = EIGHT_COLOR_PALETTE
                    elif code.startswith('9'):
                        color_palette = BRIGHT_COLOR_PALETTE
                    else:
                        continue
                    color_index = int(code[1])
                    if 0 <= color_index < len(color_palette):
                        css_color = color_palette[color_index]
                        if is_inverse:
                            styles.extend((
                                'background-color:%s' % css_color,
                                'color:%s' % select_text_color(*parse_hex_color(css_color)),
                            ))
                        else:
                            if is_faint:
                                # Because I wasn't sure how to implement faint
                                # colors based on normal colors I looked at how
                                # gnome-terminal (my terminal of choice)
                                # handles this and it appears to just
                                # pick a somewhat darker color.
                                css_color = '#%02X%02X%02X' % tuple(
                                    max(0, n - 40) for n in parse_hex_color(css_color)
                                )
                            styles.append('color:%s' % css_color)
            if styles:
                token = '<span style="%s">' % ';'.join(styles)
            else:
                token = ''
        else:
            token = html_encode(token)
        output.append(token)
    html = ''.join(output)
    html = encode_whitespace(html, tabsize)
    if code:
        html = '<code>%s</code>' % html
    return html


def encode_whitespace(text, tabsize=4):
    """
    Encode whitespace so that web browsers properly render it.

    :param text: The plain text (a string).
    :param tabsize: Refer to :func:`str.expandtabs()` for details.
    :returns: The text converted to HTML (a string).

    The purpose of this function is to encode whitespace in such a way that web
    browsers render the same whitespace regardless of whether 'preformatted'
    styling is used (by wrapping the text in a ``<pre>...</pre>`` element).

    .. note:: While the string manipulation performed by this function is
              specifically intended not to corrupt the HTML generated by
              :func:`convert()` it definitely does have the potential to
              corrupt HTML from other sources. You have been warned :-).
    """
    # Convert Windows line endings (CR+LF) to UNIX line endings (LF).
    text = text.replace('\r\n', '\n')
    # Convert UNIX line endings (LF) to HTML line endings (<br>).
    text = text.replace('\n', '<br>\n')
    # Convert tabs to spaces.
    text = text.expandtabs(tabsize)
    # Convert leading spaces (that is to say spaces at the start of the string
    # and/or directly after a line ending) into non-breaking spaces, otherwise
    # HTML rendering engines will simply ignore these spaces.
    text = re.sub(INDENT_PATTERN, encode_whitespace_cb, text)
    # Convert runs of multiple spaces into non-breaking spaces to avoid HTML
    # rendering engines from visually collapsing runs of spaces into a single
    # space. We specifically don't replace single spaces for several reasons:
    # 1. We'd break the HTML emitted by convert() by replacing spaces
    #    inside HTML elements (for example the spaces that separate
    #    element names from attribute names).
    # 2. If every single space is replaced by a non-breaking space,
    #    web browsers perform awkwardly unintuitive word wrapping.
    # 3. The HTML output would be bloated for no good reason.
    text = re.sub(' {2,}', encode_whitespace_cb, text)
    return text


def encode_whitespace_cb(match):
    """
    Replace runs of multiple spaces with non-breaking spaces.

    :param match: A regular expression match object.
    :returns: The replacement string.

    This function is used by func:`encode_whitespace()` as a callback for
    replacement using a regular expression pattern.
    """
    return '&nbsp;' * len(match.group(0))


def html_encode(text):
    """
    Encode characters with a special meaning as HTML.

    :param text: The plain text (a string).
    :returns: The text converted to HTML (a string).
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text


def parse_hex_color(value):
    """
    Convert a CSS color in hexadecimal notation into its R, G, B components.

    :param value: A CSS color in hexadecimal notation (a string like '#000000').
    :return: A tuple with three integers (with values between 0 and 255)
             corresponding to the R, G and B components of the color.
    :raises: :exc:`~exceptions.ValueError` on values that can't be parsed.
    """
    if value.startswith('#'):
        value = value[1:]
    if len(value) == 3:
        return (
            int(value[0] * 2, 16),
            int(value[1] * 2, 16),
            int(value[2] * 2, 16),
        )
    elif len(value) == 6:
        return (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
        )
    else:
        raise ValueError()


def select_text_color(r, g, b):
    """
    Choose a suitable color for the inverse text style.

    :param r: The amount of red (an integer between 0 and 255).
    :param g: The amount of green (an integer between 0 and 255).
    :param b: The amount of blue (an integer between 0 and 255).
    :returns: A CSS color in hexadecimal notation (a string).

    In inverse mode the color that is normally used for the text is instead
    used for the background, however this can render the text unreadable. The
    purpose of :func:`select_text_color()` is to make an effort to select a
    suitable text color. Based on http://stackoverflow.com/a/3943023/112731.
    """
    return '#000' if (r * 0.299 + g * 0.587 + b * 0.114) > 186 else '#FFF'


class ColoredCronMailer(object):

    """
    Easy to use integration between :mod:`coloredlogs` and the UNIX ``cron`` daemon.

    By using :class:`ColoredCronMailer` as a context manager in the command
    line interface of your Python program you make it trivially easy for users
    of your program to opt in to HTML output under ``cron``: The only thing the
    user needs to do is set ``CONTENT_TYPE="text/html"`` in their crontab!

    Under the hood this requires quite a bit of magic and I must admit that I
    developed this code simply because I was curious whether it could even be
    done :-). It requires my :mod:`capturer` package which you can install
    using ``pip install 'coloredlogs[cron]'``. The ``[cron]`` extra will pull
    in the :mod:`capturer` 2.4 or newer which is required to capture the output
    while silencing it - otherwise you'd get duplicate output in the emails
    sent by ``cron``.
    """

    def __init__(self):
        """Initialize output capturing when running under ``cron`` with the correct configuration."""
        self.is_enabled = 'text/html' in os.environ.get('CONTENT_TYPE', 'text/plain')
        self.is_silent = False
        if self.is_enabled:
            # We import capturer here so that the coloredlogs[cron] extra
            # isn't required to use the other functions in this module.
            from capturer import CaptureOutput
            self.capturer = CaptureOutput(merged=True, relay=False)

    def __enter__(self):
        """Start capturing output (when applicable)."""
        if self.is_enabled:
            self.capturer.__enter__()
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Stop capturing output and convert the output to HTML (when applicable)."""
        if self.is_enabled:
            if not self.is_silent:
                # Only call output() when we captured something useful.
                text = self.capturer.get_text()
                if text and not text.isspace():
                    output(convert(text))
            self.capturer.__exit__(exc_type, exc_value, traceback)

    def silence(self):
        """
        Tell :func:`__exit__()` to swallow all output (things will be silent).

        This can be useful when a Python program is written in such a way that
        it has already produced output by the time it becomes apparent that
        nothing useful can be done (say in a cron job that runs every few
        minutes :-p). By calling :func:`silence()` the output can be swallowed
        retroactively, avoiding useless emails from ``cron``.
        """
        self.is_silent = True
