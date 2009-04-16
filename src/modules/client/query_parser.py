#!/usr/bin/python2.4
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
# Copyright 2009 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.

import sys
import threading
import pkg.client.api_errors as api_errors
import pkg.manifest as manifest
import pkg.search_storage as ss
import pkg.search_errors as se
import pkg.fmri as fmri
from pkg.choose import choose

import pkg.query_parser as qp
from pkg.query_parser import BooleanQueryException, ParseError
import itertools

class QueryLexer(qp.QueryLexer):
        pass

class QueryParser(qp.QueryParser):
        def __init__(self, lexer):
                qp.QueryParser.__init__(self, lexer)
                mod = sys.modules[QueryParser.__module__]
                tmp = {}
                for class_name in self.query_objs.keys():
                        assert hasattr(mod, class_name)
                        tmp[class_name] = getattr(mod, class_name)
                self.query_objs = tmp


class Query(qp.Query):
        pass

class AndQuery(qp.AndQuery):
        pass

class OrQuery(qp.OrQuery):
        pass

class PkgConversion(qp.PkgConversion):
        pass
        
class PhraseQuery(qp.PhraseQuery):
        pass

class FieldQuery(qp.FieldQuery):
        pass

class TopQuery(qp.TopQuery):
        use_slow = False
        def search(self, *args):
                for i in qp.TopQuery.search(self, *args):
                        yield i
                if TopQuery.use_slow:
                        raise api_errors.SlowSearchUsed()

class TermQuery(qp.TermQuery):

        client_dict_lock = threading.Lock()

        qp.TermQuery._global_data_dict["fast_add"] = \
            ss.IndexStoreSet(ss.FAST_ADD)
        qp.TermQuery._global_data_dict["fast_remove"] = \
            ss.IndexStoreSet(ss.FAST_REMOVE)
        
        def __init__(self, term):
                qp.TermQuery.__init__(self, term)
                self._impl_fmri_to_path = None
                self._efn = None
                self._data_fast_remove = None
                self.full_fmri_hash = None
                self._data_fast_add = None

        def set_info(self, dir_path, fmri_to_manifest_path_func,
            expected_fmri_names_func, case_sensitive):
                self._efn = expected_fmri_names_func()
                TermQuery.client_dict_lock.acquire()
                try:
                        try:
                                qp.TermQuery._global_data_dict["fmri_hash"] = \
                                    ss.IndexStoreSetHash(ss.FULL_FMRI_HASH_FILE)
                                qp.TermQuery.set_info(self, dir_path,
                                    fmri_to_manifest_path_func, case_sensitive)
                                self._data_fast_add = \
                                    TermQuery._global_data_dict["fast_add"]
                                self._data_fast_remove = \
                                    TermQuery._global_data_dict["fast_remove"]
                                self.full_fmri_hash = \
                                    self._global_data_dict["fmri_hash"]
                                TopQuery.use_slow = False
                        except se.NoIndexException:
                                TopQuery.use_slow = True
                finally:
                        del qp.TermQuery._global_data_dict["fmri_hash"]
                        TermQuery.client_dict_lock.release()
                
        def search(self, restriction, fmris, manifest_func, excludes):
                if restriction:
                        return self._restricted_search_internal(restriction)
                elif not TopQuery.use_slow:
                        try:
                                self.full_fmri_hash.check_against_file(
                                    self._efn)
                        except se.IncorrectIndexFileHash:
                                raise \
                                    api_errors.IncorrectIndexFileHash()
                        base_res = \
                            self._search_internal(fmris)
                        client_res = \
                            self._search_fast_update(manifest_func,
                            excludes)
                        base_res = self._check_fast_remove(base_res)
                        it = itertools.chain(self._get_results(base_res),
                            self._get_fast_results(client_res))
                        return it
                else:
                        return self.slow_search(fmris, manifest_func, excludes)

        def _check_fast_remove(self, res):
                return (
                    (p_str, o, a, s, f)
                    for p_str, o, a, s, f
                    in res
                    if not self._data_fast_remove.has_entity(p_str)
                )

        def _search_fast_update(self, manifest_func, excludes):
                assert self._data_main_dict.get_file_handle() is not None

                glob = self._glob
                term = self._term
                case_sensitive = self._case_sensitive

                if not case_sensitive:
                        glob = True
                        
                fast_update_dict = {}

                fast_update_res = []

                for fmri_str in self._data_fast_add._set:
                        if not (self.pkg_name_wildcard or
                            self.pkg_name_match(fmri_str)):
                                continue
                        f = fmri.PkgFmri(fmri_str)
                        path = manifest_func(f)
                        search_dict = manifest.Manifest.search_dict(path,
                            return_line=True, excludes=excludes)
                        for tmp in search_dict:
                                tok, at, st, fv = tmp
                                if not (self.action_type_wildcard or
                                    at == self.action_type) or \
                                    not (self.key_wildcard or st == self.key):
                                        continue
                                if tok not in fast_update_dict:
                                        fast_update_dict[tok] = []
                                fast_update_dict[tok].append((at, st, fv,
                                    fmri_str, search_dict[tmp]))
                if glob:
                        keys = fast_update_dict.keys()
                        matches = choose(keys, term, case_sensitive)
                        fast_update_res = [
                            fast_update_dict[m] for m in matches
                        ]
                        
                else:
                        if term in fast_update_dict:
                                fast_update_res.append(fast_update_dict[term])
                return fast_update_res

        def _get_fast_results(self, fast_update_res):
                for sub_list in fast_update_res:
                        for at, st, fv, fmri_str, line_list in sub_list:
                                for l in line_list:
                                        yield at, st, fmri_str, fv, l

        def slow_search(self, fmris, manifest_func, excludes):
                if TermQuery.fmris is None:
                        TermQuery.fmris = list(fmris())
                it  = self._slow_search_internal(manifest_func, excludes)
                return it

        def _slow_search_internal(self, manifest_func, excludes):
                for pfmri in TermQuery.fmris:
                        fmri_str = pfmri.get_fmri(anarchy=True,
                            include_scheme=False)
                        if not (self.pkg_name_wildcard or
                            self.pkg_name_match(fmri_str)):
                                continue
                        manf = manifest_func(pfmri)
                        fast_update_dict = {}
                        fast_update_res = []
                        glob = self._glob
                        term = self._term
                        case_sensitive = self._case_sensitive

                        if not case_sensitive:
                                glob = True

                        search_dict = manifest.Manifest.search_dict(manf,
                            return_line=True, excludes=excludes)
                        for tmp in search_dict:
                                tok, at, st, fv = tmp
                                if not (self.action_type_wildcard or
                                    at == self.action_type) or \
                                    not (self.key_wildcard or st == self.key):
                                        continue
                                if tok not in fast_update_dict:
                                        fast_update_dict[tok] = []
                                fast_update_dict[tok].append((at, st, fv,
                                    fmri_str, search_dict[tmp]))
                        if glob:
                                keys = fast_update_dict.keys()
                                matches = choose(keys, term, case_sensitive)
                                fast_update_res = [
                                    fast_update_dict[m] for m in matches
                                ]
                        else:
                                if term in fast_update_dict:
                                        fast_update_res.append(
                                            fast_update_dict[term])
                        for sub_list in fast_update_res:
                                for at, st, fv, fmri_str, line_list in sub_list:
                                        for l in line_list:
                                                yield at, st, fmri_str, fv, l
