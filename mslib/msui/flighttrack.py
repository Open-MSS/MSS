"""Data model representing a flight track. The model is derived from
QAbstractTableModel, so that it can directly be connected to any Qt view.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

This file is part of the DLR/IPA Mission Support System User Interface (MSUI).

For better understanding of the code, compare to the 'ships' example
from chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
Definitive Guide to PyQt Programming' (Mark Summerfield).

The model includes a method for computing the distance between waypoints
and for the entire flight track.

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
from datetime import datetime, timedelta

import os
import pickle
import csv
import logging
import xml.dom.minidom


# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings
from PyQt4.QtCore import QString, QVariant, Qt, QModelIndex, SIGNAL, QAbstractTableModel
from PyQt4.QtGui import QItemDelegate, QComboBox
import numpy as np

# local application imports
from mslib import mss_util
from mslib import thermolib
from mslib.mss_util import config_loader
from mslib.msui import constants
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default


"""
CONSTANTS (used in this module)
"""
# Constants for identifying the table columns when the WaypointsTableModel is
# used with a QTableWidget.
LOCATION, LAT, LON, FLIGHTLEVEL, PRESSURE = range(5)


def secToStr(seconds):
    """Format a time given in seconds to a string HH:MM:SS. Used for the
       'leg time/cum. time' columns of the table view.
    """
    hours, seconds = divmod(int(seconds), 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)


TABLE_FULL = [
    ("Location                   ", lambda waypoint: waypoint.location, True),
    ("Lat\n(+-90)", lambda waypoint: waypoint.lat, True),
    ("Lon\n(+-180)", lambda waypoint: waypoint.lon, True),
    ("Flightlevel", lambda waypoint: waypoint.flightlevel, True),
    ("Pressure\n(hPa)", lambda waypoint: "%.2f" % (waypoint.pressure / 100.), False),
    ("Leg dist.\n(km [nm])", lambda waypoint: "%d [%d]" % (waypoint.distance_to_prev,
                                                           waypoint.distance_to_prev / 1.852), False),
    ("Cum. dist.\n(km [nm])", lambda waypoint: "%d [%d]" % (waypoint.distance_total,
                                                            waypoint.distance_total / 1.852), False),
    ("Leg time", lambda waypoint: secToStr(waypoint.leg_time), False),
    ("Cum. time", lambda waypoint: secToStr(waypoint.cum_time), False),
    ("Time (UTC)", lambda waypoint: waypoint.utc_time.strftime("%Y-%m-%d %H:%M:%S"), False),
    ("Rem. fuel\n(lb)", lambda waypoint: ("%d" % waypoint.rem_fuel), False),
    ("Aircraft\nweight (lb)", lambda waypoint: ("%d" % waypoint.weight), False),
    ("Comments                        ", lambda waypoint: waypoint.comments, True),
]

TABLE_SHORT = [TABLE_FULL[_i] for _i in range(7)] + [TABLE_FULL[-1]] + [("", lambda _: "", False)] * 6


"""
CLASS Waypoint
"""


class Waypoint(object):
    """Represents a waypoint with position, altitude and further
       properties. Used internally by WaypointsTableModel.
    """

    def __init__(self, lat=0, lon=0, flightlevel=0, location="", comments=""):
        self.location = location
        locations = config_loader(dataset='locations', default=mss_default.locations)
        if location in locations.keys():
            self.lat, self.lon = locations[location]
        else:
            self.lat = lat
            self.lon = lon
        self.flightlevel = flightlevel
        self.pressure = thermolib.flightlevel2pressure(flightlevel)
        self.comments = comments
        self.distance_to_prev = 0.
        self.distance_total = 0.

        # Performance fields (for values read from the flight performance
        # service).
        self.leg_time = None  # time from previous waypoint
        self.cum_time = None  # total time of flight
        self.utc_time = None  # time in UTC since given takeoff time
        self.leg_fuel = None  # fuel consumption since previous waypoint
        self.rem_fuel = None  # total fuel consumption
        self.weight = None  # aircraft gross weight

        self.wpnumber_major = None
        self.wpnumber_minor = None

    def get_comments(self):
        return self._comments

    def set_comments(self, string):
        if type(string) is str:
            self._comments = QString(string)
        else:
            self._comments = string

    comments = property(get_comments, set_comments)

    def __str__(self):
        """String representation of the waypoint (e.g., when used with the print
           statement).
        """
        return "WAYPOINT(LAT=%f, LON=%f, FL=%f)" % (self.lat, self.lon,
                                                    self.flightlevel)


class WaypointsTableModel(QAbstractTableModel):
    """Qt-QAbstractTableModel-derived data structure representing a flight
       track composed of a number of waypoints.

    Objects of this class can be directly connected to any Qt view that is
    able to handle tables models.

    Provides methods to store and load the model to/from an XML file, to compute
    distances between the individual waypoints, and to interpret the results of
    flight performance calculations.
    """

    def __init__(self, name="", filename=None, waypoints=None):
        super(WaypointsTableModel, self).__init__()
        self.name = name  # a name for this flight track
        self.filename = filename  # filename for store/load
        self.modified = False  # for "save on exit"
        self.waypoints = []  # user-defined waypoints

        # self.aircraft.setErrorHandling("permissive")
        self.settingsfile = os.path.join(constants.MSS_CONFIG_PATH, "mss.performance.cfg")
        self.loadSettings()

        # If a filename is passed to the constructor, load data from this file.
        if filename:
            if filename.endswith(".ftml"):
                self.loadFromFTML(filename)
            else:
                logging.debug("No known file extension! {:}".format(filename))

        if waypoints:
            self.replaceWaypoints(waypoints)

    def loadSettings(self):
        """Load settings from the file self.settingsfile.
        """
        if os.path.exists(self.settingsfile):
            logging.debug("loading settings from %s" % self.settingsfile)
            with open(self.settingsfile, "r") as fileobj:
                self.performance_settings = pickle.load(fileobj)
        else:
            self.performance_settings = DEFAULT_PERFORMANCE

    def saveSettings(self):
        """Save the current settings (map appearance) to the file
           self.settingsfile.
        """
        # TODO: ConfigParser and a central configuration file might be the better solution than pickle.
        # http://stackoverflow.com/questions/200599/whats-the-best-way-to-store-simple-user-settings-in-python
        logging.debug("storing settings to %s" % self.settingsfile)
        with open(self.settingsfile, "w") as fileobj:
            pickle.dump(self.performance_settings, fileobj)

    def setName(self, name):
        self.name = name
        self.modified = True

    def performanceValid(self):
        return self.performance_valid

    def flags(self, index):
        """Used to specify which table columns can be edited by the user;
           overrides the corresponding QAbstractTableModel method.

        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        column = index.column()
        table = TABLE_SHORT
        if self.performance_settings["visible"]:
            table = TABLE_FULL
        if table[column][2]:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable)
        else:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index))

    def data(self, index, role=Qt.DisplayRole):
        """Return a data field at the given index (of type QModelIndex,
           specifying row and column); overrides the corresponding
           QAbstractTableModel method.

        NOTE: Other roles (e.g. for display appearence) could be specified in
        this method as well. Cf. the 'ships' example in chapter 14/16 of 'Rapid
        GUI Programming with Python and Qt: The Definitive Guide to PyQt
        Programming' (Mark Summerfield).
        """
        waypoints = self.waypoints

        if not index.isValid() or \
                not (0 <= index.row() < len(waypoints)):
            return QVariant()
        waypoint = waypoints[index.row()]
        column = index.column()
        if role == Qt.DisplayRole:
            if self.performance_settings["visible"]:
                return QVariant(TABLE_FULL[column][1](waypoint))
            else:
                return QVariant(TABLE_SHORT[column][1](waypoint))
        elif role == Qt.TextAlignmentRole:
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
        return QVariant()

    def waypointData(self, row):
        """Get the waypoint object defining the given row.
        """
        return self.waypoints[row]

    def allWaypointData(self):
        """Return the entire list of waypoints.
        """
        return self.waypoints

    def intermediatePoints(self, numpoints=101, connection="greatcircle"):
        """Compute intermediate points between the waypoints.

        See mss_util.path_points() for additional arguments.

        Returns lats, lons.
        """
        path = [[wp.lat, wp.lon] for wp in self.waypoints]
        lats, lons = mss_util.path_points(
            path, numpoints=numpoints, connection=connection)
        return lats, lons

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return data describing the table header; overrides the
           corresponding QAbstractTableModel method.
        """
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return QVariant()
        # Return the names of the table columns.
        if orientation == Qt.Horizontal:
            if self.performance_settings["visible"]:
                return QVariant(TABLE_FULL[section][0])
            else:
                return QVariant(TABLE_SHORT[section][0])
        # Table rows (waypoints) are labelled with their number (= number of
        # waypoint).
        return QVariant(int(section))

    def rowCount(self, index=QModelIndex()):
        """Number of waypoints in the model.
        """
        return len(self.waypoints)

    def columnCount(self, index=QModelIndex()):
        return len(TABLE_FULL)

    def setData(self, index, value, role=Qt.EditRole, update=True):
        """Change a data element of the flight track; overrides the
           corresponding QAbstractTableModel method.

        NOTE: Performance computations loose their validity if a change is made.
        """
        if index.isValid() and 0 <= index.row() < len(self.waypoints):
            # print "\n>> SetData()"
            waypoint = self.waypoints[index.row()]
            column = index.column()
            index2 = index  # in most cases only one field is being changed
            if column == LOCATION:
                waypoint.location = value.toString()
            elif column == LAT:
                # In Qt4.6 and higher, value.toFloat() is available:
                # value, ok = value.toFloat()
                # For lower versions, we need to use try..except.
                try:
                    value, ok = float(value.toString()), True
                except:
                    ok = False
                if ok:
                    waypoint.lat = value
                    # A change of position requires an update of the distances.
                    if update:
                        self.update_distances(index.row())
                    # Notify the views that items between the edited item and
                    # the distance item of the corresponding waypoint have been
                    # changed.
                    # Delete the location name -- it won't be valid anymore
                    # after its coordinates have been changed.
                    waypoint.location = ""
                    index2 = self.createIndex(index.row(), LOCATION)
            elif column == LON:
                try:
                    value, ok = float(value.toString()), True
                except:
                    ok = False
                if ok:
                    waypoint.lon = value
                    if update:
                        self.update_distances(index.row())
                    waypoint.location = ""
                    index2 = self.createIndex(index.row(), LOCATION)
            elif column == FLIGHTLEVEL:
                try:
                    value, ok = float(value.toString()), True
                except:
                    ok = False
                if ok:
                    waypoint.flightlevel = value
                    waypoint.pressure = thermolib.flightlevel2pressure(value)
                    if update:
                        self.update_distances(index.row())
                    # need to notify view of the second item that has been
                    # changed as well.
                    index2 = self.createIndex(index.row(), PRESSURE)
            elif column == PRESSURE:
                try:
                    value, ok = float(value.toString()), True
                except:
                    ok = False
                if ok:
                    waypoint.pressure = value
                    waypoint.flightlevel = int(thermolib.pressure2flightlevel(value))
                    if update:
                        self.update_distances(index.row())
                    index2 = self.createIndex(index.row(), FLIGHTLEVEL)
            else:
                waypoint.comments = value.toString()
            self.modified = True
            # Performance computations loose their validity if a change is made.
            self.performance_valid = False
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                      index, index2)
            return True
        return False

    def insertRows(self, position, rows=1, index=QModelIndex(),
                   waypoints=[None]):
        """Insert waypoint; overrides the corresponding QAbstractTableModel
           method.
        """
        self.beginInsertRows(QModelIndex(), position,
                             position + rows - 1)
        for row in range(rows):
            wp = waypoints[row] if waypoints[row] else Waypoint(0, 0, 0)
            self.waypoints.insert(position + row, wp)

        self.update_distances(position, rows=rows)
        self.endInsertRows()
        self.modified = True
        return True

    def removeRows(self, position, rows=1, index=QModelIndex()):
        """Remove waypoint; overrides the corresponding QAbstractTableModel
           method.
        """
        # beginRemoveRows emits rowsAboutToBeRemoved(index, first, last).
        self.beginRemoveRows(QModelIndex(), position,
                             position + rows - 1)
        self.waypoints = self.waypoints[:position] + self.waypoints[position + rows:]
        if position < len(self.waypoints):
            self.update_distances(position, rows=min(rows, len(self.waypoints) - position))

        # endRemoveRows emits rowsRemoved(index, first, last).
        self.endRemoveRows()
        self.modified = True
        return True

    def update_distances(self, position, rows=1):
        """Update all distances in a flight track that are affected by a
           waypoint change involving <rows> waypoints starting at index
           <position>.

        Distances are computed along great circles.

        If rows=1, the distance to the previous waypoint is updated for
        waypoints <position> and <position+1>. The total flight track distance
        is updated for all waypoint following <position>.

        If rows>1, the distances to the previous waypoints are updated
        according to the number of modified waypoints.
        """
        waypoints = self.waypoints

        def get_duration_fuel(flightlevel0, flightlevel1, distance, weight):
            aircraft = self.performance_settings["aircraft"]
            if flightlevel0 == flightlevel1:
                tas, fuelflow = aircraft.cruisePerformance(flightlevel0 * 100, weight)
                duration = 3600. * distance / (1.852 * tas)  # convert to s (tas is in nm/h)
                leg_fuel = duration * fuelflow / 3600.
                return duration, leg_fuel
            else:
                if flightlevel0 < flightlevel1:
                    duration0, dist0, fuel0 = aircraft.climbPerformance(flightlevel0 * 100, weight)
                    duration1, dist1, fuel1 = aircraft.climbPerformance(flightlevel1 * 100, weight)
                else:
                    duration0, dist0, fuel0 = aircraft.descentPerformance(flightlevel0 * 100, weight)
                    duration1, dist1, fuel1 = aircraft.descentPerformance(flightlevel1 * 100, weight)
                duration = (duration1 - duration0) * 60  # convert from min to s
                dist = (dist1 - dist0) * 1.852  # convert from nm to km
                fuel = fuel1 - fuel0
                duration_p, fuel_p = get_duration_fuel(flightlevel1, flightlevel1, distance - dist, weight)
                return duration + duration_p, fuel + fuel_p

        pos = position
        for offset in range(rows):
            pos = position + offset
            wp1 = waypoints[pos]
            # The distance to the first waypoint is zero.
            if pos == 0:
                wp1.distance_to_prev = 0.
                wp1.distance_total = 0.

                wp1.leg_time = 0  # time from previous waypoint
                wp1.cum_time = 0  # total time of flight
                wp1.utc_time = self.performance_settings["takeoff_time"].toPyDateTime()
                wp1.weight = self.performance_settings["takeoff_weight"]
                wp1.leg_fuel = 0
                wp1.rem_fuel = self.performance_settings["fuel"]
            else:
                wp0 = waypoints[pos - 1]
                wp1.distance_to_prev = mss_util.get_distance((wp0.lat, wp0.lon),
                                                             (wp1.lat, wp1.lon))

                time, fuel = get_duration_fuel(wp0.flightlevel, wp1.flightlevel, wp1.distance_to_prev, wp0.weight)
                wp1.leg_time = time
                wp1.cum_time = wp0.cum_time + wp1.leg_time
                wp1.utc_time = wp0.utc_time + timedelta(seconds=wp1.leg_time)
                wp1.leg_fuel = fuel
                wp1.rem_fuel = wp0.rem_fuel - wp1.leg_fuel
                wp1.weight = wp0.weight - wp1.leg_fuel

        # Update the distance of the following waypoint as well.
        if pos < len(waypoints) - 1:
            wp2 = waypoints[pos + 1]
            wp2.distance_to_prev = mss_util.get_distance((wp1.lat, wp1.lon),
                                                         (wp2.lat, wp2.lon))

        # Update total distances of waypoint at index position and all
        # following waypoints.
        for i in range(max(min(position, 1), 1), len(waypoints)):
            wp0 = waypoints[i - 1]
            wp1 = waypoints[i]
            wp1.distance_total = wp0.distance_total + wp1.distance_to_prev
            wp1.weight = wp0.weight - wp0.leg_fuel
            time, fuel = get_duration_fuel(wp0.flightlevel, wp1.flightlevel, wp1.distance_to_prev, wp0.weight)

            wp1.leg_time = time
            wp1.cum_time = wp0.cum_time + wp1.leg_time
            wp1.utc_time = wp0.utc_time + timedelta(seconds=wp1.leg_time)
            wp1.leg_fuel = fuel
            wp1.rem_fuel = wp0.rem_fuel - wp1.leg_fuel
            wp1.weight = wp0.weight - wp1.leg_fuel

    def invertDirection(self):
        logging.debug("WARNING: Inverting waypoints will not invert performance waypoints!")
        self.waypoints = self.waypoints[::-1]
        if len(self.waypoints) > 0:
            self.waypoints[0].distance_to_prev = 0
            self.waypoints[0].distance_total = 0
        for i in range(1, len(self.waypoints)):
            wp_comm = str(self.waypoints[i].comments)
            if len(wp_comm) == 9 and wp_comm.startswith("Hexagon "):
                wp_comm = "Hexagon {:d}".format(8 - int(wp_comm[-1]))
                self.waypoints[i].comments = QString(wp_comm)
        self.update_distances(position=0, rows=len(self.waypoints))

    def replaceWaypoints(self, new_waypoints):
        self.waypoints = []
        self.insertRows(0, rows=len(new_waypoints), waypoints=new_waypoints)

    def saveToFTML(self, filename=None):
        """Save the flight track to an XML file.

        Arguments:
        filename -- complete path to the file to save. If None, a previously
                    specified filename will be used. If no filename has been
                    specified at all, a ValueError exception will be raised.
        """
        if filename:
            self.filename = filename
        if not self.filename:
            raise ValueError("filename to save flight track cannot be None")

        doc = xml.dom.minidom.Document()

        ft_el = doc.createElement("FlightTrack")
        doc.appendChild(ft_el)

        # Element that contains the name of the flight track.
        name_el = doc.createElement("Name")
        name_el.appendChild(doc.createTextNode(self.name))
        ft_el.appendChild(name_el)

        # The list of waypoint elements.
        wp_el = doc.createElement("ListOfWaypoints")
        ft_el.appendChild(wp_el)

        for wp in self.waypoints:
            element = doc.createElement("Waypoint")
            wp_el.appendChild(element)
            element.setAttribute("location", str(wp.location))
            element.setAttribute("lat", str(wp.lat))
            element.setAttribute("lon", str(wp.lon))
            element.setAttribute("flightlevel", str(wp.flightlevel))
            comments = doc.createElement("Comments")
            comments.appendChild(doc.createTextNode(str(wp.comments)))
            element.appendChild(comments)

        file_object = open(self.filename, 'w')
        doc.writexml(file_object, indent="  ", addindent="  ", newl="\n")
        file_object.close()

    def loadFromFTML(self, filename):
        """Load a flight track from an XML file at <filename>.
        """
        doc = xml.dom.minidom.parse(filename)

        ft_el = doc.getElementsByTagName("FlightTrack")[0]

        name_el = ft_el.getElementsByTagName("Name")[0]
        self.name = name_el.childNodes[0].data.strip()

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
                comments = unicode('')

            waypoints_list.append(Waypoint(lat, lon, flightlevel,
                                           location=location,
                                           comments=comments))
        self.replaceWaypoints(self, waypoints_list)

    def getFilename(self):
        return self.filename


"""
CLASS  WaypointDelegate
"""


class WaypointDelegate(QItemDelegate):
    """Qt delegate class for the appearance of the table view. Based on the
       'ships' example in chapter 14/16 of 'Rapid GUI Programming with Python
       and Qt: The Definitive Guide to PyQt Programming' (Mark Summerfield).
    """

    def __init__(self, parent=None):
        super(WaypointDelegate, self).__init__(parent)
        self.viewParent = parent

    def paint(self, painter, option, index):
        """Colours waypoints with a minor waypoint number (i.e. intermediate
           waypoints generated by the flight performance service) in red.
        """
        wpnumber_minor = index.model().waypointData(index.row()).wpnumber_minor
        if wpnumber_minor > 0:
            newpalette = QtGui.QPalette(option.palette)
            colour = QtGui.QColor(170, 0, 0)  # dark red
            newpalette.setColor(QtGui.QPalette.Text, colour)
            colour = QtGui.QColor(255, 255, 0)  # yellow
            newpalette.setColor(QtGui.QPalette.HighlightedText, colour)
            option.palette = newpalette
        QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        """Create a combobox listing predefined locations in the LOCATION
           column.
        """
        if index.column() == LOCATION:
            combobox = QComboBox(parent)
            locations = config_loader(dataset='locations', default=mss_default.locations)
            adds = locations.keys()
            if self.viewParent is not None:
                for loc in [wp.location for wp in self.viewParent.waypoints_model.allWaypointData() if
                            wp.location != ""]:
                    if loc not in adds:
                        adds.append(loc)
                adds = sorted(adds)
            combobox.addItems(adds)

            combobox.setEditable(True)
            return combobox
        else:
            # All other columns get the standard editor.
            return QItemDelegate.createEditor(self, parent, option,
                                              index)

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole).toString()
        if index.column() in (LOCATION,):
            i = editor.findText(text)
            if i == -1:
                i = 0
            editor.setCurrentIndex(i)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        """For the LOCATION column: If the user selects a location from the
           combobox, get the corresponding coordinates.
        """
        if index.column() == LOCATION:
            loc = str(editor.currentText())
            locations = config_loader(dataset='locations', default=mss_default.locations)
            if loc in locations.keys():
                lat, lon = locations[loc]
                # Don't update distances and flight performance twice, hence
                # set update=False for LAT.
                model.setData(index.sibling(index.row(), LAT), QVariant(lat),
                              update=False)
                model.setData(index.sibling(index.row(), LON), QVariant(lon))
            else:
                for wp in self.viewParent.waypoints_model.allWaypointData():
                    if loc == wp.location:
                        lat, lon = wp.lat, wp.lon
                        # Don't update distances and flight performance twice, hence
                        # set update=False for LAT.
                        model.setData(index.sibling(index.row(), LAT), QVariant(lat),
                                      update=False)
                        model.setData(index.sibling(index.row(), LON), QVariant(lon))

            model.setData(index, QVariant(editor.currentText()))
        else:
            QItemDelegate.setModelData(self, editor, model, index)
