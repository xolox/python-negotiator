# Makefile for negotiator.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://github.com/xolox/negotiator

SHELL = bash
WORKON_HOME ?= $(HOME)/.virtualenvs
VIRTUAL_ENV ?= $(WORKON_HOME)/negotiator
ACTIVATE = . $(VIRTUAL_ENV)/bin/activate

default:
	@echo 'Makefile for negotiator'
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo '    make reset      recreate the virtual environment'
	@echo '    make publish    publish changes to GitHub/PyPI'
	@echo '    make clean      cleanup all temporary files'
	@echo

install:
	test -d "$(WORKON_HOME)" || mkdir -p "$(WORKON_HOME)"
	test -d "$(VIRTUAL_ENV)" || virtualenv "$(VIRTUAL_ENV)"
	test -x "$(VIRTUAL_ENV)/bin/pip" || ($(ACTIVATE) && easy_install pip)
	test -x "$(VIRTUAL_ENV)/bin/pip-accel" || ($(ACTIVATE) && pip install pip-accel)
	$(ACTIVATE) && pip uninstall -y negotiator-host || true
	$(ACTIVATE) && pip uninstall -y negotiator-guest || true
	$(ACTIVATE) && pip uninstall -y negotiator-common || true
	$(ACTIVATE) && pip-accel install --editable ./common ./host ./guest

reset:
	rm -Rf "$(VIRTUAL_ENV)"
	make --no-print-directory clean install

check:
	@test -x "$(VIRTUAL_ENV)/bin/pyflakes" || ($(ACTIVATE) && pip install pyflakes)
	@test -x "$(VIRTUAL_ENV)/bin/pep8" || ($(ACTIVATE) && pip install pep8)
	@test -x "$(VIRTUAL_ENV)/bin/pep257" || ($(ACTIVATE) && pip install pep257)
	$(ACTIVATE) && pyflakes .
	$(ACTIVATE) && pep8 --max-line-length=120 .
	$(ACTIVATE) && pep257 --ignore=D400 .

docs: install
	test -x "$(VIRTUAL_ENV)/bin/sphinx-build" || ($(ACTIVATE) && pip-accel install sphinx)
	$(ACTIVATE) && cd docs && sphinx-build -b html -d build/doctrees . build/html

publish:
	git push origin && git push --tags origin
	make clean
	for package in common host guest; do \
		cp README.rst $$package; \
		cd $(CURDIR)/$$package; \
		python setup.py sdist upload; \
		rm README.rst; \
	done

clean:
	rm -Rf {host,guest,common}/{build,dist}
	rm -Rf docs/{_{build,static,templates},build}
	find -type f -name '*.pyc' -delete

.PHONY: default install reset check publish clean
