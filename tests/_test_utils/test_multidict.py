# -*- coding: utf-8 -*-
"""
    tests._test_utils.test_multidict
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mss_util

    This file is part of MSS.

    :copyright: Copyright 2016 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.
"""
import logging
import multidict
import werkzeug
import pytest

LOGGER = logging.getLogger(__name__)


class TestCIMultiDict:

    class CaseInsensitiveMultiDict(werkzeug.datastructures.ImmutableMultiDict):
        """Extension to werkzeug.datastructures.ImmutableMultiDict
        that makes the MultiDict case-insensitive.

        The only overridden method is __getitem__(), which converts string keys
        to lower case before carrying out comparisons.
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

    def test_multidict_basic_case_insensitivity(self):
        """Basic behavior: keys should be looked up case-insensitively."""
        test_dict = TestCIMultiDict.CaseInsensitiveMultiDict([('title', 'MSS')])
        dict_multidict = multidict.CIMultiDict([('title', 'MSS')])

        # membership checks should be case-insensitive
        assert 'title' in dict_multidict
        assert 'tiTLE' in dict_multidict

        # direct indexing should honor case-insensitive lookup
        assert dict_multidict['Title'] == test_dict['tITLE']

    def test_multidict_missing_key_raises_keyerror(self):
        """Accessing a missing key should raise KeyError for both implementations."""
        dict_multidict = multidict.CIMultiDict([('a', '1')])
        test_dict = TestCIMultiDict.CaseInsensitiveMultiDict([('a', '1')])

        with pytest.raises(KeyError):
            _ = dict_multidict['missing_key']  # multidict raises KeyError

        with pytest.raises(KeyError):
            _ = test_dict['another_missing']

    def test_multidict_non_string_keys(self):
        """Non-string keys (e.g., ints) should still work and not be lowered."""
        dict_multidict = multidict.CIMultiDict([(1, 'one'), ('Two', '2')])
        test_dict = TestCIMultiDict.CaseInsensitiveMultiDict([(1, 'one'), ('Two', '2')])

        # integer key should be retrievable as-is
        assert dict_multidict[1] == 'one'
        assert test_dict[1] == 'one'

        # string key should still be case-insensitive
        assert dict_multidict['two'] == '2'
        assert test_dict['tWo'] == '2'

    def test_multidict_contains_and_iteration(self):
        """Ensure 'in' checks and .items() iteration behave sensibly."""
        dict_multidict = multidict.CIMultiDict([('X-Header', 'val'), ('Content', 'c')])
        test_dict = TestCIMultiDict.CaseInsensitiveMultiDict([('X-Header', 'val'), ('Content', 'c')])

        # membership by different case
        assert 'x-header' in dict_multidict
        assert 'content' in dict_multidict
        assert 'X-HEADER' in dict_multidict

        assert 'X-HEADER' in test_dict
        assert 'content' in test_dict

        # iteration should expose the original stored keys and values
        items_dict = dict(dict_multidict.items())
        assert items_dict.get('X-Header') == 'val'
        assert items_dict.get('Content') == 'c'

        items_test = dict(test_dict.items())
        assert items_test.get('X-Header') == 'val'
        assert items_test.get('Content') == 'c'

    def test_multidict_multiple_entries_same_key(self):
        """
        Check behavior when multiple entries for same key exist (different cases).
        We don't assert a specific rule about which value is returned across
        implementations — only that lookups find one of the stored values
        and membership is case-insensitive.
        """
        md = multidict.CIMultiDict([('Title', 'first'), ('title', 'second')])
        cim = TestCIMultiDict.CaseInsensitiveMultiDict([('Title', 'first'), ('title', 'second')])

        # membership checks
        assert 'title' in md
        assert 'TITLE' in md
        assert 'title' in cim
        assert 'TITLE' in cim

        # retrieving should return one of the inserted values (string)
        assert md['title'] in ('first', 'second')
        assert cim['title'] in ('first', 'second')