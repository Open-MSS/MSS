# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_airdata
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.airdata

    This file is part of MSS.

    :copyright: Copyright 2022-2022 Reimar Bauer
    :copyright: Copyright 2022-2023 by the MSS team, see AUTHORS.
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
import mock
from PyQt5 import QtWidgets
from mslib.utils.airdata import download_progress, get_airports,\
    get_available_airspaces, update_airspace, get_airspaces
from tests.constants import ROOT_DIR


def _download_progress_airports(path, url):
    """ mock expensive download from external site"""
    assert path is not None
    assert url is not None
    text = '''"id","ident","type","name","latitude_deg","longitude_deg","elevation_ft","continent",\
"iso_country","iso_region","municipality","scheduled_service","gps_code","iata_code","local_code",\
"home_link","wikipedia_link","keywords"
6523,"00A","heliport","Total Rf Heliport",40.07080078125,-74.93360137939453,11,"NA","US",\
"US-PA","Bensalem","no","00A",,"00A",,,\
323361,"00AA","small_airport","Aero B Ranch Airport",38.704022,-101.473911,3435,"NA",\
"US","US-KS","Leoti","no","00AA",,"00AA",,,'''
    file_path = os.path.join(ROOT_DIR, "downloads", "aip", "airports.csv")
    with open(file_path, "w") as f:
        f.write(text)


def _download_progress_airspace(path, url):
    """ mock expensive download from external site"""
    assert path is not None
    assert url is not None
    text = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
 <!-- For Testing ONLY -->
<OPENAIP VERSION="1668386405436" DATAFORMAT="1.1" xmlns="https://www.openaip.net"\
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
  xsi:schemaLocation="https://www.openaip.net https://storage.googleapis.com/d644c13a-ed49-48ad-8493-d3e55d3281a5\
  /assets/common/openaip-schema-v1.xsd">
<AIRSPACES><ASP CATEGORY="C"><VERSION>1669682436912</VERSION><ID>631330d834a543d6cb4a83fe\
</ID><COUNTRY>BG</COUNTRY><NAME>TMA 1 SOFIA 123.700</NAME><ALTLIMIT_TOP REFERENCE="STD">\
<ALT UNIT="FL">245</ALT></ALTLIMIT_TOP><ALTLIMIT_BOTTOM REFERENCE="MSL"><ALT UNIT="F">8500</ALT>\
</ALTLIMIT_BOTTOM><GEOMETRY><POLYGON>22.4899253237031 43.56620830068364,22.79416666666667 \
43.478611111111114,23.09111111111111 43.39222222222222,23.31277777777778 43.32833333333333,\
23.80777777777778 43.151111111111106,24.220555555555553 43.09527777777778,24.16333333333333 \
42.705000000000005,24.129444444444445 42.66027777777778,24.029444444444444 42.52777777777778,\
24.371111111111112 42.37583333333333,24.25583333333333 42.23416666666667,24.078055555555554 \
42.31361111111111,23.90694444444444 42.30916666666666,22.691666666666666 42.269999999999996,\
22.634999999999998 42.882222222222225,22.636388888888888 42.87916666666667,22.65694444444444 \
42.88111111111111,22.66722222222222 42.87638888888889,22.676944444444445 42.86694444444444,\
22.68166666666667 42.86333333333334,22.684722222222224 42.87083333333334,22.698888888888888 \
42.88,22.703888888888887 42.88666666666666,22.713055555555556 42.88055555555555,22.720555555555553 \
42.88388888888889,22.739444444444445 42.88527777777778\
</POLYGON></GEOMETRY></ASP></AIRSPACES>
</OPENAIP>
'''
    file_path = os.path.join(ROOT_DIR, "downloads", "aip", "bg_asp.xml")
    with open(file_path, "w") as f:
        f.write(text)


def _download_incomplete_airspace(path, url):
    """ mock expensive download from external site"""
    assert path is not None
    assert url is not None
    text = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
 <!-- For Testing ONLY -->
<OPENAIP VERSION="1668386405436" DATAFORMAT="1.1" xmlns="https://www.openaip.net"\
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
  xsi:schemaLocation="https://www.openaip.net https://storage.googleapis.com/d644c13a-ed49-48ad-8493-d3e55d3281a5\
  /assets/common/openaip-schema-v1.xsd">
<AIRSPACES></AIRSPACES>
</OPENAIP>
'''
    file_path = os.path.join(ROOT_DIR, "downloads", "aip", "bg_asp.xml")
    with open(file_path, "w") as f:
        f.write(text)


