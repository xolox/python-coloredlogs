#!/usr/bin/env python

# Setup script for the `coloredlogs' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: February 16, 2020
# URL: https://coloredlogs.readthedocs.io

"""
Setup script for the `coloredlogs` package.

**python setup.py install**
  Install from the working directory into the current Python environment.

**python setup.py sdist**
  Build a source distribution archive.

**python setup.py bdist_wheel**
  Build a wheel distribution archive.
"""

# Standard library modules.
import codecs
import distutils.sysconfig
import os
import re
import sys

# De-facto standard solution for Python packaging.
from setuptools import find_packages, setup


def get_contents(*args):
    """Get the contents of a file relative to the source distribution directory."""
    with codecs.open(get_absolute_path(*args), 'r', 'UTF-8') as handle:
        return handle.read()


def get_version(*args):
    """Extract the version number from a Python module."""
    contents = get_contents(*args)
    metadata = dict(re.findall('__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']


def get_requirements(*args):
    """Get requirements from pip requirement files."""
    requirements = set()
    with open(get_absolute_path(*args)) as handle:
        for line in handle:
            # Strip comments.
            line = re.sub(r'^#.*|\s#.*', '', line)
            # Ignore empty lines
            if line and not line.isspace():
                requirements.add(re.sub(r'\s+', '', line))
    return sorted(requirements)


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


def find_pth_directory():
    """
    Determine the correct directory pathname for installing ``*.pth`` files.

    To install a ``*.pth`` file using a source distribution archive (created
    when ``python setup.py sdist`` is called) the relative directory pathname
    ``lib/pythonX.Y/site-packages`` needs to be passed to the ``data_files``
    option to ``setup()``.

    Unfortunately this breaks universal wheel archives (created when ``python
    setup.py bdist_wheel --universal`` is called) because a specific Python
    version is now encoded in the pathname of a directory that becomes part of
    the supposedly universal archive :-).

    Through trial and error I've found that by passing the directory pathname
    ``/`` when ``python setup.py bdist_wheel`` is called we can ensure that
    ``*.pth`` files are installed in the ``lib/pythonX.Y/site-packages``
    directory without hard coding its location.
    """
    return ('/' if 'bdist_wheel' in sys.argv
            else os.path.relpath(distutils.sysconfig.get_python_lib(), sys.prefix))


setup(name='coloredlogs',
      version=get_version('coloredlogs', '__init__.py'),
      description="Colored terminal output for Python's logging module",
      long_description=get_contents('README.rst'),
      url='https://coloredlogs.readthedocs.io',
      author="Peter Odding",
      author_email='peter@peterodding.com',
      license='MIT',
      packages=find_packages(),
      data_files=[
          (find_pth_directory(), ['coloredlogs.pth']),
      ],
      entry_points=dict(console_scripts=[
          'coloredlogs = coloredlogs.cli:main',
      ]),
      test_suite='coloredlogs.tests',
      install_requires=get_requirements('requirements.txt'),
      extras_require=dict(cron='capturer>=2.4'),
      tests_require=get_requirements('requirements-tests.txt'),
      python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Communications',
          'Topic :: Scientific/Engineering :: Human Machine Interfaces',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: User Interfaces',
          'Topic :: System',
          'Topic :: System :: Shells',
          'Topic :: System :: System Shells',
          'Topic :: System :: Console Fonts',
          'Topic :: System :: Logging',
          'Topic :: System :: Systems Administration',
          'Topic :: Terminals',
          'Topic :: Utilities',
      ])
