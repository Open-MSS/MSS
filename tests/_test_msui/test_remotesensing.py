# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_remotesensing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.remotesensing module

    This file is part of MSS.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017-2023 by the MSS team, see AUTHORS.
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
import pytest
import skyfield_data
from mslib.msui.remotesensing_dockwidget import RemoteSensingControlWidget


def test_skyfield_data_expiration(recwarn):
    pytest.skip("Skip until Version 5.0 is published on conda-forge. Version 4.0 is known as expired.")
    skyfield_data.check_expirations()
    assert len(recwarn) == 0, [_x.message for _x in recwarn]


class TestAngles(object):
    """
    tests about angles
    """

    def test_view_angles(self):
        compute_view_angles = RemoteSensingControlWidget.compute_view_angles
        angle = compute_view_angles(0, 0, 0, 1, 0, 0, 0, -1)
        assert angle[0] == 90.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, -1, 0, 0, 0, -1)
        assert angle[0] == 270.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, 1, 0, 0, 90, -1)
        assert angle[0] == 180.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, 0, 1, 0, 0, -1)
        assert angle[0] == 0.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, 0, -1, 0, 0, -1)
        assert angle[0] == 180.0
        assert angle[1] == -1
