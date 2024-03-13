# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_mssautoplot
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.utils.mssautoplot

    This file is part of MSS.

    :copyright: Copyright 2023 Harsh Khilawala
    :copyright: Copyright 2023-2024 by the MSS team, see AUTHORS.
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

from mslib.utils.mssautoplot import load_from_ftml


def test_load_from_ftml():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data")
    example_file = os.path.join(sample_path, "example.ftml")
    assert load_from_ftml(example_file) is not None
    data_list, wp_list = load_from_ftml(example_file)
    assert data_list == [(55.15, -23.74, 0.0, 'B', 'Takeoff'),
                         (42.99, -12.1, 350.0, 'A', ''),
                         (52.785, -8.925, 380.0, 'Shannon', 'Dive'),
                         (48.08, 11.28, 400.0, 'EDMO', ''),
                         (63.74, 1.73, 0.0, 'C', 'Landing')]
    assert len(wp_list) == 5
    assert type(wp_list[0]).__name__ == 'Waypoint'
