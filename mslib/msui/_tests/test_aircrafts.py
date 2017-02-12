# -*- coding: iso-8859-1 -*-
"""
    MSS - some common code for testing

    @copyright: 2017 Reimar Bauer,

    @license: License: Apache-2.0, see LICENSE.txt for details.
"""

from mslib.msui.aircrafts import SimpleAircraft, AIRCRAFT_DUMMY


class Test_SimpleAircraft(object):
    def setup(self):
        self.SimpleAircraft = SimpleAircraft(AIRCRAFT_DUMMY)

    def test__get_weights(self):
        test_values = [([65000., 85000.], 75000., (0, 0.5, 1, 0.5)),
                       ([15000., 22700., 28000.], 28000., (2, 1, 2, 0))
                       ]
        for xs, x, result in test_values:
            assert self.SimpleAircraft._get_weights(xs, x) == result

    def test_get_climb_performance(self):
        climb_performance = self.SimpleAircraft.get_climb_performance(200, 85000.)
        assert len(climb_performance) == 3
        assert climb_performance[0] == 0
        assert climb_performance[1] == 0.0
        assert climb_performance[2] == 0.0

    def test_get_cruise_performance(self):
        cruise_performance = self.SimpleAircraft.get_cruise_performance(200, 85000.)
        assert len(cruise_performance) == 2
        assert cruise_performance[0] == 400.
        assert cruise_performance[1] == 2900.

    def test_get_decent_performance(self):
        decent_performance = self.SimpleAircraft.get_cruise_performance(200, 85000.)
        assert len(decent_performance) == 2
        assert decent_performance[0] == 400.
        assert decent_performance[1] == 2900.
