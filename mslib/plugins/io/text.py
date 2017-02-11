import logging
import numpy as np

import mslib.msui.flighttrack as ft
from mslib import thermolib


def save_to_txt(filename, name, waypoints):
    if not filename:
        raise ValueError("filename to save flight track cannot be None")
    max_loc_len, max_com_len = len("Location"), len("Comments")
    for wp in waypoints:
        if len(unicode(wp.location)) > max_loc_len:
            max_loc_len = len(unicode(wp.location))
        if len(unicode(wp.comments)) > max_com_len:
            max_com_len = len(unicode(wp.comments))
    with open(filename, "w") as out_file:
        out_file.write("# Do not modify if you plan to import this file again!\n")
        out_file.write("Track name: {:}\n".format(name.encode("ascii", "replace")))
        line = "{0:5d}  {1:{2}}  {3:10.3f}  {4:11.3f}  {5:11.3f}  {6:14.3f}  {7:14.1f}  {8:15.1f}  {9:{10}}\n"
        header = "Index  {0:{1}}  Lat (+-90)  Lon (+-180)  Flightlevel  Pressure (hPa)  " \
                 "Leg dist. (km)  Cum. dist. (km)  {2:{3}}\n".format("Location", max_loc_len, "Comments",
                                                                     max_com_len)
        out_file.write(header)
        for i, wp in enumerate(waypoints):
            loc = unicode(wp.location).encode("ascii", "replace")
            lat = wp.lat
            lon = wp.lon
            lvl = wp.flightlevel
            pre = wp.pressure / 100.
            leg = wp.distance_to_prev
            cum = wp.distance_total
            com = unicode(wp.comments).encode("ascii", "replace")
            out_file.write(line.format(i, loc, max_loc_len, lat, lon, lvl, pre, leg, cum, com, max_com_len))


def load_from_txt(filename):
    name = ""
    waypoints = []
    with open(filename, "r") as in_file:
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
                name = line.split(':')[1].strip()
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
            for i in xrange(2, len(pos) - 1):
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
