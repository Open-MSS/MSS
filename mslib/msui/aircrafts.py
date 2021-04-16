# -*- coding: utf-8 -*-
"""

    mslib.msui.aircrafts
    ~~~~~~~~~~~~~~~~~~~~

    This module provides aircrafts definitions

    This file is part of mss.

    :copyright: Copyright 2016-2017 Joern Ungermann
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

import bisect
import logging

import numpy as np

AIRCRAFT_DUMMY = {
    "name": "DUMMY",
    "takeoff_weight": 90000,
    "fuel": 35000,
    "climb": [[0.00, 0.0, 0.0, 0.0, 0.0]],
    "descent": [[0.00, 0.0, 0.0, 0.0, 0.0]],
    "cruise": [[0.00, 0.00, 400, 2900.00]],
    "ceiling": [410],
}


class SimpleAircraft(object):
    """
    Simple aircraft model that offers methods to estimate fuel and time consumption
    of air craft for different flight maneuvers.
    """

    def __init__(self, data):
        self.name = data["name"]
        self.takeoff_weight = data.get("takeoff_weight", 0)
        self.fuel = data.get("fuel", 0)
        self._climb = self._setup(data["climb"])
        self._descent = self._setup(data["descent"])
        self._cruise = self._setup(data["cruise"])
        self._ceiling_poly = np.asarray(data.get("ceiling", [410]))[::-1]

    def _setup(self, data):
        data = np.asarray(data)
        if len(data) == 0:
            raise ValueError("Performance data requires at least one line per table!")
        weights = np.asarray(sorted(set(data[:, 0])))
        table = []
        for weight in weights:
            selection = (data[:, 0] == weight)
            table.append(data[selection][:, 1:])
        return weights, table

    def _get_weights(self, xs, x):
        """
        Calculates linear interpolation weights and indices.

        Args:
            xs: sorted list of values
            x: value for which to compute interpolation weights

        Returns: index_0, weight_0, index_1, weight_1 for interpolation.
        """
        assert len(xs) > 0, xs
        index1 = bisect.bisect(xs, x)
        if index1 == len(xs):
            index1 -= 1
            index0 = index1
            weight0, weight1 = 1, 0
        elif index1 == 0:
            index0 = 0
            weight0, weight1 = 1, 0
        else:
            index0 = index1 - 1
            weight0 = (x - xs[index1]) / (xs[index0] - xs[index1])
            weight1 = 1. - weight0
        assert 0 <= weight0 <= 1, (xs, x, weight0)
        assert 0 <= weight1 <= 1, (xs, x, weight1)
        return index0, weight0, index1, weight1

    def _interpolate_alt(self, table, altitude):
        idx0, w0, idx1, w1 = self._get_weights(table[:, 0], altitude)
        return w0 * table[idx0, 1:] + w1 * table[idx1, 1:]

    def _interpolate(self, table, altitude, grossweight):
        weights, data = table
        idx0, w0, idx1, w1 = self._get_weights(weights, grossweight)
        return self._interpolate_alt(data[idx0], altitude) * w0 + self._interpolate_alt(data[idx1], altitude) * w1

    def get_climb_performance(self, altitude, grossweight):
        """
        Climb performance of the aircraft. Returns time [min], distance [nm] and
        fuel [lbs] required for a climb from sea level to the specified
        altitude.

        Args:
            altitude:     altitude in ft to climb to
            grossweight:  total weight of the aircraft in lbs
        """
        return self._interpolate(self._climb, altitude, grossweight)

    def get_cruise_performance(self, altitude, grossweight):
        """
        Cruise performance of the aircraft. Returns true airspeed [knots] and
        fuelflow [lbs/hr] required for a cruise at the specified altitude.

        Args:
            altitude:     altitude in ft to climb to
            grossweight:  total weight of the aircraft in lbs
        """
        return self._interpolate(self._cruise, altitude, grossweight)

    def get_descent_performance(self, altitude, grossweight):
        """
        Descent performance of the aircraft. Returns time [min], distance [nm]
        and fuel [lbs] required for a climb from sea level to the specified
        altitude.

        Args:
            altitude:     altitude in ft to climb to
            grossweight:  total weight of the aircraft in lbs
        """
        return self._interpolate(self._descent, altitude, grossweight)

    def get_ceiling_altitude(self, grossweight):
        """
        Ceiling altitude of aircraft for given weight [lbs]. Computed by
        a polynomial with arbitray number of terms.

        Args:
            grossweight:  total weight of the aircraft in lbs
        """
        if hasattr(self, "_ceiling_poly"):
            maxFL = int(np.polyval(self._ceiling_poly, grossweight))
        else:
            logging.error("No data stored for computation of ceiling altitude. "
                          "Please reload performance data from JSON.")
            maxFL = 410
        return maxFL
