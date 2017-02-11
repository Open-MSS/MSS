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
        out_file.write("Track name: {:}\n".format(name))
        line = "{0:5d}  {1:{2}}  {3:10.3f}  {4:11.3f}  {5:11.3f}  {6:14.3f}  {7:14.1f}  {8:15.1f}  {9:{10}}\n"
        header = "Index  {0:{1}}  Lat (+-90)  Lon (+-180)  Flightlevel  Pressure (hPa)  " \
                 "Leg dist. (km)  Cum. dist. (km)  {2:{3}}\n".format("Location", max_loc_len, "Comments",
                                                                     max_com_len)
        out_file.write(header)
        for i, wp in enumerate(waypoints):
            loc = unicode(wp.location)
            lat = wp.lat
            lon = wp.lon
            lvl = wp.flightlevel
            pre = wp.pressure / 100.
            leg = wp.distance_to_prev
            cum = wp.distance_total
            com = unicode(wp.comments)
            out_file.write(line.format(i, loc, max_loc_len, lat, lon, lvl, pre, leg, cum, com, max_com_len))


def load_from_txt(filename):
    name = ""

    def load_fx_txt(filename_p):
        with open(filename_p, 'r') as f:
            lines = f.readlines()

        data = {
            'name': [],
            'loc': [],
        }
        for line in lines:
            if line.startswith('FWP'):
                line = line.split()
                data['name'].append(line[3])
                alt = round(float(line[-1]) / 100., 2)
                if line[4] == 'N':
                    NS = 1.
                elif line[4] == 'S':
                    NS = -1.
                else:
                    NS = np.nan
                lat = round((float(line[5]) + float(line[6]) / 60.) * NS, 2)
                if line[7] == 'E':
                    EW = 1.
                elif line[7] == 'W':
                    EW = -1.
                else:
                    EW = np.nan
                lon = round((float(line[8]) + float(line[9]) / 60.) * EW, 2)
                data['loc'].append((lat, lon, alt))
        data['loc'] = np.array(data['loc'])
        return data

    waypoints_list = []
    with open(filename, "r") as in_file:
        firstline = in_file.readline()
    if firstline.startswith("# FliteStar/FliteMap generated flight plan."):
        data = load_fx_txt(filename)
        for n, l in zip(data['name'], data['loc']):
            wp = ft.Waypoint()
            wp.location = n
            setattr(wp, "lat", float(l[0]))
            setattr(wp, "lon", float(l[1]))
            setattr(wp, "flightlevel", float(l[2]))
            wp.pressure = thermolib.flightlevel2pressure(float(wp.flightlevel))
            waypoints_list.append(wp)
        name = filename.split('/')[-1].strip('.txt')

    else:
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
                if pos == {}:
                    logging.error("ERROR")
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
                waypoints_list.append(wp)
    return name, waypoints_list
