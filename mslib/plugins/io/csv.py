# -*- coding: utf-8 -*-
"""

    mslib.plugins.io.csv
    ~~~~~~~~~~~~~~~~~~~~

    plugin for csv format flight track export

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
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

from __future__ import absolute_import
from __future__ import division

from builtins import str

import unicodecsv as csv
import os

import mslib.msui.flighttrack as ft


def save_to_csv(filename, name, waypoints):
    if not filename:
        raise ValueError("filename to save flight track cannot be None")
    with open(filename, "w") as out_file:
        csv_writer = csv.writer(out_file, encoding="utf-8", dialect='excel', delimiter=";", lineterminator="\n")
        csv_writer.writerow([str(name)])
        csv_writer.writerow(["Index", "Location", "Lat (+-90)", "Lon (+-180)", "Flightlevel", "Pressure (hPa)",
                             "Leg dist. (km)", "Cum. dist. (km)", "Comments"])
        for i, wp in enumerate(waypoints):
            loc = str(wp.location)
            lat = "{:.3f}".format(wp.lat)
            lon = "{:.3f}".format(wp.lon)
            lvl = "{:.3f}".format(wp.flightlevel)
            pre = "{:.3f}".format(wp.pressure / 100.)
            leg = "{:.3f}".format(wp.distance_to_prev)
            cum = "{:.3f}".format(wp.distance_total)
            com = str(wp.comments)
            csv_writer.writerow([i, loc, lat, lon, lvl, pre, leg, cum, com])


def load_from_csv(filename):
    waypoints = []
    with open(filename, "r") as in_file:
        lines = in_file.readlines()
    if len(lines) < 4:
        raise SyntaxError("CSV file requires at least 4 lines!")
    dialect = csv.Sniffer().sniff(lines[-1])
    csv_reader = csv.reader(lines, encoding="utf-8", dialect=dialect)
    name = next(csv_reader)[0]
    next(csv_reader)  # header
    for row in csv_reader:
        wp = ft.Waypoint()
        wp.location = row[1]
        wp.lat = float(row[2])
        wp.lon = float(row[3])
        wp.flightlevel = float(row[4])
        wp.pressure = float(row[5]) * 100.
        wp.distance_to_prev = float(row[6])
        wp.distance_total = float(row[7])
        wp.comments = row[8]
        waypoints.append(wp)
    name = os.path.basename(filename.replace(".csv", "").strip())
    return name, waypoints
