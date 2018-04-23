# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_aircrafts
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.aircrafts module

    This file is part of mss.

    :copyright: Copyright 2017 Reimar Bauer
    :copyright: Copyright 2017-2018 by the mss team, see AUTHORS.
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
        descent_performance = self.SimpleAircraft.get_descent_performance(200, 85000.)
        assert len(descent_performance) == 3
        assert descent_performance[0] == 0.
        assert descent_performance[1] == 0
        assert descent_performance[2] == 0
