# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_verify_xml_waypoint
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This tests for valid xml data of waypoint data.

    This file is part of MSS.

    :copyright: Copyright 2024 Reimar Bauer
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

from mslib.utils.verify_waypoint_data import verify_waypoint_data


def test_verify_xml_waypoint():
    """
    tests various XML waypoint data content
    """
    flight_track_with_waypoints = """<?xml version="1.0" encoding="utf-8"?>
    <FlightTrack version="9.0.0">
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
    <FlightTrack version="9.0.0">
      <ListOfWaypoints>
      </ListOfWaypoints>
    </FlightTrack>"""

    flight_track_incomplete = """<?xml version="1.0" encoding="utf-8"?>
        <FlightTrack version="9.0.0">
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
        <FlightTrack version="9.0.0">
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
        </FlightTrack>"""

    xml_content = (
        (flight_track_with_waypoints, True),
        (flight_track_empty, False),
        (flight_track_incomplete, False),
        (flight_track_with_typo, False),
    )

    for xml, check in xml_content:
        assert verify_waypoint_data(xml) is check
