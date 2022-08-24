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
import logging
import os
from PyQt5 import QtWidgets, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.utils.qt import get_open_filenames
from mslib.utils.config import load_settings_qsettings, save_settings_qsettings
from fs import open_fs
import flighttrack as ft
import msui
import xml


class MultipleFlightpath(object):
    """
    Represent a Multiple FLightpath
    """

    def __init__(self, mapcanvas, wp):
        self.map = mapcanvas
        self.flightlevel = None
        self.comments = ''
        self.patches = []
        self.waypoints = wp
        self.draw()

    def draw_line(self, x, y):
        self.patches.append(self.map.plot(x, y, color='blue', linewidth='2'))

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
        self.waypoint_list = []  # List of waypoints parsed from FTML file
        self.directory_location = None
        self.waypoints_modelList = []
        self.active_flight_track = None
        self.inactiveTrackPatches = []

        # Connect Signals and Slots
        self.bt_addFile.clicked.connect(self.get_file)
        self.btRemove_file.clicked.connect(self.remove_item)
        self.listView.itemChanged.connect(self.syncListViews)
        self.listView.itemChanged.connect(self.drawInactiveFlighttracks)
        self.listView.itemActivated.connect(self.get_active_flighttrack)

        self.view.plot_multiple_flightpath(self)

        # Update Flighttrack list from MSUI list
        self.syncListViews()

    def syncListViews(self):
        self.list_flighttrack.clear()
        for index in range(self.listView.count()):
            wp_model = self.listView.item(index).flighttrack_model
            msui.QFlightTrackListWidgetItem(wp_model, self.list_flighttrack)

    def get_file(self):
        """
        Slot that open a file dialog to choose FTML file.
        """
        filenames = get_open_filenames(
            self, "Open FTML File", os.path.dirname(str(self.directory_location)), "FTML Files(*.ftml)")
        if not filenames:
            return
        self.select_file(filenames)

    def select_file(self, filenames):
        """
        Initializes selected file.
        """
        for filename in filenames:
            if filename is None:
                return
            text = filename
            if text not in self.dict_files:
                self.dict_files[text] = {}
                self.dict_files[text]["track"] = None
                self.create_list_item(filename)
            else:
                logging.info("%s file already added", text)
        self.labelStatus.setText("Status: Files added successfully.")

    def parse_ftml(self, filename):
        """
        Load a flight track from an XML file at <filename>.
        """
        _dirname, _name = os.path.split(filename)
        _fs = open_fs(_dirname)
        datasource = _fs.open(_name)
        try:
            doc = xml.dom.minidom.parse(datasource)
        except xml.parsers.expat.ExpatError as ex:
            raise SyntaxError(str(ex))

        ft_el = doc.getElementsByTagName("FlightTrack")[0]

        waypoints_list = []
        for wp_el in ft_el.getElementsByTagName("Waypoint"):

            location = wp_el.getAttribute("location")
            lat = float(wp_el.getAttribute("lat"))
            lon = float(wp_el.getAttribute("lon"))
            flightlevel = float(wp_el.getAttribute("flightlevel"))
            comments = wp_el.getElementsByTagName("Comments")[0]
            # If num of comments is 0(null comment), then return ''
            if len(comments.childNodes):
                comments = comments.childNodes[0].data.strip()
            else:
                comments = ''
            waypoints_list.append((lat, lon, flightlevel, location, comments))
        return waypoints_list

    def save_settings(self):
        """
        Save Flighttrack settings after closing of view.
        """
        for entry in self.dict_files.values():
            entry["track"] = None
        settings = {
            "saved_files": self.dict_files
        }
        save_settings_qsettings(self.settings_tag, settings)

    def load_flighttrack(self):
        """
        Load Multiple Flighttracks simultaneously and construct corresponding
        flight patches on topview.
        """
        for entry in self.dict_files.values():  # removes all patches from map, but not from dict files
            if entry["track"] is not None:  # since newly initialized files will have patch:None
                entry["track"].remove()

        for index in range(self.list_flighttrack.count()):
            if hasattr(self.list_flighttrack.item(index), "checkState") and (
                    self.list_flighttrack.item(index).checkState() == QtCore.Qt.Checked):
                if self.list_flighttrack.item(index).text() in self.dict_files:
                    # if self.dict_files[self.list_flighttrack.item(index).text()]["track"] is None
                    # ToDO: Don't create new patch object if flighttrack patch object is Not None
                    self.directory_location = str(self.list_flighttrack.item(index).text())
                    self.waypoint_list = self.parse_ftml(self.directory_location)
                    patch = MultipleFlightpath(self.view.map, self.waypoint_list)
                    self.dict_files[self.list_flighttrack.item(index).text()]["track"] = patch

    def get_active_flighttrack(self, item):
        self.active_flight_track = item.flighttrack_model

    def remove_item(self):
        """
        Remove FTML file from list widget.
        """
        flag = 0  # used to set label, if not file is selected
        for index in range(self.list_flighttrack.count()):
            if hasattr(self.list_flighttrack.item(index), "checkState") and \
                    (self.list_flighttrack.item(index).checkState() == QtCore.Qt.Checked):  # If item is checked
                if self.dict_files[self.list_flighttrack.item(index).text()]['track'] is not None:
                    self.dict_files[self.list_flighttrack.item(index).text()]['track'].remove()
                del self.dict_files[self.list_flighttrack.item(index).text()]
                self.list_flighttrack.takeItem(index)
                self.remove_item()
                flag = 1
                self.labelStatus.setText("Status: FTML File is Removed")
        if not flag:
            self.labelStatus.setText("Status: Select FTML File to Delete")

    def create_list_item(self, filename):
        """
        Add flighttracks to list widget
        """
        wp_model = ft.WaypointsTableModel(filename=filename)
        for count in range(self.listView.count()):
            if str(self.listView.item(count).flighttrack_model) == str(wp_model):
                break
        else:
            listItem = msui.QFlightTrackListWidgetItem(wp_model, self.listView)
            msui.QFlightTrackListWidgetItem(wp_model, self.list_flighttrack)

    def drawInactiveFlighttracks(self):
        """
        """
        dict = {}  # Dictionary of waypointTableModel objects and their waypoints

        if len(self.inactiveTrackPatches) > 0:
            self.removen()

        for index in range(self.listView.count()):  # Make list of all flighttrack models
            item = self.listView.item(index).flighttrack_model
            self.waypoints_modelList.append(item)

        for count in range(len(self.waypoints_modelList)):
            waypoints_list = []
            dict[str(self.waypoints_modelList[count])] = {}
            for wp in self.waypoints_modelList[count].all_waypoint_data():
                waypoints_list.append((wp.lat, wp.lon,
                                       wp.flightlevel, wp.location, wp.comments))
            dict[str(self.waypoints_modelList[count])]["waypoints_list"] = waypoints_list

        for key in dict:   # Draw inactive flighttracks
            if str(key) != str(self.active_flight_track):
                patch = MultipleFlightpath(self.view.map, dict[key]["waypoints_list"])
                self.inactiveTrackPatches.append(patch)

    def removen(self):
        for pp in range(len(self.inactiveTrackPatches)):
            if self.inactiveTrackPatches[pp] is not None:
                self.inactiveTrackPatches[pp].remove()
        self.inactiveTrackPatches = []
