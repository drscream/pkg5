#!/usr/bin/python
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
# Copyright 2008 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.
#

"""module describing a file packaging object

This module contains the FileAction class, which represents a file-type
packaging object."""

import os
import errno
import sha
from stat import *
import generic
import pkg.misc as misc
import pkg.portable as portable
try:
        import pkg.elf as elf
        haveelf = True
except ImportError:
        haveelf = False

class FileAction(generic.Action):
        """Class representing a file-type packaging object."""

        name = "file"
        attributes = ("mode", "owner", "group", "path")
        key_attr = "path"

        def __init__(self, data=None, **attrs):
                generic.Action.__init__(self, data, **attrs)
                self.hash = "NOHASH"

        def install(self, pkgplan, orig):
                """Client-side method that installs a file."""
                path = self.attrs["path"]
                mode = int(self.attrs["mode"], 8)
                owner = pkgplan.image.get_user_by_name(self.attrs["owner"])
                group = pkgplan.image.get_group_by_name(self.attrs["group"])

                final_path = os.path.normpath(os.path.sep.join(
                    (pkgplan.image.get_root(), path)))

                if not os.path.exists(os.path.dirname(final_path)):
                        self.makedirs(os.path.dirname(final_path), mode=0755)

                # If we're upgrading, extract the attributes from the old file.
                if orig:
                        omode = int(orig.attrs["mode"], 8)
                        oowner = pkgplan.image.get_user_by_name(
                            orig.attrs["owner"])
                        ogroup = pkgplan.image.get_group_by_name(
                            orig.attrs["group"])
                        ohash = orig.hash

                # If the action has been marked with a preserve attribute, and
                # the file exists and has a contents hash different from what
                # the system expected it to be, then we preserve the original
                # file in some way, depending on the value of preserve.
                #
                # XXX What happens when we transition from preserve to
                # non-preserve or vice versa? Do we want to treat a preserve
                # attribute as turning the action into a critical action?
                if "preserve" in self.attrs and os.path.isfile(final_path):
                        cfile = file(final_path)
                        chash = sha.sha(cfile.read()).hexdigest()

                        # XXX We should save the originally installed file.  It
                        # can be used as an ancestor for a three-way merge, for
                        # example.  Where should it be stored?
                        if not orig or chash != ohash:
                                pres_type = self.attrs["preserve"]
                                if pres_type == "renameold":
                                        old_path = final_path + ".old"
                                elif pres_type == "renamenew":
                                        final_path = final_path + ".new"
                                else:
                                        return

                # XXX This needs to be modularized.
                # XXX This needs to be controlled by policy.
                if self.needsdata(orig): 
                        temp = os.path.normpath(os.path.sep.join(
                            (pkgplan.image.get_root(), path + "." + self.hash)))

                        stream = self.data()
                        tfile = file(temp, "wb")
                        shasum = misc.gunzip_from_stream(stream, tfile)

                        tfile.close()
                        stream.close()

                        # Call cleanup callable, which deletes the underlying
                        # temporary file created above.
                        if self.cleanup != None:
                                self.cleanup()
                        # XXX Should throw an exception if shasum doesn't match
                        # self.hash
                else:
                        temp = final_path

                os.chmod(temp, mode)

                try:
                        portable.chown(temp, owner, group)
                except OSError, e:
                        if e.errno != errno.EPERM:
                                raise

                # XXX There's a window where final_path doesn't exist, but we
                # probably don't care.
                if "old_path" in locals():
                        portable.rename(final_path, old_path)

                # This is safe even if temp == final_path.
                portable.rename(temp, final_path)

		# XXX .pyc files are causing problems because they're not enough
		# newer than the .py files.... if we just installed a .pyc
		# file, move its modification time into the future to prevent
		# python commands running as root from updating these files
		# because they look out of date... the right fix is to fix
		# Solaris python to look at the entire timestamp.... pending.
		# in the mean time, this "accomodation" has to be made to
		# prevent pkg verify errors.
		if final_path.endswith(".pyc"):
			t = os.stat(final_path)[ST_MTIME] + 5 # magic
			os.utime(final_path, (t, t))

        def verify(self, img, **args):
                """ verify that file is present and if preserve attribute
                not present, that hashes match"""
                path = self.attrs["path"]
                mode = int(self.attrs["mode"], 8)
                owner = img.get_user_by_name(self.attrs["owner"])
                group = img.get_group_by_name(self.attrs["group"])

                path = os.path.normpath(os.path.sep.join(
                    (img.get_root(), path)))

                try:
                        stat = os.lstat(path)
                except OSError, e:
                        if e.errno == errno.ENOENT:
                                return ["File does not exist"]
                        if e.errno == errno.EACCES:
                                return ["Skipping: Permission denied"]
                        return ["Unexpected OSError: %s" % e]

                errors = []

                if path.lower().endswith("/cat") and args["verbose"] == True:
                        errors.append("Warning: package may contain bobcat!  "
                            "(http://xkcd.com/325/)")

                if not S_ISREG(stat[ST_MODE]):
                        errors.append("%s is not a regular file" % self.attrs["path"])
                if stat[ST_UID] != owner:
                        errors.append("Owner: '%s' should be '%s'" % \
                            (img.get_name_by_uid(stat[ST_UID], True),
                             img.get_name_by_uid(owner, True)))
                if stat[ST_GID] != group:
                        errors.append("Group: '%s' should be '%s'" % \
                            (img.get_name_by_gid(stat[ST_GID], True),
                             img.get_name_by_gid(group, True)))
                if S_IMODE(stat[ST_MODE]) != mode:
                        errors.append("Mode: 0%.3o should be 0%.3o" % \
                            (S_IMODE(stat[ST_MODE]), mode))

                # avoid checking pkg.size if elfhash present;
                # different size files may have the same elfhash
                if "preserve" not in self.attrs and \
                    "pkg.size" in self.attrs and    \
                    "elfhash" not in self.attrs and \
                    stat[ST_SIZE] != int(self.attrs["pkg.size"]):
                        errors.append("Size: %d bytes should be %d" % \
                            (stat[ST_SIZE], int(self.attrs["pkg.size"])))

                if "preserve" not in self.attrs and args["forever"] == True:
                        try:
                                if "elfhash" in self.attrs:
                                        if haveelf:
                                                elfhash = elf.get_dynamic(path)["hash"]
                                                if elfhash != self.attrs["elfhash"]:
                                                        errors.append("Elfhash: %s should be %s" % \
                                                            (elfhash, self.attrs["elfhash"]))
                                        else:
                                                errors.append("Elfhash: unable to verify due to missing elf module")

                                # not an elf file -> try normal hash
                                else:
                                        f = file(path)
                                        data = f.read()
                                        f.close()
                                        hashvalue = sha.new(data).hexdigest()
                                        if hashvalue != self.hash:
                                                errors.append("Hash: %s should be %s" % \
                                                    (hashvalue, self.hash))
                        except (OSError, IOError), e:
                                if e.errno == errno.EACCES:
                                        errors.append("Skipping: Permission Denied" % e)
                                else:
                                        errors.append("Unexpected Error %s" % e)
                        except Exception, e:
                                errors.append("Unexpected Exception: %s" % e)
                return errors

        # If we're not upgrading, or the file contents have changed,
        # retrieve the file and write it to a temporary location.
        # For ELF files, only write the new file if the elfhash changed.
        def needsdata(self, orig):
                bothelf = orig and "elfhash" in orig.attrs and "elfhash" in self.attrs
                if not orig or \
                    (bothelf and orig.attrs["elfhash"] !=
                        self.attrs["elfhash"]) or \
                    (not bothelf and orig.hash != self.hash):
                        return True

                return False
                

        def remove(self, pkgplan):
                path = os.path.normpath(os.path.sep.join(
                    (pkgplan.image.get_root(), self.attrs["path"])))

                try:
                        # Make file writable so it can be deleted
                        os.chmod(path, S_IWRITE|S_IREAD)
                        os.unlink(path)
                except OSError,e:
                        if e.errno != errno.ENOENT:
                                raise


        def different(self, other):
                # Override the generic different() method to ignore the file
                # hash for ELF files and compare the ELF hash instead.
                # XXX This should be modularized and controlled by policy.

                # One of these isn't an ELF file, so call the generic method
                if "elfhash" not in self.attrs or "elfhash" not in other.attrs:
                        return generic.Action.different(self, other)

                sset = set(self.attrs.keys())
                oset = set(other.attrs.keys())
                if sset.symmetric_difference(oset):
                        return True

                for a in self.attrs:
                        if self.attrs[a] != other.attrs[a]:
                                return True

                return False

        def generate_indices(self):
                return {
                    "content": self.hash,
                    "basename": os.path.basename(self.attrs["path"]),
                    "path": os.path.sep + self.attrs["path"]
                }
