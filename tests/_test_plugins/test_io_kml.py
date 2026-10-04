# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_kml
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.plugins.io.kml

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
import os

import defusedxml.ElementTree as etree

import mslib.msui.flighttrack as ft
from tests.constants import ROOT_DIR
from mslib.plugins.io import kml


def test_save_to_kml():
    try:
        filename = os.path.join(ROOT_DIR, "testkmldata.kml")
        wp = _example_waypoints()
        name = "testkmldata"
        kml.save_to_kml(filename, name, wp)
        with open(filename) as f:
            data = f.readlines()
        assert data == ['<?xml version="1.0" encoding="UTF-8" ?>\n',
                        '<kml xmlns="http://www.opengis.net/kml/2.2">\n',
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
                        '<coordinates>-149.960,61.168,10668.000\n',
                        '-176.646,51.878,10668.000\n',
                        '</coordinates>\n',
                        '</LineString></Placemark><Placemark>\n',
                        '<name>Anchorage</name>\n',
                        '<Point>\n',
                        '  <coordinates>-149.960,61.168,10668.000</coordinates>\n',
                        '</Point>\n',
                        '</Placemark><Placemark>\n',
                        '<name>Adak</name>\n',
                        '<Point>\n',
                        '  <coordinates>-176.646,51.878,10668.000</coordinates>\n',
                        '</Point>\n',
                        '</Placemark></Document>\n',
                        '</kml>'
                        ]
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def _example_waypoints():
    return [ft.Waypoint(lat=61.168, lon=-149.960, flightlevel=350, location="Anchorage", comments="start"),
            ft.Waypoint(lat=51.878, lon=-176.646, flightlevel=350, location="Adak", comments="last")]


def test_save_to_kml_escapes_names(tmp_path):
    # names are chosen by collaborators, they must not add elements, e.g. an HTML balloon, to the KML file
    track_name = 'track</name><description><![CDATA[<a href="file:///etc/passwd">open</a>]]></description><name>'
    waypoint_name = 'Anchorage & <b>"Adak"</b>'
    waypoints = _example_waypoints()
    waypoints[0].location = waypoint_name
    filename = tmp_path / "escaped.kml"
    kml.save_to_kml(str(filename), track_name, waypoints)
    namespace = {"kml": "http://www.opengis.net/kml/2.2"}
    tree = etree.parse(str(filename))
    assert [element.text for element in tree.iterfind(".//kml:name", namespace)] == [
        track_name, track_name, waypoint_name, "Adak"]
    assert [element.text for element in tree.iterfind(".//kml:description", namespace)] == [
        "MSS flight track export"]


def test_save_to_kml_drops_characters_xml_does_not_allow(tmp_path):
    # a collaborator must not be able to make the KML export of the operation unreadable
    waypoints = _example_waypoints()
    waypoints[0].location = "A\x0bB\x00C\x1f D\tE"
    filename = tmp_path / "control.kml"
    kml.save_to_kml(str(filename), "track\x01name", waypoints)
    namespace = {"kml": "http://www.opengis.net/kml/2.2"}
    tree = etree.parse(str(filename))
    assert [element.text for element in tree.iterfind(".//kml:name", namespace)] == [
        "trackname", "trackname", "ABC D\tE", "Adak"]
