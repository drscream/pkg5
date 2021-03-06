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
# Copyright (c) 2007, 2010, Oracle and/or its affiliates. All rights reserved.
# Copyright (c) 2012, OmniTI Computer Consulting, Inc. All rights reserved.
# Copyright 2018 OmniOS Community Edition (OmniOSce) Association.
#

MACH:sh = uname -p

INSTALL = /usr/sbin/install

ROOT = ../../proto/root_${MACH}
ROOTETC = $(ROOT)/etc
ROOTETCZONES = $(ROOT)/etc/zones
ROOTETCBRAND = $(ROOT)/etc/brand/ipkg
ROOTUSRLIB = $(ROOT)/usr/lib
ROOTBRAND = $(ROOTUSRLIB)/brand
ROOTBRANDPKG = $(ROOTBRAND)/ipkg
LINKBRANDPKG = $(ROOTBRAND)/lipkg
SPARSEBRANDPKG = $(ROOTBRAND)/sparse
BHYVEBRANDPKG = $(ROOTBRAND)/bhyve
KVMBRANDPKG = $(ROOTBRAND)/kvm

ROOTDIRS = \
	$(ROOT) \
	$(ROOTETC) \
	$(ROOTETCBRAND) \
	$(ROOTETCZONES) \
	$(ROOTUSRLIB) \
	$(ROOTBRAND) \
	$(ROOTBRANDPKG) \
	$(LINKBRANDPKG) \
	$(SPARSEBRANDPKG) \
	$(BHYVEBRANDPKG) \
	$(KVMBRANDPKG)

ROOTFILES = \
	$(ROOTETCBRAND)/pkgrm.conf \
	$(ROOTETCBRAND)/smf_disable.conf \
	$(ROOTETCZONES)/OMNIlipkg.xml \
	$(ROOTETCZONES)/SUNWipkg.xml \
	\
	$(ROOTBRANDPKG)/attach \
	$(ROOTBRANDPKG)/clone \
	$(ROOTBRANDPKG)/common.ksh \
	$(ROOTBRANDPKG)/detach \
	$(ROOTBRANDPKG)/fmri_compare \
	$(ROOTBRANDPKG)/image_install \
	$(ROOTBRANDPKG)/p2v \
	$(ROOTBRANDPKG)/pkgcreatezone \
	$(ROOTBRANDPKG)/pkgrm.lst \
	$(ROOTBRANDPKG)/poststate \
	$(ROOTBRANDPKG)/prestate \
	$(ROOTBRANDPKG)/smf_disable.lst \
	$(ROOTBRANDPKG)/support \
	$(ROOTBRANDPKG)/system-unconfigure \
	$(ROOTBRANDPKG)/uninstall \
	\
	$(SPARSEBRANDPKG)/attach \
	$(SPARSEBRANDPKG)/clone \
	$(SPARSEBRANDPKG)/common.ksh \
	$(SPARSEBRANDPKG)/config.xml \
	$(SPARSEBRANDPKG)/detach \
	$(SPARSEBRANDPKG)/pkgcreatezone \
	$(SPARSEBRANDPKG)/platform.xml \
	$(SPARSEBRANDPKG)/poststate \
	$(SPARSEBRANDPKG)/prestate \
	$(SPARSEBRANDPKG)/profile.xml \
	$(SPARSEBRANDPKG)/uninstall \
	$(SPARSEBRANDPKG)/verifyadm \
	\
	$(BHYVEBRANDPKG)/config.xml \
	$(BHYVEBRANDPKG)/platform.xml \
	$(BHYVEBRANDPKG)/init \
	$(BHYVEBRANDPKG)/createzone \
	$(BHYVEBRANDPKG)/socat \
	$(BHYVEBRANDPKG)/support \
	\
	$(KVMBRANDPKG)/config.xml \
	$(KVMBRANDPKG)/platform.xml \
	$(KVMBRANDPKG)/init \
	$(KVMBRANDPKG)/support

BIN = \
	support \
	fmri_compare

support := LDLIBS = -L/lib -lzonecfg

all := TARGET = all

support: support.c
	$(LINK.c) -o $@ $@.c $(LDLIBS)

fmri_compare: fmri_compare.py
	cp $@.py $@
	chmod 755 $@

all: fmri_compare

clean:
	rm -f $(BIN)

clobber: clean
	rm -f $(ROOTFILES)
	rm -fr $(ROOTBRAND)

install: $(ROOTFILES)


$(ROOT) $(ROOTETC) $(ROOTETCBRAND) $(ROOTETCZONES) $(ROOTUSRLIB) \
	$(ROOTBRAND) $(ROOTBRANDPKG) $(LINKBRANDPKG) \
	$(SPARSEBRANDPKG) $(BHYVEBRANDPKG) $(KVMBRANDPKG):
	mkdir -p $@

$(ROOTETCBRAND)/%: $(ROOTETCBRAND) %
	rm -f $@; $(INSTALL) -f $(ROOTETCBRAND) -m 0644 $<

$(ROOTETCZONES)/%: $(ROOTETCZONES) %
	rm -f $@; $(INSTALL) -f $(ROOTETCZONES) -m 0444 $<

$(ROOTBRANDPKG)/%: $(ROOTBRANDPKG) %
	rm -f $@; $(INSTALL) -f $(ROOTBRANDPKG) -m 0444 $<

$(SPARSEBRANDPKG)/%: $(SPARSEBRANDPKG) sparse/%
	rm -f $@; $(INSTALL) -f $(SPARSEBRANDPKG) -m 0444 $<

$(BHYVEBRANDPKG)/%: $(BHYVEBRANDPKG) bhyve/%
	rm -f $@; $(INSTALL) -f $(BHYVEBRANDPKG) -m 0444 $<

$(KVMBRANDPKG)/%: $(KVMBRANDPKG) kvm/%
	rm -f $@; $(INSTALL) -f $(KVMBRANDPKG) -m 0444 $<

