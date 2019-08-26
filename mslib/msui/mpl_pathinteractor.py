# -*- coding: utf-8 -*-
"""

    mslib.msui.mpl_pathinteractor
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Interactive editing of Path objects on a Matplotlib canvas.

    This module provides the following classes:

    a) WaypointsPath and subclasses PathV, PathH and PathH-GC:
    Derivatives of matplotlib.Path, provide additional methods to
    insert and delete vertices and to find best insertion points for new
    vertices.

    b) PathInteractor and subclasses VPathInteractor and HPathInteractor:
    Classes that implement a path editor by binding matplotlib mouse events
    to a WaypointsPath object. Support for moving, inserting and deleting vertices.

    The code in this module is inspired by the matplotlib example 'path_editor.py'
    (http://matplotlib.sourceforge.net/examples/event_handling/path_editor.html).

    For more information on implementing animated graphics in matplotlib, see
    http://www.scipy.org/Cookbook/Matplotlib/Animations.


    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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

import logging
import math
import numpy as np
import datetime
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from mslib.msui.mss_qt import QtCore, QtWidgets
from mslib.utils import get_distance, find_location, path_points, latlon_points
from mslib.thermolib import pressure2flightlevel
import cartopy.crs as ccrs

from mslib.msui import flighttrack as ft


def distance_point_linesegment(p, l1, l2):
    """Computes the distance between a point p and a line segment given by its
       endpoints l1 and l2.

    p, l1, l2 should be numpy arrays of length 2 representing [x,y].

    Based on the dot product formulation from
      'Subject 1.02: How do I find the distance from a point to a line?'
      (from  http://www.faqs.org/faqs/graphics/algorithms-faq/).

    Special case: The point p projects to an extension of the line segment.
    In this case, the distance between the point and the segment equals
    the distance between the point and the closest segment endpoint.
    """
    # Compute the parameter r in the line formulation p* = l1 + r*(l2-l1).
    # p* is the point on the line at which (p-p*) and (l1-l2) form a right
    # angle.
    r = (np.dot(p - l1, l2 - l1) / np.linalg.norm(l2 - l1) ** 2)
    # If 0 < r < 1, we return the distance p-p*. If r > 1, p* is on the
    # forward extension of l1-l2, hence return the distance between
    # p and l2. If r < 0, return the distance p-l1.
    if r > 1:
        return np.linalg.norm(p - l2)
    elif r < 0:
        return np.linalg.norm(p - l1)
    else:
        p_on_line = l1 + r * (l2 - l1)
        return np.linalg.norm(p - p_on_line)


class WaypointsPath(mpath.Path):
    """Derivative of matplotlib.Path that provides methods to insert and
       delete vertices.
    """

    def delete_vertex(self, index):
        """Remove the vertex at the given index from the list of vertices.
        """
        # TODO: Should codes (MOVETO, LINETO) be modified here? relevant for
        #      inserting/deleting first/last point.
        # Emulate pop() for ndarray:
        self.vertices = np.delete(self.vertices, index, axis=0)
        self.codes = np.delete(self.codes, index, axis=0)

    def insert_vertex(self, index, vertex, code):
        """Insert a new vertex (a tuple x,y) with the given code (see
           matplotlib.Path) at the given index.
        """
        self.vertices = np.insert(self.vertices, index,
                                  np.asarray(vertex, np.float_), axis=0)
        self.codes = np.insert(self.codes, index, code, axis=0)

    def index_of_closest_segment(self, x, y, eps=5):
        """Find the index of the edge closest to the specified point at x,y.

        If the point is not within eps (in the same coordinates as x,y) of
        any edge in the path, the index of the closest end point is returned.
        """
        # If only one point is stored in the list the best index to insert a
        # new point is after this point.
        if len(self.vertices) == 1:
            return 1

        # Compute the distance between the first point in the path and
        # the given point.
        point = np.array([x, y])
        min_index = 0
        min_distance = np.linalg.norm(point - self.vertices[0])

        # Loop over all line segments. If the distance between the given
        # point and the segment is smaller than a specified threshold AND
        # the distance is smaller than the currently smallest distance
        # then remember the current index.
        for i in range(len(self.vertices) - 1):
            l1 = self.vertices[i]
            l2 = self.vertices[i + 1]
            distance = distance_point_linesegment(point, l1, l2)
            if distance < eps and distance < min_distance:
                min_index = i + 1
                min_distance = distance

        # Compute the distance between the given point and the end point of
        # the path. Is it smaller than the currently smallest distance?
        distance = np.linalg.norm(point - self.vertices[-1])
        if distance < min_distance:
            min_index = len(self.vertices)

        return min_index

    def transform_waypoint(self, wps_list, index):
        """Transform the waypoint at index <index> of wps_list to plot
           coordinates.

        wps_list is a list of <Waypoint> objects (obtained from
        WaypointsTableModel.allWaypointData()).

        NEEDS TO BE IMPLEMENTED IN DERIVED CLASSES.
        """
        return (0, 0)

    def update_from_WaypointsTableModel(self, wps_model):
        """
        """
        Path = mpath.Path
        wps = wps_model.all_waypoint_data()
        if len(wps) > 0:
            pathdata = [(Path.MOVETO, self.transform_waypoint(wps, 0))]
            for i, _ in enumerate(wps[1:]):
                pathdata.append((Path.LINETO, self.transform_waypoint(wps, i + 1)))

        codes, vertices = list(zip(*pathdata))
        self.codes = np.array(codes, dtype=np.uint8)
        self.vertices = np.array(vertices)


#
# CLASS PathV
#


class PathV(WaypointsPath):
    """Class to represent a vertical flight profile path.
    """

    def __init__(self, *args, **kwargs):
        """The constructor required the additional keyword 'numintpoints':

        numintpoints -- number of intermediate interpolation points. The entire
                        flight track will be interpolated to this number of
                        points.
        """
        self.numintpoints = kwargs.pop("numintpoints")
        super(PathV, self).__init__(*args, **kwargs)

    def update_from_WaypointsTableModel(self, wps_model):
        """Extended version of the corresponding WaypointsPath method.

        The idea is to generate a field 'intermediate_indexes' that stores
        the indexes of the waypoints in the field of the intermediate
        great circle points generated by the flight track model, then
        to use these great circle indexes as x-coordinates for the vertical
        section. This means: If ngc_points are created by
        wps_model.intermediatePoints(), the waypoints are mapped to the
        range 0..ngc_points.

        NOTE: If wps_model only contains two equal waypoints,
        intermediate_indexes will NOT span the entire vertical section
        plot (this is intentional, as a flight with two equal
        waypoints makes no sense).
        """
        # Compute intermediate points.
        lats, lons, times = wps_model.intermediate_points(
            numpoints=self.numintpoints, connection="greatcircle")

        # Determine indices of waypoints in list of intermediate points.
        # Store these indices.
        waypoints = [[wp.lat, wp.lon] for wp in wps_model.all_waypoint_data()]
        intermediate_indexes = []
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            if abs(lat - waypoints[ipoint][0]) < 1E-10 and abs(lon - waypoints[ipoint][1]) < 1E-10:
                intermediate_indexes.append(i)
                ipoint += 1
            if ipoint >= len(waypoints):
                break

        self.intermediate_indexes = intermediate_indexes
        self.ilats = lats
        self.ilons = lons
        self.itimes = times

        # Call super method.
        WaypointsPath.update_from_WaypointsTableModel(self, wps_model)

    def transform_waypoint(self, wps_list, index):
        """Returns the x-index of the waypoint and its pressure.
        """
        return (self.intermediate_indexes[index], wps_list[index].pressure)


#
# CLASS PathH, PathH_GC
#


class PathH(WaypointsPath):
    """Class to represent a horizontal flight track path, waypoints connected
       by linear line segments.
    """

    def __init__(self, *args, **kwargs):
        """The constructor required the additional keyword 'map' to transform
           vertex cooredinates between lat/lon and projection coordinates.
        """
        self.map = kwargs.pop("map")
        self.kwargs = kwargs
        super(PathH, self).__init__(*args, **kwargs)

    def transform_waypoint(self, wps_list, index):
        """Transform lon/lat to projection coordinates.
        """
        user_proj = self.map.ax.projection
        return user_proj.transform_point((wps_list[index].lon), (wps_list[index].lat), src_crs=ccrs.PlateCarree())


class PathH_GC(PathH):
    """Class to represent a horizontal flight track path, waypoints connected
       by great circle segments.

    Derives from PathH.

    Provides to kinds of vertex data: (1) Waypoint vertices (wp_vertices) and
    (2) intermediate great circle vertices (vertices).
    """

    def __init__(self, *args, **kwargs):
        super(PathH_GC, self).__init__(*args, **kwargs)
        self.wp_codes = np.array([], dtype=np.uint8)
        self.wp_vertices = np.array([])

    def update_from_WaypointsTableModel(self, wps_model):
        """Get waypoint coordinates from flight track model, get
           intermediate great circle vertices from map instance.
        """
        Path = mpath.Path

        # Waypoint coordinates.
        wps = wps_model.all_waypoint_data()
        if len(wps) > 0:
            pathdata = [(Path.MOVETO, self.transform_waypoint(wps, 0))]
            for i in range(len(wps[1:])):
                pathdata.append((Path.LINETO, self.transform_waypoint(wps, i + 1)))
        wp_codes, wp_vertices = list(zip(*pathdata))
        self.wp_codes = np.array(wp_codes, dtype=np.uint8)
        self.wp_vertices = np.array(wp_vertices)

        # Coordinates of intermediate great circle points.
        lons, lats = list(zip(*[(wp.lon, wp.lat) for wp in wps]))
        x, y = self.map.gcpoints_path(lons, lats)

        if len(x) > 0:
            pathdata = [(Path.MOVETO, (x[0], y[0]))]
            for i in range(len(x[1:])):
                pathdata.append((Path.LINETO, (x[i + 1], y[i + 1])))
        codes, vertices = list(zip(*pathdata))
        self.codes = np.array(codes, dtype=np.uint8)
        self.vertices = np.array(vertices)

    def index_of_closest_segment(self, x, y, eps=5):
        """Find the index of the edge closest to the specified point at x,y.

        If the point is not within eps (in the same coordinates as x,y) of
        any edge in the path, the index of the closest end point is returned.
        """
        # Determine the index of the great circle vertex that is closest to the
        # given point.
        gcvertex_index = super(PathH_GC, self).index_of_closest_segment(x, y, eps)

        # Determine the waypoint index that corresponds to the great circle
        # index. If the best index is to append the waypoint to the end of
        # the flight track, directly return this index.
        if gcvertex_index == len(self.vertices):
            return len(self.wp_vertices)
        # Otherwise iterate through the list of great circle points and remember
        # the index of the last "real" waypoint that was encountered in this
        # list.
        i = 0  # index for great circle points
        j = 0  # index for waypoints
        wp_vertex = self.wp_vertices[j]
        while (i < gcvertex_index):
            vertex = self.vertices[i]
            if vertex[0] == wp_vertex[0] and vertex[1] == wp_vertex[1]:
                j += 1
                wp_vertex = self.wp_vertices[j]
            i += 1
        return j


#
# CLASS PathInteractor
#


class PathInteractor(QtCore.QObject):
    """An interactive matplotlib path editor. Allows vertices of a path patch
       to be interactively picked and moved around.

    Superclass for the path editors used by the top and side views of the
    Mission Support System.
    """

    showverts = True  # show the vertices of the path patch
    epsilon = 12  # max pixel distance to count as a vertex hit when

    # picking points

    def __init__(self, ax=None, waypoints=None, mplpath=None,
                 facecolor='blue', edgecolor='yellow',
                 linecolor='blue', markerfacecolor='red',
                 marker='o', label_waypoints=True):
        """The constructor initializes the path patches, overlying line
           plot and connects matplotlib signals.

        Arguments:
        ax -- matplotlib.Axes object into which the path should be drawn.
        waypoints -- flighttrack.WaypointsModel instance.
        mplpath -- matplotlib.path.Path instance
        facecolor -- facecolor of the patch
        edgecolor -- edgecolor of the patch
        linecolor -- color of the line plotted above the patch edges
        markerfacecolor -- color of the markers that represent the waypoints
        marker -- symbol of the markers that represent the waypoints, see
                  matplotlib plot() or scatter() routines for more information.
        label_waypoints -- put labels with the waypoint numbers on the waypoints.
        """
        QtCore.QObject.__init__(self)
        self.waypoints_model = None
        self.background = None
        self._ind = None  # the active vertex

        # Create a PathPatch representing the interactively editable path
        # (vertical profile or horizontal flight track in subclasses).
        path = mplpath
        pathpatch = mpatches.PathPatch(path, facecolor=facecolor,
                                       edgecolor=edgecolor, alpha=0.15)
        ax.add_patch(pathpatch)

        self.ax = ax
        self.path = path
        self.pathpatch = pathpatch
        self.pathpatch.set_animated(True)  # ensure correct redrawing

        # Draw the line representing flight track or profile (correct
        # vertices handling for the line needs to be ensured in subclasses).
        x, y = list(zip(*self.pathpatch.get_path().vertices))
        self.line, = self.ax.plot(x, y, color=linecolor,
                                  # transform=ccrs.Geodetic(),
                                  marker=marker, linewidth=2,
                                  markerfacecolor=markerfacecolor,
                                  animated=True)

        # List to accomodate waypoint labels.
        self.wp_labels = []
        self.label_waypoints = label_waypoints

        # Connect mpl events to handler routines: mouse movements and picks.
        canvas = self.ax.figure.canvas
        canvas.mpl_connect('draw_event', self.draw_callback)
        self.canvas = canvas

        # Set the waypoints model, connect to the change() signals of the model
        # and redraw the figure.
        self.set_waypoints_model(waypoints)

    def set_waypoints_model(self, waypoints):
        """Change the underlying waypoints data structure. Disconnect change()
           signals of an already existing model and connect to the new model.
           Redraw the map.
        """
        # If a model exists, disconnect from the old change() signals.
        wpm = self.waypoints_model
        if wpm:
            wpm.dataChanged.disconnect(self.qt_data_changed_listener)
            wpm.rowsInserted.disconnect(self.qt_insert_remove_point_listener)
            wpm.rowsRemoved.disconnect(self.qt_insert_remove_point_listener)
        # Set the new waypoints model.
        self.waypoints_model = waypoints
        # Connect to the new model's signals.
        wpm = self.waypoints_model
        wpm.dataChanged.connect(self.qt_data_changed_listener)
        wpm.rowsInserted.connect(self.qt_insert_remove_point_listener)
        wpm.rowsRemoved.connect(self.qt_insert_remove_point_listener)
        # Redraw.
        self.pathpatch.get_path().update_from_WaypointsTableModel(wpm)
        self.redraw_figure()

    def qt_insert_remove_point_listener(self, index, first, last):
        """Listens to rowsInserted() and rowsRemoved() signals emitted
           by the flight track data model. The view can thus react to
           data changes induced by another view (table, side view).
        """
        self.pathpatch.get_path().update_from_WaypointsTableModel(self.waypoints_model)
        self.redraw_figure()

    def qt_data_changed_listener(self, index1, index2):
        """Listens to dataChanged() signals emitted by the flight track
           data model. The view can thus react to data changes induced
           by another view (table, top view).
        """
        # REIMPLEMENT IN SUBCLASSES.
        pass

    def draw_callback(self, event):
        """Called when the figure is redrawn. Stores background data (for later
           restoration) and draws artists.
        """
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        try:
            # TODO review
            self.ax.draw_artist(self.pathpatch)
        except ValueError as ex:
            # When using Matplotlib 1.2, "ValueError: Invalid codes array."
            # occurs. The error occurs in Matplotlib's backend_agg.py/draw_path()
            # function. However, when I print the codes array in that function,
            # it looks fine -- correct length and correct codes. I can't figure
            # out why that error occurs.. (mr, 2013Feb08).
            logging.error("{} {}".format(ex, type(ex)))
        self.ax.draw_artist(self.line)
        for t in self.wp_labels:
            self.ax.draw_artist(t)
            # The blit() method makes problems (distorted figure background). However,
            # I don't see why it is needed -- everything seems to work without this line.
            # (see infos on http://www.scipy.org/Cookbook/Matplotlib/Animations).
            # self.canvas.blit(self.ax.bbox)

    def get_ind_under_point(self, event):
        """Get the index of the waypoint vertex under the point
           specified by event within epsilon tolerance.

        Uses display coordinates.
        If no waypoint vertex is found, None is returned.
        """
        xy = np.asarray(self.pathpatch.get_path().vertices)
        xyt = self.pathpatch.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x) ** 2 + (yt - event.y) ** 2)
        ind = d.argmin()
        if d[ind] >= self.epsilon:
            ind = None
        return ind

    def button_press_callback(self, event):
        """Called whenever a mouse button is pressed. Determines the index of
           the vertex closest to the click, as long as a vertex is within
           epsilon tolerance of the click.
        """
        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)

    def set_vertices_visible(self, showverts=True):
        """Set the visibility of path vertices (the line plot).
        """
        self.showverts = showverts
        self.line.set_visible(self.showverts)
        for t in self.wp_labels:
            t.set_visible(showverts and self.label_waypoints)
        if not self.showverts:
            self._ind = None
        self.canvas.draw()

    def set_patch_visible(self, showpatch=True):
        """Set the visibility of path patch (the area).
        """
        self.pathpatch.set_visible(showpatch)
        self.canvas.draw()

    def set_labels_visible(self, visible=True):
        """Set the visibility of the waypoint labels.
        """
        self.label_waypoints = visible
        for t in self.wp_labels:
            t.set_visible(self.showverts and self.label_waypoints)
        self.canvas.draw()

    def redraw_path(self, vertices=None):
        """Redraw the matplotlib artists that represent the flight track
           (path patch and line).

        If vertices are specified, they will be applied to the graphics
        output. Otherwise the vertex array obtained from the path patch
        will be used.
        """
        if vertices is None:
            vertices = self.pathpatch.get_path().vertices
        self.line.set_data(list(zip(*vertices)))

        # Draw waypoint labels.
        for wp in self.wp_labels:
            wp.remove()
        self.wp_labels = []  # remove doesn't seem to be necessary
        x, y = list(zip(*vertices))
        wpd = self.waypoints_model.all_waypoint_data()
        for i in range(len(wpd)):
            textlabel = u"{:}   ".format(str(i))
            if wpd[i].location != "":
                textlabel = u"{:}   ".format(wpd[i].location)
            t = self.ax.text(x[i],
                             y[i],
                             textlabel,
                             bbox=dict(boxstyle="round",
                                       facecolor="white",
                                       alpha=0.5,
                                       edgecolor="none"),
                             fontweight="bold",
                             zorder=4,
                             rotation=90,
                             animated=True,
                             clip_on=True,
                             visible=self.showverts and self.label_waypoints)
            self.wp_labels.append(t)

        if self.background:
            self.canvas.restore_region(self.background)
        try:
            self.ax.draw_artist(self.pathpatch)
        except ValueError as error:
            logging.error("ValueError Exception %s", error)
        self.ax.draw_artist(self.line)
        for t in self.wp_labels:
            self.ax.draw_artist(t)
        self.canvas.blit(self.ax.bbox)

    redraw_figure = redraw_path

    def confirm_delete_waypoint(self, row):
        """Open a QMessageBox and ask the user if he really wants to
           delete the waypoint at index <row>.

        Returns TRUE if the user confirms the deletion.

        If the flight track consists of only two points deleting a waypoint
        is not possible. In this case the user is informed correspondingly.
        """
        wps = self.waypoints_model.all_waypoint_data()
        if len(wps) < 3:
            QtWidgets.QMessageBox.warning(
                None, "Remove waypoint",
                "Cannot remove waypoint, the flight track needs to consist "
                "of at least two points.")
            return False
        else:
            wp = wps[row]
            return QtWidgets.QMessageBox.question(
                None, "Remove waypoint",
                u"Remove waypoint no.{:d} at {:.2f}/{:.2f}, flightlevel {:.2f}?"
                .format(row, wp.lat, wp.lon, wp.flightlevel),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes

    def set_path_color(self, line_color=None, marker_facecolor=None,
                       patch_facecolor=None):
        """Set the color of the path patch elements.

        Arguments (options):
        line_color -- color of the path line
        marker_facecolor -- color of the waypoints
        patch_facecolor -- color of the patch covering the path area
        """
        if line_color is not None:
            self.line.set_color(line_color)
        if marker_facecolor is not None:
            self.line.set_markerfacecolor(marker_facecolor)
        if patch_facecolor is not None:
            self.pathpatch.set_facecolor(patch_facecolor)


#
# CLASS VPathInteractor
#


class VPathInteractor(PathInteractor):
    """Subclass of PathInteractor that implements an interactively editable
       vertical profile of the flight track.
    """
    signal_get_vsec = QtCore.Signal(name="get_vsec")

    def __init__(self, ax, waypoints, redraw_xaxis=None, clear_figure=None, numintpoints=101):
        """Constructor passes a PathV instance its parent.

        Arguments:
        ax -- matplotlib.Axes object into which the path should be drawn.
        waypoints -- flighttrack.WaypointsModel instance.
        numintpoints -- number of intermediate interpolation points. The entire
                        flight track will be interpolated to this number of
                        points.
        redrawXAxis -- callback function to redraw the x-axis on path changes.
        """
        self.numintpoints = numintpoints
        self.redraw_xaxis = redraw_xaxis
        self.clear_figure = clear_figure
        super(VPathInteractor, self).__init__(
            ax=ax, waypoints=waypoints, mplpath=PathV([[0, 0]], numintpoints=numintpoints))

    def get_num_interpolation_points(self):
        return self.numintpoints

    def redraw_figure(self):
        """For the side view, changes in the horizontal position of a waypoint
           (including moved waypoints, new or deleted waypoints) make a complete
           redraw of the figure necessary.

           Calls the callback function 'redrawXAxis()'.
        """
        self.redraw_path()
        # emit signal to redraw map
        self.signal_get_vsec.emit()
        if self.clear_figure() is not None:
            self.clear_figure()
        if self.redraw_xaxis is not None:
            self.redraw_xaxis(self.path.ilats, self.path.ilons, self.path.itimes)
        self.ax.figure.canvas.draw()

    def button_release_delete_callback(self, event):
        """Called whenever a mouse button is released.
        """
        if not self.showverts or event.button != 1:
            return

        if self._ind is not None:
            if self.confirm_delete_waypoint(self._ind):
                # removeRows() will trigger a signal that will redraw the path.
                self.waypoints_model.removeRows(self._ind)
            self._ind = None

    def button_release_insert_callback(self, event):
        """Called whenever a mouse button is released.

        From the click event's coordinates, best_index is calculated as
        the index of a vertex whose x coordinate > clicked x coordinate.
        This is the position where the waypoint is to be inserted.

        'lat' and 'lon' are calculated as an average of each of the first waypoint
        in left and right neighbourhood of inserted waypoint.

        The coordinates are checked against "locations" defined in mss' config.

        A new waypoint with the coordinates, and name is inserted into the waypoints_model.
        """
        if not self.showverts or event.button != 1 or event.inaxes is None:
            return
        y = event.ydata
        wpm = self.waypoints_model
        flightlevel = float(pressure2flightlevel(y))
        [lat, lon], best_index = self.get_lat_lon(event)
        loc = find_location(lat, lon)  # skipped tolerance which uses appropriate_epsilon_km
        if loc is not None:
            (lat, lon), location = loc
        else:
            lat, lon = float(round(lat, 2)), float(round(lon, 2))
            location = u""
        new_wp = ft.Waypoint(lat, lon, flightlevel, location=location)
        wpm.insertRows(best_index, rows=1, waypoints=[new_wp])
        self.redraw_figure()

        self._ind = None

    def get_lat_lon(self, event):
        x = event.xdata
        wpm = self.waypoints_model
        vertices = self.pathpatch.get_path().vertices
        vertices = np.ndarray.tolist(vertices)
        for index, vertex in enumerate(vertices):
            vertices[index].append(datetime.datetime(2012, 7, 1, 10, 30))
        best_index = 1
        # if x axis has increasing coordinates
        if vertices[-1][0] > vertices[0][0]:
            for index, vertex in enumerate(vertices):
                if x >= vertex[0]:
                    best_index = index + 1
        # if x axis has decreasing coordinates
        else:
            for index, vertex in enumerate(vertices):
                if x <= vertex[0]:
                    best_index = index + 1
        # number of subcoordinates is determined by difference in x coordinates
        number_of_intermediate_points = math.floor(vertices[best_index][0] - vertices[best_index - 1][0])
        intermediate_vertices_list = path_points([vertices[best_index - 1], vertices[best_index]],
                                                 number_of_intermediate_points)
        wp1Array = [wpm.waypoint_data(best_index - 1).lat, wpm.waypoint_data(best_index - 1).lon,
                    datetime.datetime(2012, 7, 1, 10, 30)]
        wp2Array = [wpm.waypoint_data(best_index).lat, wpm.waypoint_data(best_index).lon,
                    datetime.datetime(2012, 7, 1, 10, 30)]
        intermediate_waypoints_list = latlon_points(wp1Array, wp2Array,
                                                    number_of_intermediate_points, connection="greatcircle")

        # best_index1 is the best index among the intermediate coordinates to fit the hovered point
        # if x axis has increasing coordinates
        best_index1 = 1
        if vertices[-1][0] > vertices[0][0]:
            for index, vertex in enumerate(intermediate_vertices_list[0]):
                if x >= vertex:
                    best_index1 = index + 1
        # if x axis has decreasing coordinates
        else:
            for index, vertex in enumerate(intermediate_vertices_list[0]):
                if x <= vertex:
                    best_index1 = index + 1
        # depends if best_index1 or best_index1 - 1 on closeness to left or right neighbourhood
        return [round(intermediate_waypoints_list[0][best_index1 - 1], 2),
                round(intermediate_waypoints_list[1][best_index1 - 1], 2)], best_index

    def button_release_move_callback(self, event):
        """Called whenever a mouse button is released.
        """
        if not self.showverts or event.button != 1:
            return

        if self._ind is not None:
            # Submit the new pressure (the only value that can be edited
            # in the side view) to the data model.
            vertices = self.pathpatch.get_path().vertices
            pressure = vertices[self._ind][1]
            # http://doc.trolltech.com/4.3/qabstractitemmodel.html#createIndex
            qt_index = self.waypoints_model.createIndex(self._ind, ft.PRESSURE)
            # NOTE: QVariant cannot handle numpy.float64 types, hence convert
            # to float().
            self.waypoints_model.setData(qt_index, QtCore.QVariant(float(pressure / 100.)))

        self._ind = None

    def motion_notify_callback(self, event):
        """Called on mouse movement. Redraws the path if a vertex has been
           picked and is being dragged.

        In the side view, the horizontal position of a waypoint is locked.
        Hence, points can only be moved in the vertical direction (y position
        in this view).
        """
        if not self.showverts or self._ind is None or event.inaxes is None or event.button != 1:
            return
        vertices = self.pathpatch.get_path().vertices
        # Set the new y position of the vertex to event.ydata. Keep the
        # x coordinate.
        vertices[self._ind] = vertices[self._ind][0], event.ydata
        self.redraw_path(vertices)

    def qt_data_changed_listener(self, index1, index2):
        """Listens to dataChanged() signals emitted by the flight track
           data model. The side view can thus react to data changes
           induced by another view (table, top view).
        """
        # If the altitude of a point has changed, only the plotted flight
        # profile needs to be redrawn (redraw_path()). If the horizontal
        # position of a waypoint has changed, the entire figure needs to be
        # redrawn, as this affects the x-position of all points.
        self.pathpatch.get_path().update_from_WaypointsTableModel(self.waypoints_model)
        if index1.column() in [ft.FLIGHTLEVEL, ft.PRESSURE, ft.LOCATION]:
            self.redraw_path(self.pathpatch.get_path().vertices)
        elif index1.column() in [ft.LAT, ft.LON]:
            self.redraw_figure()
        elif index1.column() in [ft.TIME_UTC]:
            if self.redraw_xaxis is not None:
                self.redraw_xaxis(self.path.ilats, self.path.ilons, self.path.itimes)

#
# CLASS HPathInteractor
#


class HPathInteractor(PathInteractor):
    """Subclass of PathInteractor that implements an interactively editable
       horizontal flight track. Waypoints are connected with great circles.
    """

    def __init__(self, mplmap, waypoints,
                 linecolor='blue', markerfacecolor='red',
                 label_waypoints=True):
        """Constructor passes a PathH_GC instance its parent (horizontal path
           with waypoints connected with great circles).

        Arguments:
        mplmap -- mpl_map.MapCanvas instance into which the path should be drawn.
        waypoints -- flighttrack.WaypointsModel instance.
        """
        self.map = mplmap
        self.wp_scatter = None
        self.markerfacecolor = markerfacecolor
        self.tangent_lines = None
        self.show_tangent_points = False
        self.solar_lines = None
        self.show_solar_angle = None
        self.remote_sensing = None
        if self.map.ax is not None:
            self.ax = self.map.ax
        super(HPathInteractor, self).__init__(
            ax=mplmap.ax, waypoints=waypoints,
            mplpath=PathH_GC([[0, 0]], map=mplmap),
            facecolor='none', edgecolor='none', linecolor=linecolor,
            markerfacecolor=markerfacecolor, marker='',
            label_waypoints=label_waypoints)

    def appropriate_epsilon(self, px=5):
        """Determine an epsilon value appropriate for the current projection and
           figure size.

        The epsilon value gives the distance required in map projection
        coordinates that corresponds to approximately px Pixels in screen
        coordinates. The value can be used to find the line/point that is
        closest to a click while discarding clicks that are too far away
        from any geometry feature.
        """
        # (bounds = left, bottom, width, height)
        ax_bounds = self.ax.bbox.bounds
        width = int(round(ax_bounds[2]))
        map_delta_x = np.hypot(self.map.ax.get_extent()[2] - self.map.ax.get_extent()[3],
                               self.map.ax.get_extent()[0] - self.map.ax.get_extent()[1])
        map_coords_per_px_x = map_delta_x / width
        return map_coords_per_px_x * px

    def appropriate_epsilon_km(self, px=5):
        """Determine an epsilon value appropriate for the current projection and
           figure size.

        The epsilon value gives the distance required in map projection
        coordinates that corresponds to approximately px Pixels in screen
        coordinates. The value can be used to find the line/point that is
        closest to a click while discarding clicks that are too far away
        from any geometry feature.
        """
        # (bounds = left, bottom, width, height)
        ax_bounds = self.ax.bbox.bounds
        diagonal = math.hypot(round(ax_bounds[2]), round(ax_bounds[3]))
        if str(self.map.ax.projection)[13:-27] in ['Stereographic', 'LambertConformal']:
            map_delta = np.hypot(self.map.ax.get_extent()[2] - self.map.ax.get_extent()[3],
                                 self.map.ax.get_extent()[0] - self.map.ax.get_extent()[1]) / 1000.
        else:
            map_delta = get_distance((self.map.ax.get_extent()[2], self.map.ax.get_extent()[0]),
                                     (self.map.ax.get_extent()[3], self.map.ax.get_extent()[1]))
        km_per_px = map_delta / diagonal
        return km_per_px * px

    def get_lat_lon(self, event):
        return ccrs.PlateCarree().transform_point(event.xdata, event.ydata, self.map.ax.projection)

    def button_release_insert_callback(self, event):
        """Called whenever a mouse button is released.

        From the click event's coordinates, best_index is calculated if it can be optimally fit
        as a prior waypoint in the path.

        A vertex with same coordinates is inserted into the path in canvas.

        The coordinates are checked against "locations" defined in mss' config.

        A new waypoint with the coordinates, and name is inserted into the waypoints_model.
        """
        if not self.showverts or event.button != 1 or event.inaxes is None:
            return

        # Get position for new vertex.
        x, y = event.xdata, event.ydata
        best_index = self.pathpatch.get_path().index_of_closest_segment(
            x, y, eps=self.appropriate_epsilon())
        logging.debug(u"TopView insert point: clicked at (%f, %f), "
                      u"best index: %d", x, y, best_index)
        self.pathpatch.get_path().insert_vertex(best_index, [x, y], WaypointsPath.LINETO)

        lon, lat = ccrs.PlateCarree().transform_point(x, y, self.map.ax.projection)
        loc = find_location(lat, lon, tolerance=self.appropriate_epsilon_km(px=15))
        if loc is not None:
            (lat, lon), location = loc
        else:
            lat, lon = float(round(lat, 2)), float(round(lon, 2))
            location = u""
        wpm = self.waypoints_model
        if len(wpm.all_waypoint_data()) > 0 and 0 < best_index <= len(wpm.all_waypoint_data()):
            flightlevel = wpm.waypoint_data(best_index - 1).flightlevel
        elif len(wpm.all_waypoint_data()) > 0 and best_index == 0:
            flightlevel = wpm.waypoint_data(0).flightlevel
        else:
            logging.error(u"Cannot copy flightlevel. best_index: %s, len: %s",
                          best_index, len(wpm.all_waypoint_data()))
            flightlevel = 0
        new_wp = ft.Waypoint(lat, lon, flightlevel, location=location)
        wpm.insertRows(best_index, rows=1, waypoints=[new_wp])
        self.redraw_path()

        self._ind = None

    def button_release_move_callback(self, event):
        """Called whenever a mouse button is released.
        """
        if not self.showverts or event.button != 1 or self._ind is None:
            return

        # Submit the new position to the data model.
        vertices = self.pathpatch.get_path().wp_vertices
        lon, lat = ccrs.PlateCarree().transform_point(vertices[self._ind][0],
                                                      vertices[self._ind][1], self.map.ax.projection)
        loc = find_location(lat, lon, tolerance=self.appropriate_epsilon_km(px=15))
        if loc is not None:
            lat, lon = loc[0]
        else:
            lat, lon = float(round(lat, 2)), float(round(lon, 2))
        # http://doc.trolltech.com/4.3/qabstractitemmodel.html#createIndex
        # TODO: can lat/lon be submitted together to avoid emitting dataChanged() signals
        #      twice?
        qt_index = self.waypoints_model.createIndex(self._ind, ft.LAT)
        self.waypoints_model.setData(qt_index, QtCore.QVariant(lat))
        qt_index = self.waypoints_model.createIndex(self._ind, ft.LON)
        self.waypoints_model.setData(qt_index, QtCore.QVariant(lon))

        self._ind = None

    def button_release_delete_callback(self, event):
        """Called whenever a mouse button is released.
        """
        if not self.showverts or event.button != 1:
            return

        if self._ind is not None and self.confirm_delete_waypoint(self._ind):
            # removeRows() will trigger a signal that will redraw the path.
            self.waypoints_model.removeRows(self._ind)

        self._ind = None

    def motion_notify_callback(self, event):
        """Called on mouse movement. Redraws the path if a vertex has been
           picked and dragged.
        """
        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        wp_vertices = self.pathpatch.get_path().wp_vertices
        wp_vertices[self._ind] = event.xdata, event.ydata
        print(event, event.xdata, event.ydata)
        self.redraw_path(wp_vertices)

    def qt_data_changed_listener(self, index1, index2):
        """Listens to dataChanged() signals emitted by the flight track
           data model. The top view can thus react to data changes
           induced by another view (table, side view).
        """
        # Update the top view if the horizontal position of any point has been
        # changed.
        if index1.column() in [ft.LOCATION, ft.LAT, ft.LON, ft.FLIGHTLEVEL]:
            self.update()

    def update(self):
        """Update the path plot by updating coordinates and intermediate
           great circle points from the path patch, then redrawing.
        """
        self.pathpatch.get_path().update_from_WaypointsTableModel(
            self.waypoints_model)
        self.redraw_path()

    def redraw_path(self, wp_vertices=None):
        """Redraw the matplotlib artists that represent the flight track
           (path patch, line and waypoint scatter).

        If waypoint vertices are specified, they will be applied to the
        graphics output. Otherwise the vertex array obtained from the path
        patch will be used.
        """
        if self.map.ax is not None:
            self.ax = self.map.ax

        if wp_vertices is None:
            wp_vertices = self.pathpatch.get_path().wp_vertices
            x, y = list(zip(*wp_vertices))
            # print(x, y)
            x, y = np.asarray(x), np.asarray(y)
            result = ccrs.PlateCarree().transform_points(
                self.map.ax.projection, x, y)
            lons, lats = result[:, 0], result[:, 1]
            # print("res", result)
            # print("lons", lons)
            # print("lats", lats)
            x, y = self.map.gcpoints_path(lons, lats)
            # print(x, y)
            result = ccrs.PlateCarree().transform_points(
                self.map.ax.projection, x, y)
            # print("res", result)
            vertices = np.asarray(list(zip(x, y)))
        else:
            # If waypoints have been provided, compute the intermediate
            # great circle points for the line instance.
            x, y = list(zip(*wp_vertices))
            # print(x, y)
            x, y = np.asarray(x), np.asarray(y)
            result = ccrs.PlateCarree().transform_points(
                self.map.ax.projection, x, y)
            lons, lats = result[:, 0], result[:, 1]
            # print("res", result)
            # print("lons", lons)
            # print("lats", lats)
            x, y = self.map.gcpoints_path(lons, lats)
            # print(x, y)
            result = ccrs.PlateCarree().transform_points(
                self.map.ax.projection, x, y)
            # print("res", result)
            vertices = np.asarray(list(zip(x, y)))

        # Set the line to disply great circle points, remove existing
        # waypoints scatter instance and draw a new one. This is
        # necessary as scatter() does not provide a set_data method.
        self.line.set_data(list(zip(*vertices)))

        wp_heights = [(wp.flightlevel * 0.03048) for wp in self.waypoints_model.all_waypoint_data()]
        wp_times = [wp.utc_time for wp in self.waypoints_model.all_waypoint_data()]

        if self.tangent_lines is not None:
            self.tangent_lines.remove()
        if self.show_tangent_points:
            assert self.remote_sensing is not None
            self.tangent_lines = self.remote_sensing.compute_tangent_lines(
                self.map, wp_vertices, wp_heights)
            self.ax.add_collection(self.tangent_lines)
        else:
            self.tangent_lines = None

        if self.solar_lines is not None:
            self.solar_lines.remove()
        if self.show_solar_angle is not None:
            assert self.remote_sensing is not None
            self.solar_lines = self.remote_sensing.compute_solar_lines(
                self.map, wp_vertices, wp_heights, wp_times, self.show_solar_angle)
            self.ax.add_collection(self.solar_lines)
        else:
            self.solar_lines = None

        if self.wp_scatter is not None:
            self.wp_scatter.remove()
        x, y = list(zip(*wp_vertices))
        # (animated is important to remove the old scatter points from the map)
        self.wp_scatter = self.ax.scatter(x, y, color=self.markerfacecolor,
                                          s=20, zorder=3, animated=True,
                                          visible=self.showverts)
        self.line, = self.ax.plot(x, y, color='blue',
                                  marker='o', linewidth=2,
                                  markerfacecolor='red',
                                  animated=True)

        # Draw waypoint labels.
        label_offset = self.appropriate_epsilon()
        for wp_label in self.wp_labels:
            wp_label.remove()
        self.wp_labels = []  # remove doesn't seem to be necessary
        wpd = self.waypoints_model.all_waypoint_data()
        for i in range(len(wpd)):
            textlabel = str(i)
            if wpd[i].location != "":
                textlabel = u"{:}".format(wpd[i].location)
            t = self.ax.text(x[i] + label_offset,
                             y[i] + label_offset,
                             textlabel,
                             bbox=dict(boxstyle="round",
                                       facecolor="white",
                                       alpha=0.6,
                                       edgecolor="none"),
                             fontweight="bold",
                             zorder=4,
                             animated=True,
                             clip_on=True,
                             visible=self.showverts and self.label_waypoints)
            self.wp_labels.append(t)

        # Redraw the artists.
        if self.background:
            self.canvas.restore_region(self.background)
        try:
            self.ax.draw_artist(self.pathpatch)
        except ValueError as error:
            logging.debug("ValueError Exception %s", error)
        self.ax.draw_artist(self.wp_scatter)
        self.ax.draw_artist(self.line)

        for t in self.wp_labels:
            self.ax.draw_artist(t)
        if self.show_tangent_points:
            self.ax.draw_artist(self.tangent_lines)
        if self.show_solar_angle is not None:
            self.ax.draw_artist(self.solar_lines)
        self.canvas.blit(self.ax.bbox)

    # Link redraw_figure() to redraw_path().
    redraw_figure = redraw_path

    def draw_callback(self, event):
        """Extends PathInteractor.draw_callback() by drawing the scatter
           instance.
        """
        PathInteractor.draw_callback(self, event)
        self.ax.draw_artist(self.wp_scatter)
        if self.show_solar_angle:
            self.ax.draw_artist(self.solar_lines)
        if self.show_tangent_points:
            self.ax.draw_artist(self.tangent_lines)

    def get_ind_under_point(self, event):
        """Get the index of the waypoint vertex under the point
           specified by event within epsilon tolerance.

        Uses display coordinates.
        If no waypoint vertex is found, None is returned.
        """
        xy = np.asarray(self.pathpatch.get_path().wp_vertices)
        xt, yt = xy[:, 0], xy[:, 1]
        d = np.hypot(xt - event.xdata, yt - event.ydata)
        ind = d.argmin()
        if d[ind] >= self.appropriate_epsilon():
            ind = None
        return ind

    def set_path_color(self, line_color=None, marker_facecolor=None,
                       patch_facecolor=None):
        """Set the color of the path patch elements.

        Arguments (options):
        line_color -- color of the path line
        marker_facecolor -- color of the waypoints
        patch_facecolor -- color of the patch covering the path area
        """
        PathInteractor.set_path_color(self, line_color, marker_facecolor,
                                      patch_facecolor)
        if marker_facecolor is not None:
            self.wp_scatter.set_facecolor(marker_facecolor)
            self.wp_scatter.set_edgecolor(marker_facecolor)
            self.markerfacecolor = marker_facecolor

    def set_vertices_visible(self, showverts=True):
        """Set the visibility of path vertices (the line plot).
        """
        self.wp_scatter.set_visible(showverts)
        PathInteractor.set_vertices_visible(self, showverts)

    def set_tangent_visible(self, visible):
        self.show_tangent_points = visible

    def set_solar_angle_visible(self, visible):
        self.show_solar_angle = visible

    def set_remote_sensing(self, ref):
        self.remote_sensing = ref
