# -*- coding: utf-8 -*-
"""

    mslib.plugins.io.kml
    ~~~~~~~~~~~~~~~~~~~~

    plugin for KML format flight track export

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

import codecs


def save_to_kml(filename, name, waypoints):
    if not filename:
        raise ValueError("filename to save flight track cannot be None")
    with codecs.open(filename, "w", "utf_8") as out_file:
        header = """<?xml version="1.0" encoding="UTF-8" ?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
<name>{name}</name>
<open>1</open>
<description>MSS flight track export</description>
<Style id="flighttrack">
<LineStyle><color>ff000000</color><width>4</width></LineStyle><PolyStyle><color>FFF87217</color></PolyStyle></Style>
<Placemark><name>{name}</name>
<styleUrl>#flighttrack</styleUrl>
<LineString>
<tessellate>1</tessellate><altitudeMode>absolute</altitudeMode>
<coordinates>
""".format(name=name)
        line = "{lon:.3f},{lat:.3f},{alt:.3f}\n"
        footer = """</coordinates>
</LineString></Placemark>
</Document>
</kml>"""
        out_file.write(header)
        for i, wp in enumerate(waypoints):
            lat = wp.lat
            lon = wp.lon
            lvl = wp.flightlevel
            alt = lvl * 100 * 0.3048
            out_file.write(line.format(lon=lon, lat=lat, alt=alt))
        out_file.write(footer)
