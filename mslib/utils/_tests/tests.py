# -*- coding: utf-8 -*-
"""

    mslib._tests.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mss_util

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import logging
import multidict
import werkzeug

LOGGER = logging.getLogger(__name__)


class TestCIMultiDict(object):

    class CaseInsensitiveMultiDict(werkzeug.datastructures.ImmutableMultiDict):
        """Extension to werkzeug.datastructures.ImmutableMultiDict
        that makes the MultiDict case-insensitive.

        The only overridden method is __getitem__(), which converts string keys
        to lower case before carrying out comparisons.

        See ../paste/util/multidict.py as well as
          http://stackoverflow.com/questions/2082152/case-insensitive-dictionary
        """

        def __getitem__(self, key):
            if hasattr(key, 'lower'):
                key = key.lower()
            for k, v in self.items():
                if hasattr(k, 'lower'):
                    k = k.lower()
                if k == key:
                    return v
            raise KeyError(repr(key))

    def test_multidict(object):
        dict = TestCIMultiDict.CaseInsensitiveMultiDict([('title', 'MSS')])
        dict_multidict = multidict.CIMultiDict([('title', 'MSS')])
        assert 'title' in dict_multidict
        assert 'tiTLE' in dict_multidict
        assert dict_multidict['Title'] == dict['tITLE']
