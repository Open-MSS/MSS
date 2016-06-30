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

# standard library imports

# related third party imports

# local application imports


"""
Global cache variables
"""

global cached_usrname
global cached_passwd
global cached_config_file

cached_usrname = None
cached_passwd = None
cached_config_file = None
