"""
Program to convert text with ANSI escape sequences to HTML.

Author: Peter Odding <peter@peterodding.com>
Last Change: May 10, 2014
URL: https://github.com/xolox/python-coloredlogs
"""

# Standard library modules.
import pipes
import re
import subprocess
import sys
import tempfile
import webbrowser

# Portable color codes from http://en.wikipedia.org/wiki/ANSI_escape_code#Colors.
EIGHT_COLOR_PALETTE = ('black',
                       'red',
                       'rgb(78, 154, 6)', # green
                       'rgb(196, 160, 0)', # yellow
                       'blue',
                       'rgb(117, 80, 123)', # magenta
                       'cyan',
                       'white')

# Regular expression that matches strings we want to convert. Used to separate
# all special strings and literal output in a single pass (this allows us to
# properly encode the output without resorting to nasty hacks).
token_pattern = re.compile('(https?://\\S+|www\\.\\S+|\x1b\\[.*?m)', re.UNICODE)

def main():
    """
    Command line interface for the ``ansi2html`` program. Takes a command (and
    its arguments) and runs the program under ``script`` (emulating an
    interactive terminal), intercepts the output of the command and converts
    ANSI escape sequences in the output to HTML.
    """
    command = ['script', '-qe']
    command.extend(['-c', ' '.join(pipes.quote(a) for a in sys.argv[1:])])
    command.append('/dev/null')
    program = subprocess.Popen(command, stdout=subprocess.PIPE)
    stdout, stderr = program.communicate()
    html_output = convert(stdout)
    if sys.stdout.isatty():
        fd, filename = tempfile.mkstemp(suffix='.html')
        with open(filename, 'w') as handle:
            handle.write(html_output)
        webbrowser.open(filename)
    else:
        print(html_output)

def convert(text):
    """
    Convert text with ANSI escape sequences to HTML.

    :param text: The text with ANSI escape sequences (a string).
    :returns: The text converted to HTML (a string).
    """
    output = []
    for token in token_pattern.split(text):
        if token.startswith(('http://', 'https://', 'www.')):
            url = token
            if '://' not in token:
                url = 'http://' + url
            text = url.partition('://')[2]
            token = u'<a href="%s" style="color: inherit;">%s</a>' % (html_encode(url), html_encode(text))
        elif token.startswith('\x1b['):
            ansi_codes = token[2:-1].split(';')
            if ansi_codes == ['0']:
                token = '</span>'
            else:
                styles = []
                for code in ansi_codes:
                    if code == '1':
                        styles.append('font-weight: bold;')
                    elif code.startswith('3') and len(code) == 2:
                        styles.append('color: %s;' % EIGHT_COLOR_PALETTE[int(code[1])])
                if styles:
                    token = '<span style="%s">' % ' '.join(styles)
                else:
                    token = ''
        else:
            token = html_encode(token)
            token = encode_whitespace(token)
        output.append(token)
    return ''.join(output)

def encode_whitespace(text):
    """
    Encode whitespace in text as HTML so that all whitespace (specifically
    indentation and line breaks) is preserved when the text is rendered in a
    web browser.

    :param text: The plain text (a string).
    :returns: The text converted to HTML (a string).
    """
    text = text.replace('\r\n', '\n')
    text = text.replace('\n', '<br>\n')
    text = text.replace(' ', '&nbsp;')
    return text

def html_encode(text):
    """
    Encode special characters as HTML so that web browsers render the
    characters literally instead of messing up the rendering :-).

    :param text: The plain text (a string).
    :returns: The text converted to HTML (a string).
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text

# vim: ts=4 sw=4 et
