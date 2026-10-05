# -*- coding: utf-8 -*-
"""

    mslib.plugins.io.csv
    ~~~~~~~~~~~~~~~~~~~~

    plugin for csv format flight track export

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

import unicodecsv as csv
import os
from pathlib import Path

import mslib.msui.flighttrack as ft

# a cell that starts with one of these is a formula in spreadsheet programs, e.g. =HYPERLINK(...)
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def _spreadsheet_text(text):
    """
    text for a text cell: a "'" is put in front of text a spreadsheet program would run as a formula

    The names and comments of the flight track and its waypoints can be chosen by collaborators. Text that starts
    with "'"s before a formula character gets one more, so _from_spreadsheet_text gives every text back as it was.
    """
    text = str(text)
    return "'" + text if text.lstrip("'").startswith(_FORMULA_STARTS) else text


def _from_spreadsheet_text(text):
    """
    The text of a text cell written by _spreadsheet_text
    """
    return text[1:] if text.startswith("'") and text.lstrip("'").startswith(_FORMULA_STARTS) else text


def save_to_csv(filename, name, waypoints):
    if not filename:
        raise ValueError("fileexportname to save flight track cannot be None")
    path = Path(filename)
    with path.open("wb") as csvfile:
        csv_writer = csv.writer(csvfile, dialect='excel', delimiter=";", lineterminator="\n")
        csv_writer.writerow([_spreadsheet_text(name)])
        csv_writer.writerow(["Index", "Location", "Lat (+-90)", "Lon (+-180)", "Flightlevel", "Pressure (hPa)",
                             "Leg dist. (km)", "Cum. dist. (km)", "Comments"])
        for i, wp in enumerate(waypoints):
            loc = _spreadsheet_text(wp.location)
            lat = f"{wp.lat:.3f}"
            lon = f"{wp.lon:.3f}"
            lvl = f"{wp.flightlevel:.3f}"
            pre = f"{wp.pressure / 100.:.3f}"
            leg = f"{wp.distance_to_prev:.3f}"
            cum = f"{wp.distance_total:.3f}"
            com = _spreadsheet_text(wp.comments)
            csv_writer.writerow([i, loc, lat, lon, lvl, pre, leg, cum, com])


def load_from_csv(filename):
    waypoints = []
    path = Path(filename)
    with path.open("rb") as in_file:
        lines = in_file.readlines()
    if len(lines) < 4:
        raise SyntaxError("CSV file requires at least 4 lines!")
    dialect = csv.Sniffer().sniff(lines[-1].decode("utf-8"))
    # save_to_csv quotes like Excel, a quote in a text is doubled; the last line may have no quote to tell
    dialect.doublequote = True
    csv_reader = csv.reader(lines, encoding="utf-8", dialect=dialect)
    name = next(csv_reader)[0]
    next(csv_reader)  # header
    for row in csv_reader:
        wp = ft.Waypoint()
        wp.location = _from_spreadsheet_text(row[1])
        wp.lat = float(row[2])
        wp.lon = float(row[3])
        wp.flightlevel = float(row[4])
        wp.pressure = float(row[5]) * 100.
        wp.distance_to_prev = float(row[6])
        wp.distance_total = float(row[7])
        wp.comments = _from_spreadsheet_text(row[8])
        waypoints.append(wp)
    name = os.path.basename(filename.replace(".csv", "").strip())
    return name, waypoints
