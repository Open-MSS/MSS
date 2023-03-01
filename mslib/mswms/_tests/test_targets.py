# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_targets
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.wms

    This file is part of MSS.

    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

from mslib.utils.units import units
from mslib.mswms.utils import Targets


def test_targets():
    for standard_name in Targets.get_targets():
        unit = Targets.get_unit(standard_name)
        units(unit)  # ensure that the unit may be parsed
        Targets.get_range(standard_name)
        Targets.get_thresholds(standard_name)
        Targets.get_range(standard_name)
        Targets.UNITS[standard_name]
        Targets.TITLES[standard_name]

    for ent in Targets.THRESHOLDS:
        units(Targets.THRESHOLDS[ent][0])
