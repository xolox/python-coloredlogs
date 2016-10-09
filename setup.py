#!/usr/bin/env python

"""Setup script for the `coloredlogs` package."""

# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 9, 2016
# URL: https://coloredlogs.readthedocs.org

# Standard library modules.
import codecs
import os
import re
import sys

# De-facto standard solution for Python packaging.
from setuptools import find_packages, setup

# Find the directory where the source distribution was unpacked.
source_directory = os.path.dirname(os.path.abspath(__file__))

# Find the current version.
module = os.path.join(source_directory, 'coloredlogs', '__init__.py')
for line in open(module, 'r'):
    match = re.match(r'^__version__\s*=\s*["\']([^"\']+)["\']$', line)
    if match:
        version_string = match.group(1)
        break
else:
    raise Exception("Failed to extract version from %s!" % module)

# Fill in the long description (for the benefit of PyPI)
# with the contents of README.rst (rendered by GitHub).
readme_file = os.path.join(source_directory, 'README.rst')
with codecs.open(readme_file, 'r', 'utf-8') as handle:
    readme_text = handle.read()

# External dependencies.
install_requires = [
    'humanfriendly >= 2.1',
]

# Conditional dependency (Windows only).
if sys.platform == 'win32':
    install_requires.append('colorama')

setup(name='coloredlogs',
      version=version_string,
      description="Colored terminal output for Python's logging module",
      long_description=readme_text,
      url='https://coloredlogs.readthedocs.org',
      author='Peter Odding',
      author_email='peter@peterodding.com',
      packages=find_packages(),
      entry_points=dict(console_scripts=[
          'coloredlogs = coloredlogs.cli:main',
      ]),
      install_requires=install_requires,
      test_suite='coloredlogs.tests',
      tests_require=[
          'capturer',
          'verboselogs',
      ],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Scientific/Engineering :: Human Machine Interfaces',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: User Interfaces',
          'Topic :: System',
          'Topic :: System :: Console Fonts',
          'Topic :: System :: Logging',
          'Topic :: System :: Systems Administration',
          'Topic :: Terminals',
      ])
