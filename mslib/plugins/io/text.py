# -*- coding: utf-8 -*-
"""

    mslib.plugins.io.text
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    plugin for text format flight track export

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2018 by the mss team, see AUTHORS.
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

from __future__ import division

from builtins import str

import logging
import codecs
import mslib.msui.flighttrack as ft
from mslib import thermolib
import os
from fs import open_fs


def save_to_txt(filename, name, waypoints):
    if not filename:
        raise ValueError("filename to save flight track cannot be None")
    max_loc_len, max_com_len = len("Location"), len("Comments")
    for wp in waypoints:
        if len(str(wp.location)) > max_loc_len:
            max_loc_len = len(str(wp.location))
        if len(str(wp.comments)) > max_com_len:
            max_com_len = len(str(wp.comments))
    with codecs.open(filename, "w", encoding="utf-8") as out_file:
        out_file.write(u"# Do not modify if you plan to import this file again!\n")
        out_file.write(u"Track name: {:}\n".format(name))
        line = u"{0:5d}  {1:{2}}  {3:10.3f}  {4:11.3f}  {5:11.3f}  {6:14.3f}  {7:14.1f}  {8:15.1f}  {9:{10}}\n"
        header = u"Index  {0:{1}}  Lat (+-90)  Lon (+-180)  Flightlevel  Pressure (hPa)  " \
                 u"Leg dist. (km)  Cum. dist. (km)  {2:{3}}\n".format(
                     "Location", max_loc_len, "Comments", max_com_len)
        out_file.write(header)
        for i, wp in enumerate(waypoints):
            # ToDo check str(str( .. ) and may be use csv write
            loc = str(wp.location)
            lat = wp.lat
            lon = wp.lon
            lvl = wp.flightlevel
            pre = wp.pressure / 100.
            leg = wp.distance_to_prev
            cum = wp.distance_total
            com = str(wp.comments)
            out_file.write(line.format(i, loc, max_loc_len, lat, lon, lvl, pre, leg, cum, com, max_com_len))


def load_from_txt(filename):
    name = os.path.basename(filename.replace(".txt", "").strip())
    waypoints = []
    _dirname, _name = os.path.split(filename)
    _fs = open_fs(_dirname)
    with _fs.open(_name, "r") as in_file:
        pos = []
        for line in in_file:
            if line.startswith("#"):
                continue
            if line.startswith("Index"):
                pos.append(0)  # 0
                pos.append(line.find("Location"))  # 1
                pos.append(line.find("Lat (+-90)"))  # 2
                pos.append(line.find("Lon (+-180)"))  # 3
                pos.append(line.find("Flightlevel"))  # 4
                pos.append(line.find("Pressure (hPa)"))  # 5
                pos.append(line.find("Leg dist. (km)"))  # 6
                pos.append(line.find("Cum. dist. (km)"))  # 7
                pos.append(line.find("Comments"))  # 8
                continue
            if line.startswith("Track name: "):
                continue

            if len(pos) == 0:
                raise SyntaxError("TXT Import could not parse column headings.")
            if len(line) < max(pos):
                raise SyntaxError("TXT Import could not parse line: '{}'".format(line))

            wp = ft.Waypoint()
            attr_names = ["location", "lat", "lon", "flightlevel",
                          "pressure", "distance_to_prev", "distance_total",
                          "comments"]
            setattr(wp, attr_names[0], line[pos[1]:pos[2]].strip())
            setattr(wp, attr_names[7], line[pos[8]:].strip())
            for i in range(2, len(pos) - 1):
                if pos[i] >= 0:
                    if i == 5:
                        setattr(wp, attr_names[i - 1],
                                float(line[pos[i]:pos[i + 1]].strip()) * 100.)
                    else:
                        setattr(wp, attr_names[i - 1],
                                float(line[pos[i]:pos[i + 1]].strip()))
                else:
                    if i == 5:
                        logging.debug('calculate pressure from FL ' + str(
                            thermolib.flightlevel2pressure(float(wp.flightlevel))))
                        setattr(wp, attr_names[i - 1],
                                thermolib.flightlevel2pressure(float(wp.flightlevel)))
            waypoints.append(wp)
    return name, waypoints
