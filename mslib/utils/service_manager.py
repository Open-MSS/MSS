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
        return self._cache.get(url)

    def cache_service(self, url, wms):
        self._cache[url] = wms
