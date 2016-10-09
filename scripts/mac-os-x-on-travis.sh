#!/bin/bash -x

# An experiment inspired by https://github.com/travis-ci/travis-ci/issues/2312#issuecomment-195620855.

find_program () {
  local matches="$(which -a "$1")"
  echo "Matches for '$1' program on PATH:"
  if [ -z "$matches" ]; then
    echo " - (none)"
  else
    echo "$matches" | while read PATHNAME; do
      if [ -x "$PATHNAME" ]; then
        VERSION=$("$PATHNAME" --version 2>&1)
        echo " - $VERSION ($PATHNAME)"
      fi
    done
  fi
}

if [ "$TRAVIS_OS_NAME" = osx ]; then

  # Show the installed Python interpreters.
  for program in python{,{2{,.6,.7},3{,.4,.5}}}; do
    find_program "$program"
  done

  # Show the installed `virtualenv' version.
  find_program virtualenv

  # I'm getting the distinct impression that I don't even need Homebrew
  # to install Python 2.7 on Mac OS X because it's already available?!
  if ! which python2.7 &>/dev/null; then
    brew update
    brew install python
  fi

  # But do I still need this as an alternative to the Travis CI Python runtime support?
  virtualenv osx-env
  source osx-env/bin/activate

  # Show the Python version inside the virtual environment.
  find_program "python"

fi
