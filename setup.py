#!/usr/bin/env python

# Setup script for the `coloredlogs' package.

# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 1, 2016
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


def get_install_requires():
    """Add conditional dependencies for Windows (when creating source distributions)."""
    install_requires = get_requirements('requirements.txt')
    if 'bdist_wheel' not in sys.argv:
        if sys.platform == 'win32':
            install_requires.extend('colorama')
    return sorted(install_requires)


def get_extras_require():
    """Add conditional dependencies for Windows (when creating wheel distributions)."""
    extras_require = {}
    if have_environment_marker_support():
        expression = ':sys_platform == "win32"'
        extras_require[expression] = 'colorama'
    return extras_require


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


def have_environment_marker_support():
    """
    Check whether setuptools has support for PEP-426 environment marker support.

    Based on the ``setup.py`` script of the ``pytest`` package:
    https://bitbucket.org/pytest-dev/pytest/src/default/setup.py
    """
    try:
        from pkg_resources import parse_version
        from setuptools import __version__
        return parse_version(__version__) >= parse_version('0.7.2')
    except Exception:
        return False


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
      packages=find_packages(),
      data_files=[
          (find_pth_directory(), ['coloredlogs.pth']),
      ],
      entry_points=dict(console_scripts=[
          'coloredlogs = coloredlogs.cli:main',
      ]),
      test_suite='coloredlogs.tests',
      install_requires=get_install_requires(),
      extras_require=get_extras_require(),
      tests_require=get_requirements('requirements-tests.txt'),
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
