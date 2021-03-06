#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

#
# Copyright (c) 2007, 2016, Oracle and/or its affiliates. All rights reserved.
# Copyright 2016, OmniTI Computer Consulting, Inc. All rights reserved.
# Copyright 2018 OmniOS Community Edition (OmniOSce) Association.
#

PYTHON27 = /usr/bin/python2.7
PYTHON35 = /usr/bin/python3.5

# Should match python version above.
PYLINT_FMRI = pkg:/library/python-2/pylint-27

CODE_WS = $$(hg root 2>/dev/null || git rev-parse --show-toplevel)

CC=/opt/gcc-4.4.4/bin/gcc

all := TARGET = all
install := TARGET = install
packages := TARGET = install
clean := TARGET = clean
clobber := TARGET = clobber
lint := TARGET = lint
clint := TARGET = clint
pylint := TARGET = pylint
pep8 := TARGET = pep8
test := TARGET = test
test-verbose := TARGET = test-verbose
test-generate := TARGET = test-generate

#
# clear PYTHONPATH when invoking /usr/bin/pkg (we don't want to load any
# pkg python modules from this workspace since they may be out of sync
# with the pkg modules in the root filesystem).
#
PYLINT_VER_CMD = PYTHONPATH= /usr/bin/pkg info $(PYLINT_FMRI) | \
		 /usr/bin/grep Version | /usr/bin/awk -F: '{print $$2}' | \
		 /usr/bin/sed -e 's/ //g'

PEP8 = /usr/bin/pep8
JOBS = 8

SUBDIRS=brand zoneproxy tsol util/mkcert

all: $(SUBDIRS)
	mkdir -p $(CODE_WS)/proto/build_i386/lib.solaris-2.11-i86pc-2.6/pkg/64
	mkdir -p $(CODE_WS)/proto/build_i386/lib.solaris-2.11-i86pc-2.6/pkg/actions/64
	ISALIST=i386 $(PYTHON27) setup.py build

clean: $(SUBDIRS)
	$(PYTHON27) setup.py clean
	@cd pkg; pwd; make clean

clobber: $(SUBDIRS)
	$(PYTHON27) setup.py clobber
	@cd pkg; pwd; make clobber

#
# run pylint as part of the install target.
# it's the best way to ensure things stay pylint clean.
#
install: $(SUBDIRS)
	ISALIST=i386 CC=$(CC) $(PYTHON27) setup.py install
	CC=$(CC) $(PYTHON35) setup.py install

lint:
	CC=$(CC) $(PYTHON27) setup.py lint
	@cd zoneproxy; pwd; make lint

clint:
	CC=$(CC) $(PYTHON27) setup.py clint
	@cd zoneproxy; pwd; make lint

pylint: install
	PYLINT_VER=$(PYLINT_VER_CMD:sh) $(PYTHON27) setup.py pylint
	PYLINT_VER=$(PYLINT_VER_CMD:sh) $(PYTHON27) setup.py pylint_py3k

pep8:
	$(PEP8) --statistics --count `cat tests/pep8-whitelist.txt`

#
# This rule propagates the current make target through all of the
# subdirectories in $SUBDIRS.
#
$(SUBDIRS): FRC
	@cd $@; pwd; $(MAKE) $(TARGET) CC=$(CC)

# Use the bits we just built to create the packages. - #XXX pep8
packages: install
	@cd pkg; pwd; $(MAKE) $(TARGET) check \
		PATH=$(CODE_WS)/proto/root_$$(uname -p)/usr/bin:$$PATH \
		CC=$(CC)

test: install
	-pfexec $(PYTHON27) tests/run.py -j ${JOBS}
	-pfexec $(PYTHON35) tests/run.py -j ${JOBS}

FRC:
