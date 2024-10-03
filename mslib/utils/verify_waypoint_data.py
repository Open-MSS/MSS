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


import defusedxml.minidom
import xml.parsers.expat


def verify_waypoint_data(xml_content):
    try:
        doc = defusedxml.minidom.parseString(xml_content)
    except xml.parsers.expat.ExpatError:
        return False

    ft_el = doc.getElementsByTagName("FlightTrack")[0]
    waypoints = ft_el.getElementsByTagName("Waypoint")
    if (len(waypoints)) < 2:
        return False

    for wp_el in ft_el.getElementsByTagName("Waypoint"):
        try:
            wp_el.getAttribute("location")
            float(wp_el.getAttribute("lat"))
            float(wp_el.getAttribute("lon"))
            float(wp_el.getAttribute("flightlevel"))
            wp_el.getElementsByTagName("Comments")[0]
        except ValueError:
            return False

    return True
