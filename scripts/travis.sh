#!/bin/bash -e

# Even though Travis CI supports Mac OS X [1] and several Python interpreters
# are installed out of the box, the Python environment cannot be configured in
# the Travis CI build configuration [2].
#
# As a workaround the build configuration file specifies a single Mac OS X job
# with `language: generic' that runs this script to create and activate a
# Python virtual environment.
#
# Recently the `virtualenv' command seems to no longer come pre-installed on
# the MacOS workers of Travis CI [3] so when this situation is detected we
# install it ourselves.
#
# [1] https://github.com/travis-ci/travis-ci/issues/216
# [2] https://github.com/travis-ci/travis-ci/issues/2312
# [3] https://travis-ci.org/xolox/python-humanfriendly/jobs/411396506

main () {
  if [ "$TRAVIS_OS_NAME" = osx ]; then
    local environment="$HOME/virtualenv/python2.7"
    if [ -x "$environment/bin/python" ]; then
      msg "Activating virtual environment ($environment) .."
      source "$environment/bin/activate"
    else
      if ! which virtualenv &>/dev/null; then
        msg "Installing 'virtualenv' in per-user site-packages .."
        pip install --user virtualenv
        msg "Figuring out 'bin' directory of per-user site-packages .."
        LOCAL_BINARIES=$(python -c 'import os, site; print(os.path.join(site.USER_BASE, "bin"))')
        msg "Prefixing '$LOCAL_BINARIES' to PATH .."
        export PATH="$LOCAL_BINARIES:$PATH"
      fi
      msg "Creating virtual environment ($environment) .."
      virtualenv "$environment"
      msg "Activating virtual environment ($environment) .."
      source "$environment/bin/activate"
      msg "Checking if 'pip' executable works .."
      if ! pip --version; then
        msg "Bootstrapping working 'pip' installation using get-pip.py .."
        curl -s https://bootstrap.pypa.io/get-pip.py | python -
      fi
    fi
  fi
  msg "Running command: $*"
  eval "$@"
}

msg () {
  echo "[travis.sh] $*" >&2
}

main "$@"
