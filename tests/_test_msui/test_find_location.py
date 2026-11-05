# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_find_location
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.msui.utils.find_location (moved here from
    tests/_test_utils/test_coordinate.py: find_location reads its locations from the msui configuration)

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
from mslib.msui.utils.find_location import find_location


def test_find_location():
    assert find_location(50.92, 6.36) == ([50.92, 6.36], 'Juelich')
    assert find_location(50.9200002, 6.36) == ([50.92, 6.36], 'Juelich')
