""" Stores WMS login credentials during program runtime.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus
   Copyright 2016-2017 see AUTHORS

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

AUTHORS:
========

* Tongxi Lou (tl)
* Marc Rautenhaus (mr)

"""


import os

HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(HOME, ".config")
MSS_CONFIG_PATH = os.getenv("MSS_CONFIG_PATH", os.path.join(HOME, ".config", "mss"))
if not os.path.exists(MSS_CONFIG_PATH):
    os.makedirs(MSS_CONFIG_PATH)

MSS_SETTINGS = os.getenv('MSS_SETTINGS', os.path.join(MSS_CONFIG_PATH, "mss_settings.json"))

WMS_LOGIN_CACHE = {}
CACHED_CONFIG_FILE = None

if os.path.exists(MSS_SETTINGS):
    CACHED_CONFIG_FILE = MSS_SETTINGS
