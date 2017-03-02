# -*- coding: iso-8859-1 -*-
"""
    MSS - some common code for testing

    @copyright: 2016 - 2017 Reimar Bauer, Joern Ungermann

    @license: License: Apache-2.0, see LICENSE.txt for details.
"""


import pytest
import datetime
from mslib.msui.remotesensing_dockwidget import compute_solar_angle, compute_view_angles


class TestAngles(object):
    """
    tests about angles
    """
    def test_compute_solar_angle(self):
        azimuth_angle, zenith_angle = compute_solar_angle(0, 7.56607, 50.355136)
        assert int(azimuth_angle * 1000) == 13510
        assert int(zenith_angle * 1000) == -62205
        azimuth_angle, zenith_angle = compute_solar_angle(12, 7.56607, 50.355136)
        assert int(azimuth_angle * 1000) == 13607
        assert int(zenith_angle * 1000) == -62197

    def test_view_angles(self):
        angle = compute_view_angles(0, 0, 0, 1, 0, 0, 0)
        assert angle[0] == 90.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, -1, 0, 0, 0)
        assert angle[0] == 270.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, 1, 0, 0, 90)
        assert angle[0] == 180.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, 0, 1, 0, 0)
        assert angle[0] == 0.0
        assert angle[1] == -1
        angle = compute_view_angles(0, 0, 0, 0, -1, 0, 0)
        assert angle[0] == 180.0
        assert angle[1] == -1
