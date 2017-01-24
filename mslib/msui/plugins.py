import csv
import mslib.msui.flighttrack as ft
import logging
import numpy as np
from mslib import thermolib


def saveToCSV(filename, name, waypoints):
    if not filename:
        raise ValueError("filename to save flight track cannot be None")
    with open(filename, "w") as out_file:
        csv_writer = csv.writer(out_file, dialect='excel', delimiter=";", lineterminator="\n")
        csv_writer.writerow([name])
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


def loadFromCSV(filename):
    waypoints = []
    with open(filename, "r") as in_file:
        lines = in_file.readlines()
    dialect = csv.Sniffer().sniff(lines[-1])
    csv_reader = csv.reader(lines, dialect=dialect)
    name = csv_reader.next()[0]
    csv_reader.next()  # header
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
    return name, waypoints


def saveToFliteStarText(filename, name, waypoints):
    if not filename:
        raise ValueError("filename to save flight track cannot be None")
    max_loc_len, max_com_len = len("Location"), len("Comments")
    for wp in waypoints:
        if len(str(wp.location)) > max_loc_len:
            max_loc_len = len(str(wp.location))
        if len(str(wp.comments)) > max_com_len:
            max_com_len = len(str(wp.comments))
    with open(filename, "w") as out_file:
        out_file.write("# Do not modify if you plan to import this file again!\n")
        out_file.write("Track name: {:}\n".format(name))
        line = "{0:5d}  {1:{2}}  {3:10.3f}  {4:11.3f}  {5:11.3f}  {6:14.3f}  {7:14.1f}  {8:15.1f}  {9:{10}}\n"
        header = "Index  {0:{1}}  Lat (+-90)  Lon (+-180)  Flightlevel  Pressure (hPa)  " \
                 "Leg dist. (km)  Cum. dist. (km)  {2:{3}}\n".format("Location", max_loc_len, "Comments",
                                                                     max_com_len)
        out_file.write(header)
        for i, wp in enumerate(waypoints):
            loc = str(wp.location)
            lat = wp.lat
            lon = wp.lon
            lvl = wp.flightlevel
            pre = wp.pressure / 100.
            leg = wp.distance_to_prev
            cum = wp.distance_total
            com = str(wp.comments)
            out_file.write(line.format(i, loc, max_loc_len, lat, lon, lvl, pre, leg, cum, com, max_com_len))


def loadFromFliteStarText(filename):
    name = ""

    def loadFXtxt(filename_p):
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
        data = loadFXtxt(filename)
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
