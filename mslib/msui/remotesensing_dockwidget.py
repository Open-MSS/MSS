# -*- coding: utf-8 -*-
"""

    mslib.msui.remotesensing_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control widget to configure remote sensing overlays.

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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


import numpy as np
from mslib.msui.mss_qt import QtGui, QtWidgets
from mslib.msui.mss_qt import ui_remotesensing_dockwidget as ui
from mslib.utils import datetime_to_jsec, get_distance, rotate_point, fix_angle, compute_hour_of_day
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
import collections


EARTH_RADIUS = 6371.


def compute_view_angles(lon0, lat0, h0, lon1, lat1, h1, angle):
    mlat = ((lat0 + lat1) / 2.)
    lon0 *= np.cos(np.deg2rad(mlat))
    lon1 *= np.cos(np.deg2rad(mlat))
    dlon = lon1 - lon0
    dlat = lat1 - lat0
    obs_azi2 = fix_angle(angle + np.rad2deg(np.arctan2(dlon, dlat)))
    return obs_azi2, -1


def compute_solar_angle(jsec, lon, lat):
    # The input to the Astronomer's almanach is the difference between
    # the Julian date and JD 2451545.0 (noon, 1 January 2000)
    time = (jsec / (60. * 60. * 24.)) - 0.5

    # Mean longitude
    mnlong = 280.460 + .9856474 * time
    mnlong %= 360.
    if mnlong < 0:
        mnlong += 360
        assert mnlong >= 0

    # Mean anomaly
    mnanom = 357.528 + .9856003 * time
    mnanom = np.deg2rad(mnanom % 360.)
    if mnanom < 0:
        mnanom += 2 * np.pi
        assert mnanom >= 0

    # Ecliptic longitude and obliquity of ecliptic
    eclong = mnlong + 1.915 * np.sin(mnanom) + 0.020 * np.sin(2 * mnanom)
    eclong = np.deg2rad(eclong % 360.)
    if (eclong < 0):
        eclong += 2 * np.pi
        assert (eclong >= 0)

    oblqec = np.deg2rad(23.439 - 0.0000004 * time)

    # Celestial coordinates
    # Right ascension and declination
    num = np.cos(oblqec) * np.sin(eclong)
    den = np.cos(eclong)
    ra = np.arctan(num / den)
    if den < 0:
        ra += np.pi
    elif den >= 0 and num < 0:
        ra += 2 * np.pi

    dec = np.arcsin(np.sin(oblqec) * np.sin(eclong))
    # Local coordinates
    # Greenwich mean sidereal time
    gmst = 6.697375 + .0657098242 * time + compute_hour_of_day(jsec)

    gmst = gmst % 24.
    if gmst < 0:
        gmst += 24
        assert gmst >= 0

    # Local mean sidereal time
    if lon < 0:
        lon += 360
        assert 0 <= lon <= 360

    lmst = gmst + (lon / 15.)
    lmst = np.deg2rad(15. * (lmst % 24.))

    # Hour angle
    ha = lmst - ra
    if ha < -np.pi:
        ha += 2 * np.pi

    if ha > np.pi:
        ha -= 2 * np.pi

    assert -np.pi < ha < 2 * np.pi

    # Latitude to radians
    lat = np.deg2rad(lat)

    # Azimuth and elevation
    zenithAngle = np.arccos(np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(ha))
    azimuthAngle = np.arccos(((np.sin(lat) * np.cos(zenithAngle) - np.sin(dec)) /
                             (np.cos(lat) * np.sin(zenithAngle))))

    if ha > 0:
        azimuthAngle += np.pi
    else:
        azimuthAngle = 3 * np.pi - azimuthAngle % (2 * np.pi)

    if azimuthAngle > np.pi:
        azimuthAngle -= 2 * np.pi

    return np.rad2deg(azimuthAngle), 90 - np.rad2deg(zenithAngle)


class RemoteSensingControlWidget(QtWidgets.QWidget, ui.Ui_RemoteSensingDockWidget):
    """This class implements the remote sensing functionality as dockable widget.
    """

    def __init__(self, parent=None, view=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        view -- reference to mpl canvas class
        """
        super(RemoteSensingControlWidget, self).__init__(parent)
        self.setupUi(self)

        self.view = view

        button = self.btTangentsColour
        palette = QtGui.QPalette(button.palette())
        colour = QtGui.QColor()
        colour.setRgbF(1, 0, 0, 1)
        palette.setColor(QtGui.QPalette.Button, colour)
        button.setPalette(palette)

        self.dsbTangentHeight.setValue(10.)
        self.dsbObsAngle.setValue(90.)

        # update plot on every value change
        self.cbDrawTangents.stateChanged.connect(self.update_settings)
        self.cbShowSolarAngle.stateChanged.connect(self.update_settings)
        self.btTangentsColour.clicked.connect(self.set_tangentpoint_colour)
        self.dsbTangentHeight.valueChanged.connect(self.update_settings)
        self.dsbObsAngle.valueChanged.connect(self.update_settings)

        self.solar_cmap = ListedColormap([
            (1.0, 0.0, 0.0, 1.0),
            (1.0, 0.44823529411764707, 0.0, 1.0),
            (1.0, 0.75, 0.0, 1.0),
            (0.46999999999999997, 0.10000000000000001, 1.0, 1.0),
            (0.64666666666666672, 0.25, 1.0, 1.0),
            (0.82333333333333336, 0.40000000000000002, 1.0, 1.0),
            (1.0, 0.55000000000000004, 1.0, 1.0),
            (0.65000000000000002, 1.0, 0.65000000000000002, 1.0),
            (0.32372549019607844, 0.84941176470588231, 0.32372549019607844, 1.0),
            (0.0, 0.69999999999999996, 0.0, 1.0)])
        self.solar_norm = BoundaryNorm([0, 5, 10, 15, 25, 35, 45, 60, 90, 135, 180], self.solar_cmap.N)

        self.update_settings()

    def update_settings(self):
        """
        Updates settings in TopView and triggers a redraw.
        """
        settings = {
            "reference": self,
            "draw_tangents": self.cbDrawTangents.isChecked(),
            "show_solar_angle": self.cbShowSolarAngle.isChecked(),
        }
        self.view.set_remote_sensing_appearance(settings)

    def set_tangentpoint_colour(self):
        """Slot for the colour buttons: Opens a QColorDialog and sets the
           new button face colour.
        """
        button = self.btTangentsColour
        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)
        self.update_settings()

    def compute_tangent_lines(self, bmap, wp_vertices, wp_heights):
        """
        Computes Tangent points of limb sounders aboard the aircraft

        Args:
            bmap: Projection of TopView
            wp_vertices: waypoints of the flight path
            wp_heights: altitude of the waypoints of flight path

        Returns: LineCollection of dotted lines at tangent point locations
        """
        x, y = list(zip(*wp_vertices))
        wp_lons, wp_lats = bmap(x, y, inverse=True)
        fine_lines = [bmap.gcpoints2(
                      wp_lons[i], wp_lats[i], wp_lons[i + 1], wp_lats[i + 1], del_s=10., map_coords=False)
                      for i in range(len(wp_lons) - 1)]
        line_heights = [np.linspace(wp_heights[i], wp_heights[i + 1], num=len(fine_lines[i][0]))
                        for i in range(len(fine_lines))]
        # fine_lines = list of tuples with x-list and y-list for each segment
        tplines = [self.tangent_point_coordinates(
            fine_lines[i][0], fine_lines[i][1], line_heights[i],
            cut_height=self.dsbTangentHeight.value()) for i in range(len(fine_lines))]
        dirlines = self.direction_coordinates(wp_lons, wp_lats)
        lines = tplines + dirlines
        for i, line in enumerate(lines):
            for j, (lon, lat) in enumerate(line):
                line[j] = bmap(lon, lat)
            lines[i] = line
        return LineCollection(
            lines,
            colors=QtGui.QPalette(self.btTangentsColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            zorder=2, animated=True, linewidth=3, linestyles=[':'] * len(tplines) + ['-'] * len(dirlines))

    def compute_solar_lines(self, bmap, wp_vertices, wp_heights, wp_times):
        """
        Computes coloured overlay over the flight path that indicates
        the danger of looking into the sun with a limb sounder aboard
        the aircraft.

        Args:
            bmap: Projection of TopView
            wp_vertices: waypoints of the flight path
            wp_heights: altitude of the waypoints of flight path

        Returns: LineCollection of coloured lines according to the
                 angular distance between viewing direction and solar
                 angle
        """
        # calculate distances and times
        times = [datetime_to_jsec(_wp_time) for _wp_time in wp_times]
        x, y = list(zip(*wp_vertices))
        wp_lons, wp_lats = bmap(x, y, inverse=True)

        fine_lines = [bmap.gcpoints2(wp_lons[i], wp_lats[i], wp_lons[i + 1], wp_lats[i + 1], map_coords=False) for i in
                      range(len(wp_lons) - 1)]
        line_heights = [np.linspace(wp_heights[i], wp_heights[i + 1], num=len(fine_lines[i][0])) for i in
                        range(len(fine_lines))]
        line_times = [np.linspace(times[i], times[i + 1], num=len(fine_lines[i][0])) for i in
                      range(len(fine_lines))]
        # fine_lines = list of tuples with x-list and y-list for each segment
        # lines = list of tuples with lon-list and lat-list for each segment
        heights = []
        times = []
        for i in range(len(fine_lines) - 1):
            heights.extend(line_heights[i][:-1])
            times.extend(line_times[i][:-1])
        heights.extend(line_heights[-1])
        times.extend(line_times[-1])
        solar_x = []
        solar_y = []
        for i in range(len(fine_lines) - 1):
            solar_x.extend(fine_lines[i][0][:-1])
            solar_y.extend(fine_lines[i][1][:-1])
        solar_x.extend(fine_lines[-1][0])
        solar_y.extend(fine_lines[-1][1])
        points = []
        old_wp = None
        total_distance = 0
        for i, (lon, lat) in enumerate(zip(solar_x, solar_y)):
            points.append([[lon, lat]])  # append double-list for later concatenation
            if old_wp is not None:
                wp_dist = get_distance((old_wp[0], old_wp[1]), (lat, lon)) * 1000.
                total_distance += wp_dist
            old_wp = (lat, lon)
        vals = []
        for i in range(len(points) - 1):
            p0, p1 = points[i][0], points[i + 1][0]
            sol_azi, sol_ele = compute_solar_angle(times[i], p0[0], p0[1])
            if sol_azi < 0:
                sol_azi += 360
            obs_azi, obs_ele = compute_view_angles(p0[0], p0[1], heights[i], p1[0], p1[1], heights[i + 1],
                                                   self.dsbObsAngle.value())
            if obs_azi < 0:
                obs_azi += 360
            rating = self.calc_view_rating(obs_azi, obs_ele, sol_azi, sol_ele, heights[i])
            vals.append(rating)

        # convert lon, lat to map points
        for i in range(len(points)):
            points[i][0][0], points[i][0][1] = bmap(points[i][0][0], points[i][0][1])
        points = np.concatenate([points[:-1], points[1:]], axis=1)
        # plot
        solar_lines = LineCollection(points, cmap=self.solar_cmap, norm=self.solar_norm,
                                     zorder=2, linewidths=3, animated=True)
        solar_lines.set_array(np.array(vals))
        return solar_lines

    def tangent_point_coordinates(self, lon_lin, lat_lin, flight_alt=14, cut_height=12):
        """
        Computes coordinates of tangent points given coordinates of flight path.

        Args:
            lon_lin: longitudes of flight path
            lat_lin: latitudes of flight path
            flight_alt: altitude of aircraft (scalar or numpy array)
            cut_height: altitude of tangent points

        Returns: List of tuples of longitude/latitude coordinates

        """
        lins = list(zip(lon_lin[0:-1], lon_lin[1:], lat_lin[0:-1], lat_lin[1:]))
        lins = [(x0 * np.cos(np.deg2rad(np.mean([y0, y1]))), x1 * np.cos(np.deg2rad(np.mean([y0, y1]))), y0, y1)
                for x0, x1, y0, y1 in lins]

        direction = [(x1 - x0, y1 - y0) for x0, x1, y0, y1 in lins]
        direction = [(_x / np.hypot(_x, _y), _y / np.hypot(_x, _y))
                     for _x, _y in direction]
        los = [rotate_point(point, -self.dsbObsAngle.value()) for point in direction]
        los.append(los[-1])

        if isinstance(flight_alt, (collections.Sequence, np.ndarray)):
            dist = [(np.sqrt(max((EARTH_RADIUS + a) ** 2 - (EARTH_RADIUS + cut_height) ** 2, 0)) / 110.)
                    for a in flight_alt[:-1]]
            dist.append(dist[-1])
        else:
            dist = (np.sqrt((EARTH_RADIUS + flight_alt) ** 2 - (EARTH_RADIUS + cut_height) ** 2) / 110.)

        tp_dir = (np.array(los).T * dist).T

        tps = [(x0 + tp_x, y0 + tp_y) for
               ((x0, x1, y0, y1), (tp_x, tp_y)) in zip(lins, tp_dir)]
        tps = [(x0 / np.cos(np.deg2rad(y0)), y0) for (x0, y0) in tps]
        return tps

    def direction_coordinates(self, lon_lin, lat_lin):
        """
        Computes coordinates of tangent points given coordinates of flight path.

        Args:
            lon_lin: longitudes of flight path
            lat_lin: latitudes of flight path
            flight_alt: altitude of aircraft (scalar or numpy array)
            cut_height: altitude of tangent points

        Returns: List of tuples of longitude/latitude coordinates

        """
        lins = list(zip(lon_lin[0:-1], lon_lin[1:], lat_lin[0:-1], lat_lin[1:]))
        lins = [(x0 * np.cos(np.deg2rad(np.mean([y0, y1]))), x1 * np.cos(np.deg2rad(np.mean([y0, y1]))), y0, y1)
                for x0, x1, y0, y1 in lins]

        direction = [(0.5 * (x0 + x1), 0.5 * (y0 + y1), x1 - x0, y1 - y0) for x0, x1, y0, y1 in lins]
        direction = [(_u, _v, _x / np.hypot(_x, _y), _y / np.hypot(_x, _y))
                     for _u, _v, _x, _y in direction]
        los = [rotate_point(point[2:], -self.dsbObsAngle.value()) for point in direction]

        dist = 1.

        tp_dir = (np.array(los).T * dist).T

        tps = [(x0, y0, x0 + tp_x, y0 + tp_y) for
               ((x0, y0, _, _), (tp_x, tp_y)) in zip(direction, tp_dir)]
        tps = [[(x0 / np.cos(np.deg2rad(y0)), y0), (x1 / np.cos(np.deg2rad(y0)), y1)] for (x0, y0, x1, y1) in tps]
        return tps

    @staticmethod
    def calc_view_rating(obs_azi, obs_ele, sol_azi, sol_ele, height):
        """
        Calculates the angular distance between given directions under the
        condition that the sun is above the horizon.

        Args:
            obs_azi: observator azimuth angle
            obs_ele: observator elevation angle
            sol_azi: solar azimuth angle
            sol_ele: solar elevation angle
            height: altitude of observer

        Returns: angular distance or 180 degrees if sun is below horizon
        """
        thresh = -np.rad2deg(np.arccos(EARTH_RADIUS / (height + EARTH_RADIUS))) - 3

        delta_azi = obs_azi - sol_azi
        delta_ele = obs_ele + sol_ele
        if sol_ele < thresh:
            delta_ele = 180
        return np.linalg.norm([delta_azi, delta_ele])
