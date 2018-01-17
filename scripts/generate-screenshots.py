#!/usr/bin/env python

"""
Generate screenshots of `coloredlogs` in a terminal emulator.

When the `coloredlogs` documentation was originally written, the screenshots
were created manually, which had the following consequences:

- Screen shots were never updated, even after making code changes that affected
  the appearance, because recreating the screen shots was too much work.

- There was no consistency between screen shots because each screen shot
  reflected my personal preference at the point in time where the screen
  shot was taken.

Because of these points I decided to create a Python script that would
orchestrate reproducible creation of screen shots. It's far from perfect, but
it's a whole lot better than no automation at all :-).

Why this script uses the ``urxvt`` terminal emulator:

1. My terminal emulator of choice is ``gnome-terminal``, but its command line
   options are rather limited.

2. Knowing that ``xterm`` has quite a lot of command line options I tried it
   instead of ``gnome-terminal``. While it worked fine I didn't like how xterm
   renders the 'Monaco' font (my favorite monospace font) so I looked for a
   terminal emulator that allows to change letter spacing.

3. The search for a terminal emulator that allows to customize letter spacing
   brought me to ``urxvt``, however when I actually tried it out it became
   apparent that the default letter spacing chosen by ``urxvt`` matches
   ``gnome-terminal`` which meant the default letter spacing was fine :-).
"""

# Standard library modules.
import glob
import os
import subprocess
import sys
import time

# External dependencies.
import coloredlogs
from capturer import CaptureOutput
from coloredlogs.converter import EIGHT_COLOR_PALETTE
from executor import execute, quote, which
from humanfriendly import compact, format_path
from humanfriendly.terminal import ansi_strip, ansi_wrap
from humanfriendly.testing import random_string
from verboselogs import VerboseLogger

# Configuration defaults.
FONT_NAME = 'Monaco'
"""The name of the font used in screen shots."""

FONT_SIZE = 14
"""The pixel size of the font used in screen shots."""

TEXT_COLOR = 'white'
"""The default text color used in screen shots."""

BACKGROUND_COLOR = 'black'
"""The default background color used in screen shots."""

# Initialize a logger for this program.
logger = VerboseLogger('screenshot-generator')


def main():
    """Command line interface."""
    coloredlogs.install(level='debug')
    arguments = sys.argv[1:]
    if arguments:
        interpret_script(arguments[0])
    else:
        logger.notice(compact("""
            This script requires the 'urxvt' terminal emulator and the
            ImageMagick command line programs 'convert' and 'import' to be
            installed. Don't switch windows while the screenshots are being
            generated because it seems that 'import' can only take screenshots
            of foreground windows.
        """))
        generate_screenshots()


def generate_screenshots():
    """Generate screenshots from shell scripts."""
    this_script = os.path.abspath(__file__)
    this_directory = os.path.dirname(this_script)
    repository = os.path.join(this_directory, os.pardir)
    examples_directory = os.path.join(repository, 'docs', 'examples')
    images_directory = os.path.join(repository, 'docs', 'images')
    for shell_script in sorted(glob.glob(os.path.join(examples_directory, '*.sh'))):
        basename, extension = os.path.splitext(os.path.basename(shell_script))
        image_file = os.path.join(images_directory, '%s.png' % basename)
        logger.info("Generating %s by running %s ..",
                    format_path(image_file),
                    format_path(shell_script))
        command_line = [sys.executable, __file__, shell_script]
        random_title = random_string(25)
        # Generate the urxvt command line.
        urxvt_command = [
            'urxvt',
            # Enforce a default geometry.
            '-geometry', '98x30',
            # Set the text and background color.
            '-fg', TEXT_COLOR,
            '-bg', BACKGROUND_COLOR,
            # Set the font name and pixel size.
            '-fn', 'xft:%s:pixelsize=%i' % (FONT_NAME, FONT_SIZE),
            # Set the window title.
            '-title', random_title,
            # Hide scrollbars.
            '+sb',
        ]
        if which('qtile-run'):
            # I've been using tiling window managers for years now, at the
            # moment 'qtile' is my window manager of choice. It requires the
            # following special handling to enable the 'urxvt' window to float,
            # which in turn enables it to respect the '--geometry' option.
            urxvt_command.insert(0, 'qtile-run')
            urxvt_command.insert(1, '-f')
        # Apply the Ubuntu color scheme to urxvt.
        for index, css_color in enumerate(EIGHT_COLOR_PALETTE):
            urxvt_command.extend(('--color%i' % index, css_color))
        # Add the command that should run inside the terminal.
        urxvt_command.extend(('-e', 'sh', '-c', 'setterm -cursor off; %s' % quote(command_line)))
        # Launch urxvt.
        execute(*urxvt_command, async=True)
        # Make sure we close the urxvt window.
        try:
            # Wait for urxvt to start up. If I were to improve this I could
            # instead wait for the creation of a file by interpret_script().
            time.sleep(10)
            # Take a screen shot of the window using ImageMagick.
            execute('import', '-window', random_title, image_file)
            # Auto-trim the screen shot, then give it a 5px border.
            execute('convert', image_file, '-trim',
                    '-bordercolor', BACKGROUND_COLOR,
                    '-border', '5', image_file)
        finally:
            execute('wmctrl', '-c', random_title)


def interpret_script(shell_script):
    """Make it appear as if commands are typed into the terminal."""
    with CaptureOutput() as capturer:
        shell = subprocess.Popen(['bash', '-'], stdin=subprocess.PIPE)
        with open(shell_script) as handle:
            for line in handle:
                sys.stdout.write(ansi_wrap('$', color='green') + ' ' + line)
                sys.stdout.flush()
                shell.stdin.write(line)
                shell.stdin.flush()
            shell.stdin.close()
        time.sleep(12)
        # Get the text that was shown in the terminal.
        captured_output = capturer.get_text()
    # Store the text that was shown in the terminal.
    filename, extension = os.path.splitext(shell_script)
    transcript_file = '%s.txt' % filename
    logger.info("Updating %s ..", format_path(transcript_file))
    with open(transcript_file, 'w') as handle:
        handle.write(ansi_strip(captured_output))


if __name__ == '__main__':
    main()
