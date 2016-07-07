""" Stores WMS login credentials during program runtime.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus

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
if not os.path.exists(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)
DEFAULT_CONFIG_PATH = os.path.join(HOME, ".config", "mss")
if not os.path.exists(DEFAULT_CONFIG_PATH):
    os.mkdir(DEFAULT_CONFIG_PATH)

MSS_SETTINGS = os.getenv('MSS_SETTINGS', os.path.join(DEFAULT_CONFIG_PATH, "mss_settings.json"))

wms_login_cache = {}
cached_config_file = None

if os.path.exists(MSS_SETTINGS):
    cached_config_file = MSS_SETTINGS
