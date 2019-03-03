# Makefile for negotiator.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: March 3, 2019
# URL: https://github.com/xolox/negotiator

PROJECT_NAME = negotiator
WORKON_HOME ?= $(HOME)/.virtualenvs
VIRTUAL_ENV ?= $(WORKON_HOME)/$(PROJECT_NAME)
PATH := $(VIRTUAL_ENV)/bin:$(PATH)
MAKE := $(MAKE) --no-print-directory
SHELL = bash

default:
	@echo "Makefile for $(PROJECT_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo '    make reset      recreate the virtual environment'
	@echo '    make check      check coding style (PEP-8, PEP-257)'
	@echo '    make readme     update usage in readme'
	@echo '    make docs       update documentation using Sphinx'
	@echo '    make publish    publish changes to GitHub/PyPI'
	@echo '    make clean      cleanup all temporary files'
	@echo

install:
	@test -d "$(VIRTUAL_ENV)" || mkdir -p "$(VIRTUAL_ENV)"
	@test -x "$(VIRTUAL_ENV)/bin/python" || virtualenv --quiet "$(VIRTUAL_ENV)"
	@test -x "$(VIRTUAL_ENV)/bin/pip" || easy_install pip
	@test -x "$(VIRTUAL_ENV)/bin/pip-accel" || pip install --quiet pip-accel
	@pip uninstall --yes negotiator-host &>/dev/null || true
	@pip uninstall --yes negotiator-guest &>/dev/null || true
	@pip uninstall --yes negotiator-common &>/dev/null || true
	@pip install --quiet --editable ./common
	@pip install --quiet --editable ./host
	@pip install --quiet --editable ./guest

reset:
	$(MAKE) clean
	rm -Rf "$(VIRTUAL_ENV)"
	$(MAKE) install

check: install
	@pip install -r requirements-checks.txt && flake8

readme: install
	@pip install --quiet cogapp && cog.py -r README.rst

docs: readme
	@pip install --quiet sphinx
	@cd docs && sphinx-build -nb html -d build/doctrees . build/html

publish: install
	git push origin && git push --tags origin
	$(MAKE) clean
	pip install --quiet twine wheel
	set -e; for package in common host guest; do \
		cp $(CURDIR)/README.rst $(CURDIR)/$$package; \
		cd $(CURDIR)/$$package; \
		python setup.py sdist bdist_wheel; \
		twine upload dist/*; \
		rm README.rst; \
	done

clean:
	rm -Rf {host,guest,common}/{build,dist}
	rm -Rf docs/{_{build,static,templates},build}
	find -type f -name '*.pyc' -delete

.PHONY: default install reset check readme docs publish clean
