#!/bin/bash -e

# Even though Travis CI supports Mac OS X [1] and several Python interpreters
# are installed out of the box, the Python environment cannot be configured in
# the Travis CI build configuration [2].
#
# As a workaround the build configuration file specifies a single Mac OS X job
# with `language: generic' that runs this script from the `before_install'
# section to create and activate a Python virtual environment.
#
# [1] https://github.com/travis-ci/travis-ci/issues/216
# [2] https://github.com/travis-ci/travis-ci/issues/2312

if [ "$TRAVIS_OS_NAME" = osx ]; then
  VIRTUAL_ENV="$HOME/virtualenv/python2.7"
  if [ ! -x "$VIRTUAL_ENV/bin/python" ]; then
    virtualenv "$VIRTUAL_ENV"
  fi
  source "$VIRTUAL_ENV/bin/activate"
fi

eval "$@"
