# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_csv
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.plugins.io.csv

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
from mslib.plugins.io import csv


def test_save_to_csv():
    save_csv = os.path.join(ROOT_DIR, "testdata.csv")
    wp = _example_waypoints()
    name = "testdata"
    csv.save_to_csv(save_csv, name, wp)
    with open(save_csv) as f:
        data = f.readlines()
    assert data == ['testdata\n',
                    'Index;Location;Lat (+-90);Lon (+-180);Flightlevel;Pressure (hPa);Leg dist. '
                    '(km);Cum. dist. (km);Comments\n',
                    '0;Anchorage;61.168;-149.960;350.000;238.416;0.000;0.000;start\n',
                    '1;Adak;51.878;-176.646;350.000;238.416;0.000;0.000;last\n'
                    ]


def test_load_from_csv():
    data = ['testreaddata\n',
            'Index;Location;Lat (+-90);Lon (+-180);Flightlevel;Pressure (hPa);Leg dist. '
            '(km);Cum. dist. (km);Comments\n',
            '0;Anchorage;61.168;-149.960;350.000;238.416;0.000;0.000;start\n',
            '1;Adak;51.878;-176.646;350.000;238.416;0.000;0.000;last\n'
            ]
    load_csv = os.path.join(ROOT_DIR, "testreaddata.csv")
    with open(load_csv, 'w') as f:
        f.writelines(data)
    name, wp = csv.load_from_csv(load_csv)
    assert name == "testreaddata"
    assert wp[0].location == "Anchorage"
    assert wp[0].comments == "start"
    assert wp[1].location == "Adak"
    assert wp[1].comments == "last"


def _example_waypoints():
    return [ft.Waypoint(lat=61.168, lon=-149.960, flightlevel=350, location="Anchorage", comments="start"),
            ft.Waypoint(lat=51.878, lon=-176.646, flightlevel=350, location="Adak", comments="last")]
