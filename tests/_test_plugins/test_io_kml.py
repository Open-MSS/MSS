# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_kml
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.plugins.io.kml

    This file is part of MSS.

    :copyright: Copyright 2022-2022 Reimar Bauer
    :copyright: Copyright 2022-2024 by the MSS team, see AUTHORS.
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

import mslib.msui.flighttrack as ft
from tests.constants import ROOT_DIR
from mslib.plugins.io import kml


def test_save_to_kml():
    filename = os.path.join(ROOT_DIR, "testkmldata.kml")
    wp = _example_waypoints()
    name = "testkmldata"
    kml.save_to_kml(filename, name, wp)
    with open(filename) as f:
        data = f.readlines()
    assert data == ['<?xml version="1.0" encoding="UTF-8" ?>\n',
                    '<kml xmlns="http://earth.google.com/kml/2.2">\n',
                    '<Document>\n',
                    '<name>testkmldata</name>\n',
                    '<open>1</open>\n',
                    '<description>MSS flight track export</description>\n',
                    '<Style id="flighttrack">\n',
                    '<LineStyle><color>ff000000</color><width>2</width></LineStyle></Style>\n',
                    '<Placemark><name>testkmldata</name>\n',
                    '<styleUrl>#flighttrack</styleUrl>\n',
                    '<LineString>\n',
                    '<tessellate>1</tessellate><altitudeMode>absolute</altitudeMode>\n',
                    '<coordinates>\n',
                    '-149.960,61.168,10668.000\n',
                    '-176.646,51.878,10668.000\n',
                    '</coordinates>\n',
                    '</LineString></Placemark>\n',
                    '</Document>\n',
                    '</kml>'
                    ]


def _example_waypoints():
    return [ft.Waypoint(lat=61.168, lon=-149.960, flightlevel=350, location="Anchorage", comments="start"),
            ft.Waypoint(lat=51.878, lon=-176.646, flightlevel=350, location="Adak", comments="last")]