def _cleanup_test_files():
    file_path = os.path.join(ROOT_DIR, "downloads", "aip", "bg_asp.xml")
    if "tmp" in file_path:
        if os.path.exists(file_path):
            os.remove(file_path)
    file_path = os.path.join(ROOT_DIR, "downloads", "aip", "airports.csv")
    if "tmp" in file_path:
        if os.path.exists(file_path):
            os.remove(file_path)


def test_download_progress():
    file_path = os.path.join(ROOT_DIR, "downloads", "aip", "airdata")
    download_progress(file_path, 'http://speedtest.ftp.otenet.gr/files/test100k.db')
    assert os.path.exists(file_path)


@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.No)
def test_get_airports(mockbox):
    _cleanup_test_files()
    airports = get_airports()
    assert airports == []


@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
def test_get_downloaded_airports(mockbox):
    with mock.patch("mslib.utils.airdata.download_progress", _download_progress_airports):
        airports = get_airports(force_download=True)
        assert len(airports) > 0
        assert 'continent' in airports[0].keys()
        assert mockbox.critical.call_count == 0


def test_get_available_airspaces():
    _cleanup_test_files()
    airspaces = get_available_airspaces()
    assert len(airspaces) > 0


@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
def test_update_airspace(mockbox):
    with mock.patch("mslib.utils.airdata.download_progress", _download_progress_airspace):
        update_airspace(force_download=True, countries=["bg"])
        example_file = os.path.join(ROOT_DIR, "downloads", "aip", "bg_asp.xml")
        os.path.exists(example_file)
        with open(example_file, 'r') as f:
            text = f.read()
        assert "<!-- For Testing ONLY -->" in text
        assert mockbox.critical.call_count == 0


@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.No)
def test_get_airspaces_no_data(mockbox):
    """
    In the test environment we start always in a fresh tmp dir, no data is available
    once it is downloaded it is managed by airdata
    """
    _cleanup_test_files()
    airspaces = get_airspaces(countries=["bg"])
    assert airspaces == []


@mock.patch("mslib.utils.airdata.download_progress", _download_progress_airspace)
@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
def test_get_airspaces(mockbox):
    """ We use a test file without the need for downloading to check handling """
    # update_airspace would only update after 30 days
    _cleanup_test_files()
    airspaces = get_airspaces(countries=["bg"])
    assert airspaces == [
        {'top': 7.47,
         'bottom': 2.59,
         'country': 'BG',
         'name': 'TMA 1 SOFIA 123.700',
         'polygon': [(22.4899253237031, 43.56620830068364),
                     (22.79416666666667, 43.478611111111114),
                     (23.09111111111111, 43.39222222222222),
                     (23.31277777777778, 43.32833333333333),
                     (23.80777777777778, 43.151111111111106),
                     (24.220555555555553, 43.09527777777778),
                     (24.16333333333333, 42.705000000000005),
                     (24.129444444444445, 42.66027777777778),
                     (24.029444444444444, 42.52777777777778),
                     (24.371111111111112, 42.37583333333333),
                     (24.25583333333333, 42.23416666666667),
                     (24.078055555555554, 42.31361111111111),
                     (23.90694444444444, 42.30916666666666),
                     (22.691666666666666, 42.269999999999996),
                     (22.634999999999998, 42.882222222222225),
                     (22.636388888888888, 42.87916666666667),
                     (22.65694444444444, 42.88111111111111),
                     (22.66722222222222, 42.87638888888889),
                     (22.676944444444445, 42.86694444444444),
                     (22.68166666666667, 42.86333333333334),
                     (22.684722222222224, 42.87083333333334),
                     (22.698888888888888, 42.88),
                     (22.703888888888887, 42.88666666666666),
                     (22.713055555555556, 42.88055555555555),
                     (22.720555555555553, 42.88388888888889),
                     (22.739444444444445, 42.88527777777778)]
        }
    ]
    assert mockbox.critical.call_count == 0


@mock.patch("mslib.utils.airdata.download_progress", _download_incomplete_airspace)
@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
def test_get_airspaces_missing_data(mockbox):
    """ We use a test file without the need for downloading to check handling """
    # update_airspace would only update after 30 days
    _cleanup_test_files()
    airspaces = get_airspaces(countries=["bg"])
    assert airspaces == []
