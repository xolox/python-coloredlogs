#!/bin/bash -ex

# An experiment inspired by https://github.com/travis-ci/travis-ci/issues/2312#issuecomment-195620855.

if [ "$TRAVIS_OS_NAME" = osx ]; then
  brew update
  brew install python
  virtualenv osx-env
  source osx-env/bin/activate
fi
