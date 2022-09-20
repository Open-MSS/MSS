# -*- coding: utf-8 -*-
"""

    mslib.plugins.io.navaid
    ~~~~~~~~~~~~~~~~~~~~

    plugin for navaid format flight track export

    This file is part of MSS.

    :copyright: Copyright 2022 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
"""
import os
import datetime
import csv
import codecs
import numpy as np
import geomag
from geopy.distance import geodesic
from geographiclib.geodesic import Geodesic
from mslib.msui.constants import MSUI_CONFIG_PATH


def radial_dme(lat, lon, elev=12., test_date=datetime.date.today(), maxdist=250.):
    # Read the list of NAVAIDs
    # PATH needs to be replaced by generic
    navaid_file = os.path.join(MSUI_CONFIG_PATH, 'plugins', 'NAVAID_System.csv')
    navaid = open(navaid_file, encoding='utf-8-sig')
    csvreader = csv.reader(navaid)
    header = next(csvreader)
    ix = header.index('X')
    iy = header.index('Y')
    itype = header.index('TYPE_CODE')
    iident = header.index('IDENT')
    locations = []
    navidents = []
    for row in csvreader:
        # Find the ones that are useful to the pilots (types 6, 7, or 8)
        type_code = int(row[itype])
        if type_code == 6 or type_code == 7 or type_code == 8:
            navlon = float(row[ix])
            navlat = float(row[iy])
            locations.append((navlat, navlon))
            navidents.append(row[iident])

    # Determine nearest NAVAID to the lat/lon point in nautical miles.
    position = (lat, lon)
    dist = [geodesic(position, i).nm for i in locations]
    minpos = dist.index(min(dist))
    navident = navidents[minpos]
    navlat = locations[minpos][0]
    navlon = locations[minpos][1]

    # Calculate the true heading to the nearest NAVAID
    # Uses WGS84 ellipsoid for the earth
    true_bear = Geodesic.WGS84.Inverse(navlat, navlon, lat, lon)['azi1']

    # Convert to magnetic heading (note: elevation converted to feet)
    mag_bear = geomag.mag_heading(true_bear, dlat=lat, dlon=lon,
                                  h=elev * 3280.8399, time=test_date)

    # Round to whole numbers
    az = round(mag_bear)
    rng = round(dist[minpos])

    # Print and return values
    lonx = np.mod((lon + 180), 360) - 180
    hemx = 'E'
    if lonx < 0:
        hemx = 'W'
    hemy = 'N'
    if lat < 0:
        hemy = 'S'

    lonx = np.abs(lonx)
    latx = np.abs(lat)
    latdeg = int(np.floor(latx))
    londeg = int(np.floor(lonx))
    latmin = int(round((latx - np.floor(latx)) * 60.))
    lonmin = int(round((lonx - np.floor(lonx)) * 60.))

    if rng > maxdist:
        wpt_str = '{:02d}{:02d}{}{:03d}{:02d}{}'.format(latdeg, latmin, hemy,
                                                        londeg, lonmin, hemx)
    else:
        wpt_str = '{}{:03d}{:03d}'.format(navident, az, rng)
    if rng <= 1:
        wpt_str = navident
    return wpt_str


def save_to_navaid(filename, name, waypoints):
    maxdist = 250.
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
        out_file.write(
            f"# This file contains NAVAID-DME names for points less than {maxdist:.0f} "
            "nm distance from closest NAVAID point\n")
        out_file.write(f"Track name: {name:}\n")
        line = u"{0:5d}  {1:{2}} {3:11} {4:4.0f}° {5:02.0f}'  {6:4.0f}° {7:02.0f}' {8:7.1f} {9:7.1f}  {10:8.1f}" \
               u"  {11:8.1f}  {12:{13}}\n"
        header = f"Index  {'Location':{max_loc_len}} NAVAID-DME    Lat      Lon      FL (hft) P (hPa)  " \
                 f"Leg (km) Cum. (km)  {'Comments':{max_com_len}}\n"
        out_file.write(header)
        for i, wp in enumerate(waypoints):
            # ToDo check str(str( .. ) and may be use csv write
            loc = str(wp.location)
            lat = wp.lat
            lon = wp.lon
            # transform to degrees and minutes
            latdeg = np.floor(lat)
            if lat < 0:
                latdeg = - np.floor(-lat)
            latmin = abs(round((lat - latdeg) * 60.))

            londeg = np.floor(lon)
            if lon < 0:
                londeg = - np.floor(-lon)
            lonmin = abs(round((lon - londeg) * 60.))

            nav = radial_dme(lat, lon, maxdist=maxdist)
            lvl = wp.flightlevel
            pre = wp.pressure / 100.
            leg = wp.distance_to_prev
            cum = wp.distance_total
            com = str(wp.comments)
            out_file.write(line.format(i, loc, max_loc_len, nav, latdeg, latmin,
                                       londeg, lonmin, lvl, pre, leg, cum, com,
                                       max_com_len))
