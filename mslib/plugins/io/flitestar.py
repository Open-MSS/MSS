# -*- coding: utf-8 -*-
"""

    mslib.plugins.io.flitestar
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    plugin for flitestar format flight track export

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
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
from __future__ import division

import numpy as np
import os
from fs import open_fs

import mslib.msui.flighttrack as ft
from mslib.utils import thermolib
from mslib.utils.units import units


def load_from_flitestar(filename):
    waypoints = []
    _dirname, _name = os.path.split(filename)
    _fs = open_fs(_dirname)
    with _fs.open(_name, 'r') as f:
        firstline = f.readline()
        if not firstline.startswith("# FliteStar/FliteMap generated flight plan."):
            raise SyntaxError("The file does not seem to be a FliteStar file!")
        for line in f:

            if line.startswith('FWP'):
                line = line.split()
                if len(line) < 10:
                    raise SyntaxError(f"Line {line} has less than 9 fields.")
                alt = round(float(line[-1]) / 100., 2)
                if line[4] == 'N':
                    NS = 1.
                elif line[4] == 'S':
                    NS = -1.
                else:
                    NS = np.nan
                lat = round((float(line[5]) + (float(line[6]) / 60.)) * NS, 3)
                if line[7] == 'E':
                    EW = 1.
                elif line[7] == 'W':
                    EW = -1.
                else:
                    EW = np.nan
                lon = round((float(line[8]) + (float(line[9]) / 60.)) * EW, 3)

                wp = ft.Waypoint()
                wp.location = line[3]
                wp.lat = float(lat)
                wp.lon = float(lon)
                wp.flightlevel = float(alt)
                wp.pressure = thermolib.flightlevel2pressure(float(wp.flightlevel) * units.hft).magnitude
                waypoints.append(wp)

    name = os.path.basename(filename).strip('.txt')
    return name, waypoints
