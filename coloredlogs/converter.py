# Program to convert text with ANSI escape sequences to HTML.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 17, 2017
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
from humanfriendly.terminal import ANSI_CSI, clean_terminal_output

# Portable color codes from http://en.wikipedia.org/wiki/ANSI_escape_code#Colors.
EIGHT_COLOR_PALETTE = (
    'black',
    'red',
    'rgb(78,154,6)',  # green
    'rgb(196,160,0)',  # yellow
    'blue',
    'rgb(117,80,123)',  # magenta
    'cyan',
    'white',
)

# Regular expression that matches strings we want to convert. Used to separate
# all special strings and literal output in a single pass (this allows us to
# properly encode the output without resorting to nasty hacks).
token_pattern = re.compile('(https?://\\S+|www\\.\\S+|\x1b\\[.*?m)', re.UNICODE)


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
        # the Mac OS X (BSD) implementation [2]: The command is specified
        # using the -c option and the typescript file is /dev/null.
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
            # line invocation which means it's the Mac OS X (BSD) implementation
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
    for token in token_pattern.split(text):
        if token.startswith(('http://', 'https://', 'www.')):
            url = token
            if '://' not in token:
                url = 'http://' + url
            text = url.partition('://')[2]
            token = u'<a href="%s" style="color:inherit">%s</a>' % (html_encode(url), html_encode(text))
        elif token.startswith(ANSI_CSI):
            ansi_codes = token[len(ANSI_CSI):-1].split(';')
            if ansi_codes == ['0']:
                token = '</span>'
            else:
                styles = []
                for code in ansi_codes:
                    if code == '1':
                        styles.append('font-weight:bold')
                    elif code.startswith('3') and len(code) == 2:
                        styles.append('color:%s' % EIGHT_COLOR_PALETTE[int(code[1])])
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
    text = re.sub('^ +', encode_whitespace_cb, text, 0, re.MULTILINE)
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
