#!/usr/bin/env make -f
PYTHON=/usr/bin/env python
PIP=/usr/bin/env pip
DJANGO_ADMIN=/usr/bin/env django-admin

.PHONY: all clean sdist upload install-dev install

all: sdist

clean:
	rm -fr dist *.egg-info build
	find . \( -name "*.py[co]" -o -name "*.mo" -o -name "*~" \) -type f -delete

sdist: clean
	$(PIP) install wheel
	$(PYTHON) setup.py sdist bdist_wheel

upload: clean
	$(PYTHON) setup.py sdist upload

install-dev:
	$(PIP) install -e .

install:
	$(PYTHON) setup.py install
