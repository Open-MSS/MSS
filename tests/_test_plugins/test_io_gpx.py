# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_gpx
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.plugins.io.gpx

    This file is part of MSS.

    :copyright: Copyright 2022-2022 Reimar Bauer
    :copyright: Copyright 2022-2022 by the MSS team, see AUTHORS.
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
from mslib.plugins.io import gpx


def test_save_to_gpx():
    filename = os.path.join(ROOT_DIR, "testgpxdata.gpx")
    wp = _example_waypoints()
    name = "testgpxdata"
    gpx.save_to_gpx(filename, name, wp)
    with open(filename) as f:
        data = f.readlines()
    assert data == ['<?xml version="1.0" encoding="UTF-8"?>\n',
                    '<gpx xmlns="http://www.topografix.com/GPX/1/1" '
                    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                    'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
                    'http://www.topografix.com/GPX/1/1/gpx.xsd" version="1.1" creator="gpx.py -- '
                    'https://github.com/tkrajina/gpxpy">\n',
                    '  <metadata>\n',
                    '    <name>testgpxdata</name>\n',
                    '    <desc>MSS flight track export</desc>\n',
                    '  </metadata>\n',
                    '  <trk>\n',
                    '    <trkseg>\n',
                    '      <trkpt lat="61.168" lon="-149.96">\n',
                    '        <name>Anchorage</name>\n',
                    '      </trkpt>\n',
                    '      <trkpt lat="51.878" lon="-176.646">\n',
                    '        <name>Adak</name>\n',
                    '      </trkpt>\n',
                    '    </trkseg>\n',
                    '  </trk>\n',
                    '</gpx>'
                    ]


def _example_waypoints():
    return [ft.Waypoint(lat=61.168, lon=-149.960, flightlevel=350, location="Anchorage", comments="start"),
            ft.Waypoint(lat=51.878, lon=-176.646, flightlevel=350, location="Adak", comments="last")]
