from __future__ import absolute_import
import csv
import mslib.msui.flighttrack as ft


def save_to_csv(filename, name, waypoints):
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


def load_from_csv(filename):
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
