# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_verify_xml_waypoint
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This tests for valid xml data of waypoint data.

    This file is part of MSS.

    :copyright: Copyright 2024 Reimar Bauer
    :copyright: Copyright 2024-2026 by the MSS team, see AUTHORS.
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
import pytest

from mslib.utils.verify_waypoint_data import verify_waypoint_data


flight_track_with_waypoints = """<?xml version="1.0" encoding="utf-8"?>
        <FlightTrack version="9.1.0">
          <ListOfWaypoints>
            <Waypoint flightlevel="233.0" lat="41.601070573320186" location="" lon="41.355120439498535">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="374.0" lat="48.19354838709677" location="" lon="33.74841526975632">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="372.0" lat="51.23623045499366" location="" lon="-34.20481757994082">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="20.0" lat="37.037047471474835" location="" lon="-40.797295393717434">
              <Comments></Comments>
            </Waypoint>
          </ListOfWaypoints>
        </FlightTrack>"""

flight_track_with_waypoints_and_broken_by_linebreak = """
    <?xml version="1.0" encoding="utf-8"?>
        <FlightTrack version="9.1.0">
          <ListOfWaypoints>
            <Waypoint flightlevel="233.0" lat="41.601070573320186" location="" lon="41.355120439498535">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="374.0" lat="48.19354838709677" location="" lon="33.74841526975632">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="372.0" lat="51.23623045499366" location="" lon="-34.20481757994082">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="20.0" lat="37.037047471474835" location="" lon="-40.797295393717434">
              <Comments></Comments>
            </Waypoint>
          </ListOfWaypoints>
        </FlightTrack>"""

flight_track_empty = """<?xml version="1.0" encoding="utf-8"?>
        <FlightTrack version="9.1.0">
          <ListOfWaypoints>
          </ListOfWaypoints>
        </FlightTrack>"""

flight_track_incomplete = """<?xml version="1.0" encoding="utf-8"?>
        <FlightTrack version="9.1.0">
          <ListOfWaypoints>
            <Waypoint flightlevel="233.0" lat="41.601070573320186">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="374.0">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="372.0" lat="51.23623045499366" location="" lon="-34.20481757994082">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="20.0" lat="37.037047471474835" location="">
              <Comments></Comments>
            </Waypoint>
          </ListOfWaypoints>
        </FlightTrack>"""

flight_track_with_typo = """<?xml version="1.0" encoding="utf-8"?>
            <FlightTrack version="9.1.0">
              <ListOfWaypoints>
                <Waypoint flightlevel="233.0"" lat="41.601070573320186" location="" lon="41.355120439498535">
                  <Comments></Comments>
                </Waypoint>
                <Waypoint flightlevel="374.0" lat="48.19354838709677" location="" lon="33.74841526975632">
                  <Comments></Comments>
                </Waypoint>
                  <Comments></Comments>
                </Waypoint>
              </ListOfWaypoints>
            </FlightTrack>
            """  # typo is "233.0""

cases = [
    (flight_track_with_waypoints, True),
    (flight_track_with_waypoints_and_broken_by_linebreak, False),
    (flight_track_empty, False),
    (flight_track_incomplete, False),
    (flight_track_with_typo, False),
]


@pytest.mark.parametrize("xml_content, verification_result", cases)
def test_verify_xml_waypoint(xml_content, verification_result):
    """Test xml verification."""
    assert verify_waypoint_data(xml_content) is verification_result


def flight_track(lat="50", lon="6", flightlevel="300", comments="<Comments></Comments>"):
    """Two waypoints, the first with the given attributes"""
    return ('<?xml version="1.0" encoding="utf-8"?><FlightTrack version="9.1.0"><ListOfWaypoints>'
            f'<Waypoint flightlevel="{flightlevel}" lat="{lat}" location="" lon="{lon}">{comments}</Waypoint>'
            '<Waypoint flightlevel="300" lat="51" location="" lon="7"><Comments></Comments></Waypoint>'
            '</ListOfWaypoints></FlightTrack>')


@pytest.mark.parametrize("xml_content", [
    "<a/>",
    flight_track(comments=""),
    '<!DOCTYPE a [<!ENTITY e "x">]><FlightTrack/>',
    "<a>\ud800</a>",
    None,
    "<a>" * 5000 + "</a>" * 5000,
    flight_track().replace("utf-8", "bogus").encode("ascii"),
] + [flight_track(**{attribute: value}) for attribute in ("lat", "lon", "flightlevel")
     for value in ("nan", "inf", "-inf", "1e400")],
    ids=["not-a-flight-track", "no-comments", "entity", "lone-surrogate", "none", "deeply-nested",
         "unknown-encoding"] + [
        f"{attribute}-{value}" for attribute in ("lat", "lon", "flightlevel")
        for value in ("nan", "inf", "-inf", "1e400")])
def test_verify_rejects_without_raising(xml_content):
    """
    Content that isn't a flight track, or with values that aren't finite, is rejected, not raised on: the
    MSColab server stored nan, and raised on the others (#3336)
    """
    assert verify_waypoint_data(xml_content) is False


def test_verify_sets_no_range_limits():
    """Only values that aren't finite are rejected, no ranges"""
    assert verify_waypoint_data(flight_track(lat="100", lon="-700", flightlevel="1e300")) is True
