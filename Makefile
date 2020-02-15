# Makefile for the 'coloredlogs' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: February 15, 2020
# URL: https://coloredlogs.readthedocs.io

PACKAGE_NAME = coloredlogs
WORKON_HOME ?= $(HOME)/.virtualenvs
VIRTUAL_ENV ?= $(WORKON_HOME)/$(PACKAGE_NAME)
PYTHON ?= python3
PATH := $(VIRTUAL_ENV)/bin:$(PATH)
MAKE := $(MAKE) --no-print-directory
SHELL = bash

default:
	@echo "Makefile for $(PACKAGE_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install        install the package in a virtual environment'
	@echo '    make reset          recreate the virtual environment'
	@echo '    make check          check coding style (PEP-8, PEP-257)'
	@echo '    make test           run the test suite, report coverage'
	@echo '    make tox            run the tests on all Python versions'
	@echo '    make docs           update documentation using Sphinx'
	@echo '    make screenshots    generate screenshots of coloredlogs'
	@echo '    make publish        publish changes to GitHub/PyPI'
	@echo '    make clean          cleanup all temporary files'
	@echo

install:
	@test -d "$(VIRTUAL_ENV)" || mkdir -p "$(VIRTUAL_ENV)"
	@test -x "$(VIRTUAL_ENV)/bin/python" || virtualenv --python=$(PYTHON) --quiet "$(VIRTUAL_ENV)"
	@pip install --quiet --requirement=requirements.txt
	@pip uninstall --yes $(PACKAGE_NAME) &>/dev/null || true
	@pip install --quiet --no-deps --ignore-installed .

reset:
	@$(MAKE) clean
	@rm -Rf "$(VIRTUAL_ENV)"
	@$(MAKE) install

check: install
	@pip install --upgrade --quiet --requirement=requirements-checks.txt
	@flake8

test: install
	@pip install --quiet --requirement=requirements-tests.txt
	@py.test --cov --cov-report=html --no-cov-on-fail
	@coverage report --fail-under=90

tox: install
	@pip install --quiet tox
	@tox

docs: install
	@pip install --quiet sphinx
	@cd docs && sphinx-build -nb html -d build/doctrees . build/html

screenshots: install
	@pip install --quiet --requirement=requirements-screenshots.txt
	@python scripts/generate-screenshots.py

publish: install
	@git push origin && git push --tags origin
	@$(MAKE) clean
	@pip install --quiet twine wheel
	@python setup.py sdist bdist_wheel
	@twine upload dist/*
	@$(MAKE) clean

clean:
	@rm -Rf *.egg .cache .coverage .tox build dist docs/build htmlcov
	@find -depth -type d -name __pycache__ -exec rm -Rf {} \;
	@find -type f -name '*.pyc' -delete

.PHONY: default install reset check test tox docs screenshots publish clean
