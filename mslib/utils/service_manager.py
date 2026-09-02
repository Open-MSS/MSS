# -*- coding: utf-8 -*-
"""

    mslib.utils.service_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    caches wms services

    This file is part of MSS.

    :copyright: Copyright 2025 Reimar Bauer
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
import urllib.parse

# query parameters which describe a single request instead of the service itself
OGC_REQUEST_PARAMS = ("service", "request")


def strip_request_params(url):
    """Remove the OGC request parameters (service, request) from an url.

    All other query parameters are kept in their original order, so the result
    can be used as base url for further requests to the same service.
    """
    scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
    kept = [(key, value) for key, value in urllib.parse.parse_qsl(query)
            if key.lower() not in OGC_REQUEST_PARAMS]
    return urllib.parse.urlunparse(
        (scheme, netloc, path, params, urllib.parse.urlencode(kept), fragment))


def service_cache_key(url):
    """Build the cache key of a WMS service from its full url.

    In contrast to using only the base url, the query parameters are part of
    the key. Services which differ solely in their parameters, e.g.
    "https://example.com/wms?dataset=a", therefore get separate cache entries.

    The parameters of the GetCapabilities request itself are dropped and the
    remaining ones are sorted, so that the very same service is found again no
    matter how the request was spelled. Scheme and host are lower cased because
    they are case insensitive, the rest of the url is not.

    The key is the normalized url itself. It must not be reduced any further,
    e.g. by slugifying it, because that would collapse the url separators and
    map distinct services onto the same key, for example
    "http://example.com:1/wms" and "http://example.com/1/wms".
    """
    scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(strip_request_params(url))
    query = urllib.parse.urlencode(sorted(urllib.parse.parse_qsl(query)))
    return urllib.parse.urlunparse(
        (scheme.lower(), netloc.lower(), path, params, query, fragment))


class WMSServiceManager:

    _instance = None
    _shared_cache = {}

    def __new__(cls, cache=None):
        if cls._instance is None:
            cls._instance = super(WMSServiceManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, cache=None):
        if not hasattr(self, '_initialized'):
            self._cache = cache or self._shared_cache
            self._initialized = True

    def clear_cache(self):
        self._cache.clear()

    def get_service(self, url):
        return self._cache.get(service_cache_key(url))

    def cache_service(self, url, wms):
        self._cache[service_cache_key(url)] = wms
