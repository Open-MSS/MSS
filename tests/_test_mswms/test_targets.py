# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_targets
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.wms

    This file is part of MSS.

    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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
import mslib.mswms.generics as generics


def test_targets():
    for standard_name in generics.get_standard_names():
        unit = generics.get_unit(standard_name)
        units(unit)  # ensure that the unit may be parsed
        generics.get_range(standard_name)
        generics.get_thresholds(standard_name)
        generics.get_range(standard_name)
        generics.get_unit(standard_name)
        generics.get_title(standard_name)
