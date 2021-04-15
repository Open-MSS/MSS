# -*- coding: utf-8 -*-
"""

    mslib.version
    ~~~~~~~~~~~~~~~~

    This module provides the version number

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
import os
import sys
import glob


__version__ = u'2.0.4.'

__conda_meta__ = os.path.join(sys.prefix, 'conda-meta', '')
__mss_description__ = glob.glob(os.path.join(__conda_meta__, 'mss-*'))
__canonical_name__ = ""
if len(__mss_description__) == 1:
    __canonical_name__ = __mss_description__[0].split(__conda_meta__)[1].split('.json')[0]
