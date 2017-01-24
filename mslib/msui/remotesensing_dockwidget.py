"""Control widget to configure remote sensing overlays.


This file is part of the Mission Support System User Interface (MSUI).

AUTHORS:
========

* Joern Ungermann

"""

import numpy as np
from PyQt4 import QtGui, QtCore  # Qt4 bindings
from mslib.msui import ui_remotesensing_dockwidget as ui
from mslib.mss_util import datetime_to_jsec, compute_solar_angle, \
    compute_view_angles, get_distance, rotate_point
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
import collections


R = 6371.


class RemoteSensingControlWidget(QtGui.QWidget, ui.Ui_RemoteSensingDockWidget):
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
        self.connect(self.btTangentsColour, QtCore.SIGNAL("clicked()"),
                     self.set_tangentpoint_colour)
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
        self.view.setRemoteSensingAppearance(settings)

    def set_tangentpoint_colour(self):
        """Slot for the colour buttons: Opens a QColorDialog and sets the
           new button face colour.
        """
        button = self.btTangentsColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtGui.QColorDialog.getColor(colour)
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
        x, y = zip(*wp_vertices)
        wp_lons, wp_lats = bmap(x, y, inverse=True)
        fine_lines = [bmap.gcpoints2(wp_lons[i], wp_lats[i], wp_lons[i + 1], wp_lats[i + 1], del_s=10.,
                                     map_coords=False) for i in range(len(wp_lons) - 1)]
        line_heights = [np.linspace(wp_heights[i], wp_heights[i + 1], num=len(fine_lines[i][0]))
                        for i in range(len(fine_lines))]
        # fine_lines = list of tuples with x-list and y-list for each segment
        tplines = [self.tangent_point_coordinates(
            fine_lines[i][0], fine_lines[i][1], line_heights[i],
            cut_height=self.dsbTangentHeight.value()) for i in range(len(fine_lines))]
        for i in range(len(tplines)):
            l = tplines[i]
            for j in range(len(l)):
                l[j] = bmap(l[j][0], l[j][1])
            tplines[i] = l
        return LineCollection(
            tplines,
            colors=QtGui.QPalette(self.btTangentsColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            zorder=2, animated=True, linewidth=3, linestyles=':')

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
        speed = 850. / 3.6  # speed in km/s
        times = [datetime_to_jsec(_wp_time) for _wp_time in wp_times]
        x, y = zip(*wp_vertices)
        wp_lons, wp_lats = bmap(x, y, inverse=True)
        fine_lines = [bmap.gcpoints2(wp_lons[i], wp_lats[i], wp_lons[i + 1], wp_lats[i + 1]) for i in
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
        for i in range(len(solar_x)):
            lon, lat = solar_x[i], solar_y[i]
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
        lon_lin2 = np.array(lon_lin) * np.cos(np.deg2rad(np.array(lat_lin)))
        lins = zip(lon_lin2[0:-1], lon_lin2[1:], lat_lin[0:-1], lat_lin[1:])
        direction = [(x1 - x0, y1 - y0) for x0, x1, y0, y1 in lins]
        direction = [(_x / np.hypot(_x, _y), _y / np.hypot(_x, _y))
                     for _x, _y in direction]
        los = [rotate_point(point, -self.dsbObsAngle.value()) for point in direction]
        los.append(los[-1])

        if isinstance(flight_alt, (collections.Sequence, np.ndarray)):
            dist = [np.sqrt(max((R + a) ** 2 - (R + cut_height) ** 2, 0)) / 110. for a in flight_alt[:-1]]
            dist.append(dist[-1])
        else:
            dist = np.sqrt((R + flight_alt) ** 2 - (R + cut_height) ** 2) / 110.

        tp_dir = (np.array(los).T * dist).T

        tps = [(x0 + tp_x, y0 + tp_y) for
               ((x0, x1, y0, y1), (tp_x, tp_y)) in zip(lins, tp_dir)]
        tps = [(x0 / np.cos(np.deg2rad(y0)), y0) for
               (x0, y0) in tps]
        return tps

    def calc_view_rating(self, obs_azi, obs_ele, sol_azi, sol_ele, height):
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
        thresh = -np.rad2deg(np.arccos(R / (height + R))) - 3

        delta_azi = obs_azi - sol_azi
        delta_ele = obs_ele + sol_ele
        if sol_ele < thresh:
            delta_ele = 180
        return np.linalg.norm([delta_azi, delta_ele])
