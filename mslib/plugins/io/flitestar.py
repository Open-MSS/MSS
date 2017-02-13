import numpy as np
import os

import mslib.msui.flighttrack as ft
from mslib import thermolib


def load_from_flitestar(filename):
    waypoints = []

    with open(filename, 'r') as f:
        firstline = f.readline()
        if not firstline.startswith("# FliteStar/FliteMap generated flight plan."):
            raise SyntaxError("The file does not seem to be a FliteStar file!")
        for line in f:

            if line.startswith('FWP'):
                line = line.split()
                if len(line) < 10:
                    raise SyntaxError("Line {} has less than 9 fields.".format(line))
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

                wp = ft.Waypoint()
                wp.location = line[3]
                wp.lat = float(lat)
                wp.lon = float(lon)
                wp.flightlevel = float(alt)
                wp.pressure = thermolib.flightlevel2pressure(float(wp.flightlevel))
                waypoints.append(wp)

    name = os.path.basename(filename).strip('.txt')
    return name, waypoints
