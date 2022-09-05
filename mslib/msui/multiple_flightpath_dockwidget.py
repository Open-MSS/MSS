# -*- coding: utf-8 -*-
"""

    mslib.multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control Widget to configure multiple flightpath on topview.

    This file is part of MSS.

    :copyright: Copyright 2022 Jatin Jain
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
    limitations under the License.
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.msui import msui
import threading


class MultipleFlightpath(object):
    """
    Represent a Multiple FLightpath
    """

    def __init__(self, mapcanvas, wp, linewidth=2, color='blue'):
        self.map = mapcanvas
        self.flightlevel = None
        self.comments = ''
        self.patches = []
        self.waypoints = wp
        self.linewidth = linewidth
        self.color = color
        self.draw()

    def draw_line(self, x, y):
        self.patches.append(self.map.plot(x, y, color=self.color, linewidth=self.linewidth))

    def compute_xy(self, lon, lat):
        x, y = self.map.gcpoints_path(lon, lat)
        return x, y

    def get_lonlat(self):
        lon = []
        lat = []
        for i in range(len(self.waypoints)):
            lat.append(self.waypoints[i][0])
            lon.append(self.waypoints[i][1])
        return lat, lon

    def update(self, linewidth=None):
        if linewidth is not None:
            self.linewidth = linewidth
        self.remove()
        self.draw()

    def draw(self):
        lat, lon = self.get_lonlat()
        x, y = self.compute_xy(lon, lat)
        self.draw_line(x, y)
        self.map.ax.figure.canvas.draw()

    def remove(self):
        for patch in self.patches:
            for elem in patch:
                elem.remove()
        self.patches = []
        self.map.ax.figure.canvas.draw()


class MultipleFlightpathControlWidget(QtWidgets.QWidget, ui.Ui_MultipleViewWidget):
    """
    This class provides the interface for plotting Multiple Flighttracks
    on the TopView canvas.
    """

    def __init__(self, parent=None, view=None, listView=None, activeFlightTrack=None):
        super(MultipleFlightpathControlWidget, self).__init__(parent)
        self.listView = listView
        self.ui = parent
        self.setupUi(self)
        self.view = view  # canvas
        self.flight_path = None  # flightpath object
        self.dict_files = {}  # Dictionary of files added; key: patch, waypoints
        self.active_flight_track = activeFlightTrack

        # Connect Signals and Slots
        self.list_flighttrack.itemChanged.connect(self.wait2)
        self.listView.model().rowsInserted.connect(self.wait)
        self.listView.model().rowsRemoved.connect(self.flighttrackRemoved)
        self.listView.itemActivated.connect(self.activate_flighttrack)
        # Set flags
        self.flighttrack_added = False
        self.flighttrack_activated = False

        # Load default flighttrack.
        for index in range(self.listView.count()):
            wp_model = self.listView.item(index).flighttrack_model
            listItem = self.create_list_item(wp_model)

            self.save_waypoint_model_data(wp_model)

            self.activate_flighttrack(listItem)

    def update(self):
        for entry in self.dict_files.values():
            entry["patch"].update()

    def remove(self):
        for entry in self.dict_files.values():
            entry["patch"].remove()

    def wait(self, parent, start, end):
        t1 = threading.Timer(1.0, self.flighttrackAdded, [parent, start, end])
        t1.start()

    def wait2(self):
        t2 = threading.Timer(2.0, self.flagop)
        t2.start()

    def flagop(self):
        if self.flighttrack_added:
            self.flighttrack_added = False
        elif self.flighttrack_activated:
            self.flighttrack_activated = False
        else:
            self.drawInactiveFlighttracks()

    def flighttrackAdded(self, parent, start, end):
        """
        Slot to add flighttrack.
        """
        self.flighttrack_added = True
        wp_model = self.listView.item(start).flighttrack_model
        listItem = self.create_list_item(wp_model)
        self.save_waypoint_model_data(wp_model)

        self.drawInactiveFlighttracks()
        self.activate_flighttrack(listItem)

    def save_waypoint_model_data(self, wp_model):
        wp_data = [(wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_model.all_waypoint_data()]
        self.dict_files[wp_model]["wp_data"] = wp_data

    def create_list_item(self, wp_model):
        """
        PyQt5 method : Add items in list and add checkbox functionality
        """
        self.active_flight_track = wp_model
        listItem = msui.QFlightTrackListWidgetItem(wp_model, self.list_flighttrack)
        listItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        listItem.setCheckState(QtCore.Qt.Unchecked)

        # Create new key in dict
        self.dict_files[wp_model] = {}
        self.dict_files[wp_model]["patch"] = None
        self.dict_files[wp_model]["wp_data"] = []

        return listItem

    def flighttrackRemoved(self, parent, start, end):
        """
        Slot to remove flighttrack.
        """
        self.dict_files[self.list_flighttrack.item(start).flighttrack_model]["patch"].remove()
        del self.dict_files[self.list_flighttrack.item(start).flighttrack_model]
        self.list_flighttrack.takeItem(start)

    def activate_flighttrack(self, item):
        """
        Activate flighttrack
        """
        if not self.flighttrack_added:
            self.flighttrack_activated = True
        self.save_waypoint_model_data(self.active_flight_track)   # Before activating new flighttrack, update waypoints of previous flighttrack
        self.active_flight_track = item.flighttrack_model

        font = QtGui.QFont()

        for i in range(self.list_flighttrack.count()):
            listItem = self.list_flighttrack.item(i)
            if self.active_flight_track == self.list_flighttrack.item(i).flighttrack_model:
                font.setBold(True)
                if self.dict_files[listItem.flighttrack_model]["patch"] is not None:
                    self.dict_files[listItem.flighttrack_model]["patch"].remove()
                listItem.setCheckState(QtCore.Qt.Unchecked)
                listItem.setFlags(listItem.flags() ^ QtCore.Qt.ItemIsUserCheckable)   # make activated track uncheckable
            else:
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            listItem.setFont(font)

    def set_linewidth(self):
        """
        """
        pass

    def drawInactiveFlighttracks(self):
        """
        Draw inactive flighttracks
        """
        for entry in self.dict_files.values():
            if entry["patch"] is not None:
                entry["patch"].remove()

        for index in range(self.list_flighttrack.count()):
            if hasattr(self.list_flighttrack.item(index), "checkState") and (
                    self.list_flighttrack.item(index).checkState() == QtCore.Qt.Checked):
                listItem = self.list_flighttrack.item(index)
                if listItem.flighttrack_model != self.active_flight_track:

                    patch = MultipleFlightpath(self.view.map,
                                               self.dict_files[listItem.flighttrack_model][
                                                   "wp_data"])

                    self.dict_files[listItem.flighttrack_model]["patch"] = patch
            else:
                pass
