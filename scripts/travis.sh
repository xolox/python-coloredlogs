#!/bin/bash -e

# Even though Travis CI supports Mac OS X [1] and several Python interpreters
# are installed out of the box, the Python environment cannot be configured in
# the Travis CI build configuration [2].
#
# As a workaround the build configuration file specifies a single Mac OS X job
# with `language: generic' that runs this script from the `before_install'
# section to create a Python virtual environment.
#
# [1] https://github.com/travis-ci/travis-ci/issues/216
# [2] https://github.com/travis-ci/travis-ci/issues/2312

# We define $VIRTUAL_ENV to match the default location on Travis CI.
export VIRTUAL_ENV=$HOME/virtualenv

# We are responsible for creating the environment on Mac OS X.
if [ "$TRAVIS_OS_NAME" = osx ]; then
  virtualenv "$VIRTUAL_ENV"
fi

# Activate the virtual environment before running the command.
source "$VIRTUAL_ENV/bin/activate"

# Execute the requested command inside the virtual environment.
exec "$@"
