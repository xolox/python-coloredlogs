#!/usr/bin/env python

import sys
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

# Find the directory where the source distribution was unpacked.
source_directory = dirname(abspath(__file__))

# Add the source distribution directory to the module path.
sys.path.append(source_directory)

# Find the version number embedded in coloredlogs/__init__.py.
from coloredlogs import __version__

# Fill in the long description (for the benefit of PyPi)
# with the contents of README.rst (rendered by GitHub).
readme_file = join(source_directory, 'README.rst')
readme_text = open(readme_file, 'r').read()

setup(name='coloredlogs',
      version=__version__,
      description='Colored stream handler for the logging module',
      long_description=readme_text,
      url='https://github.com/xolox/python-coloredlogs',
      author='Peter Odding',
      author_email='peter@peterodding.com',
      packages=find_packages(),
      entry_points={'console_scripts': ['ansi2html = coloredlogs.converter:main']})
