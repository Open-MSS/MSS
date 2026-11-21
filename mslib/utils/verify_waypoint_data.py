# -*- coding: utf-8 -*-
"""

    mslib.utils.verify_waypoint_data
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    basic checks for xml waypoint data.

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


import math

import defusedxml.minidom
import xml.parsers.expat


def verify_waypoint_data(xml_content):
    """
    Whether xml_content is a flight track with at least two waypoints whose positions and flight levels are
    finite numbers. Returns False for anything else, it never raises (#3336).
    """
    try:
        doc = defusedxml.minidom.parseString(xml_content)
    # ValueError includes UnicodeError, e.g. a lone surrogate; TypeError e.g. None, from a server request;
    # LookupError: bytes declaring an unknown encoding
    except (xml.parsers.expat.ExpatError, defusedxml.DefusedXmlException, ValueError, TypeError, LookupError):
        return False
    # minidom searches elements recursively
    try:
        return _is_flight_track(doc)
    except RecursionError:
        return False


def _is_flight_track(doc):
    flight_tracks = doc.getElementsByTagName("FlightTrack")
    if not flight_tracks:
        return False
    waypoints = flight_tracks[0].getElementsByTagName("Waypoint")
    if (len(waypoints)) < 2:
        return False

    for wp_el in waypoints:
        try:
            values = [float(wp_el.getAttribute(name)) for name in ("lat", "lon", "flightlevel")]
        except ValueError:
            return False
        # e.g. nan, inf or 1e400: msui can't compute or show such a flight track
        if not all(math.isfinite(value) for value in values):
            return False
        if not wp_el.getElementsByTagName("Comments"):
            return False

    return True
