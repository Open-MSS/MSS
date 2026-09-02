# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_service_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.utils.service_manager

    This file is part of MSS.

    :copyright: Copyright 2025 Reimar Bauer
    :copyright: Copyright 2025-2026 by the MSS team, see AUTHORS.
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
import pytest

from mslib.utils.service_manager import WMSServiceManager, service_cache_key, strip_request_params


class TestStripRequestParams:
    @pytest.mark.parametrize("url,expected", [
        ("http://example.com/wms", "http://example.com/wms"),
        ("http://example.com/wms?service=WMS&request=GetCapabilities", "http://example.com/wms"),
        ("http://example.com/wms?SERVICE=WMS&REQUEST=GetCapabilities", "http://example.com/wms"),
        ("http://example.com/wms?dataset=a&service=WMS", "http://example.com/wms?dataset=a"),
        # other parameters keep their original order
        ("http://example.com/wms?b=2&a=1", "http://example.com/wms?b=2&a=1"),
    ])
    def test_strip_request_params(self, url, expected):
        assert strip_request_params(url) == expected


class TestServiceCacheKey:
    @pytest.mark.parametrize("url,other", [
        # a port is not the same as a path element
        ("http://example.com:1/wms", "http://example.com/1/wms"),
        ("https://example.com:8080/wms", "https://example.com/8080/wms"),
        # nor is a host boundary the same as a path separator
        ("http://example.com/wms", "http://example/com/wms"),
        # different hosts, same words
        ("http://a.example.com/wms", "http://a-example-com/wms"),
        # parameters must not collapse into the path either
        ("http://example.com/wms?dataset=a", "http://example.com/wms/dataset/a"),
        ("http://example.com/wms?dataset=a&layer=b", "http://example.com/wms?dataset=a-layer-b"),
        # a parameter value separator is not a parameter separator
        ("http://example.com/wms?dataset=a&layer=b", "http://example.com/wms?dataset=a%26layer%3Db"),
    ])
    def test_distinct_urls_get_distinct_keys(self, url, other):
        assert service_cache_key(url) != service_cache_key(other)

    @pytest.mark.parametrize("url,other", [
        # the GetCapabilities request itself is not part of the service
        ("http://example.com/wms",
         "http://example.com/wms?service=WMS&request=GetCapabilities"),
        ("http://example.com/wms?dataset=a",
         "http://example.com/wms?service=WMS&dataset=a&request=GetCapabilities"),
        # parameter order does not matter
        ("http://example.com/wms?dataset=a&layer=b",
         "http://example.com/wms?layer=b&dataset=a"),
        # scheme and host are case insensitive
        ("http://example.com/wms", "HTTP://Example.COM/wms"),
        ("http://example.com:1/wms", "HTTP://Example.COM:1/wms"),
    ])
    def test_equivalent_urls_share_a_key(self, url, other):
        assert service_cache_key(url) == service_cache_key(other)

    @pytest.mark.parametrize("url,other", [
        # the path is case sensitive
        ("http://example.com/wms", "http://example.com/WMS"),
        # so are parameter names and values
        ("http://example.com/wms?dataset=a", "http://example.com/wms?dataset=A"),
        ("http://example.com/wms?dataset=a", "http://example.com/wms?DATASET=a"),
        # a scheme is not just a name
        ("http://example.com/wms", "https://example.com/wms"),
    ])
    def test_case_and_scheme_are_kept(self, url, other):
        assert service_cache_key(url) != service_cache_key(other)


class TestWMSServiceManager:
    @pytest.fixture(autouse=True)
    def _cache(self):
        manager = WMSServiceManager()
        manager.clear_cache()
        yield
        manager.clear_cache()

    def test_cache_and_get_service(self):
        manager = WMSServiceManager()
        assert manager.get_service("http://example.com/wms") is None
        manager.cache_service("http://example.com/wms", "wms")
        assert manager.get_service("http://example.com/wms") == "wms"

    def test_get_service_by_equivalent_url(self):
        manager = WMSServiceManager()
        manager.cache_service("http://example.com/wms?dataset=a", "wms")
        assert manager.get_service(
            "http://example.com/wms?request=GetCapabilities&dataset=a&service=WMS") == "wms"

    @pytest.mark.parametrize("url,other", [
        ("http://example.com:1/wms", "http://example.com/1/wms"),
        ("http://example.com/wms?dataset=a", "http://example.com/wms?dataset=b"),
        ("http://example.com/wms?dataset=a", "http://example.com/wms"),
    ])
    def test_distinct_services_do_not_share_an_entry(self, url, other):
        manager = WMSServiceManager()
        manager.cache_service(url, "wms")
        assert manager.get_service(other) is None

    def test_shared_cache_between_instances(self):
        WMSServiceManager().cache_service("http://example.com/wms", "wms")
        assert WMSServiceManager().get_service("http://example.com/wms") == "wms"
