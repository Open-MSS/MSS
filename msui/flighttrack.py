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
import xml.dom.minidom
import logging
import urllib2
import csv
from datetime import datetime

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
from geopy import distance

# local application imports
from mslib import mss_util
from mslib import thermolib
import mss_settings


################################################################################
###                    CONSTANTS (used in this module)                       ###
################################################################################

# Constants for identifying the table columns when the WaypointsTableModel is
# used with a QTableWidget.
LOCATION, \
LAT, \
LON, \
FLIGHTLEVEL, \
PRESSURE, \
SPEED, \
TIME_LEG, \
TIME_CUM, \
TIME_UTC, \
DISTANCE_LEG, \
DISTANCE_CUM, \
FUEL_LEG, \
FUEL_CUM, \
WEIGHT, \
COMMENTS = range(15)

# Internal mode of the WaypointsTableModel.
USER = 0
PERFORMANCE = 1

# Predefined locations for the table (names and coordinates of the places that
# can be selected in the table view when double-clicking in the "location"
# column).
locations = mss_settings.locations


################################################################################
###                           CLASS Waypoint                                 ###
################################################################################

class Waypoint(object):
    """Represents a waypoint with position, altitude and further
       properties. Used internally by WaypointsTableModel.
    """
    def __init__(self, lat=0, lon=0, flightlevel=0, location="", comments=""):
        self.location = location
        if location in locations.keys():
            self.lat, self.lon = locations[location]
        else:
            self.lat = lat
            self.lon = lon
        self.flightlevel = flightlevel
        self.pressure = thermolib.flightlevel2pressure(flightlevel)
        self.comments = QString(comments)
        self.distance_to_prev = 0.
        self.distance_total = 0.

        # Performance fields (for values read from the flight performance
        # service).
        self.leg_time = None # time from previous waypoint
        self.cum_time = None # total time of flight
        self.utc_time = None # time in UTC since given takeoff time
        self.leg_fuel = None # fuel consumption since previous waypoint
        self.cum_fuel = None # total fuel consumption
        self.weight = None   # aircraft gross weight
        self.speed = None    # cruise speed/mode

        self.wpnumber_major = None
        self.wpnumber_minor = None
        

    def __str__(self):
        """String representation of the waypoint (e.g., when used with the print
           statement).
        """
        return "WAYPOINT(LAT=%f, LON=%f, FL=%f)" % (self.lat, self.lon, 
                                                    self.flightlevel)


################################################################################
###                     CLASS WaypointsTableModel                            ###
################################################################################

class WaypointsTableModel(QAbstractTableModel):
    """Qt-QAbstractTableModel-derived data structure representing a flight
       track composed of a number of waypoints.

    Objects of this class can be directly connected to any Qt view that is
    able to handle tables models.

    Provides methods to store and load the model to/from an XML file, to compute
    distances between the individual waypoints, and to interpret the results of
    a flight performance web service query. Internally, the structure keeps two
    lists of waypoints -- (1) as defined by the user (self.waypoints; if mode ==
    USER) and (2) as obtained from a flight performance service query (the
    results may contain additional waypoints in ascend/descend segments;
    self.performance_waypoints; if mode == PERFORMANCE).
    """

    def __init__(self, name="", filename=None):
        super(WaypointsTableModel, self).__init__()
        self.name = name # a name for this flight track
        self.filename = filename # filename for store/load
        self.modified = False # for "save on exit"
        self.waypoints = [] # user-defined waypoints
        self.performance_waypoints = [] # waypoints from performance service
        self.performance_valid = False # performance results become invalid if
                                       # the user changes a waypoint
        self.performance_remaining_fuel_capacity = 0
        self.performance_remaining_range_nm = 0
        self.mode = USER # depending on the mode data from either user waypoints
                         # or performance waypoints are returned.

        # If a filename is passed to the constructor, load data from this file.
        if filename:
            if filename.endswith(".ftml"):
                self.loadFromFTML(filename)
            elif filename.endswith(".csv"):
                self.loadFromCSV(filename)
            elif filename.endswith(".txt"):
                self.loadFromText(filename)
            else:
                logging.debug("No known file extension! {:}".format(filename))



    def setName(self, name):
        self.name = name
        self.modified = True


    def setMode(self, mode):
        self.mode = mode
        #logging.debug("switching to mode %s." % ("USER" if mode == USER else "PERFORMANCE"))
        self.reset()


    def getMode(self):
        return self.mode


    def performanceValid(self):
        return self.performance_valid


    def flags(self, index):
        """Used to specify which table columns can be edited by the user;
           overrides the corresponding QAbstractTableModel method.
           
        PERFORMANCE mode is always read-only.  
        USER mode allows modification of LOCATION, LAT, LON, FLIGHTLEVEL,
        COMMENTS.
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        column = index.column()
        if column in [LOCATION, LAT, LON, FLIGHTLEVEL, COMMENTS] \
               and self.mode == USER:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                                Qt.ItemIsEditable)
            
        else:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index))


    def secToStr(self, sec):
        """Format a time given in seconds to a string HH:MM:SS. Used for the
           'leg time/cum. time' columns of the table view.
        """
        sec = int(sec)
        hours = sec / 3600
        sec = sec % 3600
        minutes = sec / 60
        sec = sec % 60
        return "%02i:%02i:%02i" % (hours, minutes, sec)


    def data(self, index, role=Qt.DisplayRole):
        """Return a data field at the given index (of type QModelIndex,
           specifying row and column); overrides the corresponding
           QAbstractTableModel method.

        NOTE: Other roles (e.g. for display appearence) could be specified in
        this method as well. Cf. the 'ships' example in chapter 14/16 of 'Rapid
        GUI Programming with Python and Qt: The Definitive Guide to PyQt
        Programming' (Mark Summerfield).
        """
        if self.mode == USER:
            waypoints = self.waypoints
        else:
            waypoints = self.performance_waypoints

        if not index.isValid() or \
           not (0 <= index.row() < len(waypoints)):
            return QVariant()
        waypoint = waypoints[index.row()]
        column = index.column()
        if role == Qt.DisplayRole:
            if column == LOCATION:
                return QVariant(waypoint.location)
            elif column == LAT:
                return QVariant(waypoint.lat)
            elif column == LON:
                return QVariant(waypoint.lon)
            elif column == FLIGHTLEVEL:
                return QVariant(waypoint.flightlevel)
            elif column == PRESSURE:
                return QVariant("%.2f" % (waypoint.pressure/100.))
            elif column == SPEED:
                return QVariant(waypoint.speed) \
                       if waypoint.speed is not None else QVariant("")
            elif column == TIME_LEG:
                return QVariant(self.secToStr(waypoint.leg_time)) \
                       if waypoint.leg_time is not None else QVariant("")
            elif column == TIME_CUM:
                return QVariant(self.secToStr(waypoint.cum_time)) \
                       if waypoint.cum_time is not None else QVariant("")
            elif column == TIME_UTC:
                return QVariant(waypoint.utc_time.strftime("%Y-%m-%d %H:%M:%S")) \
                       if waypoint.utc_time is not None else QVariant("")
            elif column == DISTANCE_LEG:
                # Return distance in km and nm.
                return QVariant("%.1f [%.1f]" % (waypoint.distance_to_prev,
                                                 waypoint.distance_to_prev / 1.852))
            elif column == DISTANCE_CUM:
                return QVariant("%.1f [%.1f]" % (waypoint.distance_total,
                                                 waypoint.distance_total / 1.852))
            elif column == FUEL_LEG:
                return QVariant("%.2f" % waypoint.leg_fuel) \
                       if waypoint.leg_fuel is not None else QVariant("")
            elif column == FUEL_CUM:
                return QVariant("%.2f" % waypoint.cum_fuel) \
                       if waypoint.cum_fuel is not None else QVariant("")
            elif column == WEIGHT:
                return QVariant("%.2f" % waypoint.weight) \
                       if waypoint.weight is not None else QVariant("")
            elif column == COMMENTS:
                return QVariant(waypoint.comments)
        elif role == Qt.TextAlignmentRole:
            return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
        return QVariant()


    def waypointData(self, row, mode=None):
        """Get the waypoint object defining the given row.
        """
        if mode is None: mode = self.mode
        if mode == USER:
            return self.waypoints[row]
        else:
            return self.performance_waypoints[row]


    def allWaypointData(self, mode=USER):
        """Return the entire list of waypoints.
        """
        if mode is None: mode = self.mode
        if mode == USER:
            return self.waypoints
        else:
            return self.performance_waypoints


    def intermediatePoints(self, numpoints=101, connection="greatcircle"):
        """Compute intermediate points between the waypoints.

        See mss_util.path_points() for additional arguments.

        Returns lats, lons.
        """
        path = [[wp.lat, wp.lon] for wp in self.waypoints]
        lats, lons = mss_util.path_points(path, numpoints=numpoints,
                                          connection=connection)
        return lats, lons
    

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return data describing the table header; overrides the
           corresponding QAbstractTableModel method.
        """
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
            return QVariant(int(Qt.AlignRight|Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return QVariant()
        # Return the names of the table columns.
        if orientation == Qt.Horizontal:
            if section == LOCATION:
                return QVariant("Location                   ")
            if section == LAT:
                return QVariant("Lat (+-90)")
            elif section == LON:
                return QVariant("Lon (+-180)")
            elif section == FLIGHTLEVEL:
                return QVariant("Flightlevel")
            elif section == PRESSURE:
                return QVariant("Pressure\n(hPa)")
            elif section == SPEED:
                return QVariant("Cruise mode") if self.mode == PERFORMANCE else QVariant("")
            elif section == TIME_LEG:
                return QVariant("Leg time") if self.mode == PERFORMANCE else QVariant("")
            elif section == TIME_CUM:
                return QVariant("Cum. time") if self.mode == PERFORMANCE else QVariant("")
            elif section == TIME_UTC:
                return QVariant("Time (UTC)") if self.mode == PERFORMANCE else QVariant("")
            elif section == DISTANCE_LEG:
                return QVariant("Leg dist.\n(km [nm])")
            elif section == DISTANCE_CUM:
                return QVariant("Cum. dist.\n(km [nm])")
            elif section == FUEL_LEG:
                return QVariant("Leg fuel\n(lb)") if self.mode == PERFORMANCE else QVariant("")
            elif section == FUEL_CUM:
                return QVariant("Cum. fuel\n(lb)") if self.mode == PERFORMANCE else QVariant("")
            elif section == WEIGHT:
                return QVariant("Aircraft\nweight (lb)") if self.mode == PERFORMANCE else QVariant("")
            elif section == COMMENTS:
                return QVariant("Comments                        ")
        # Table rows (waypoints) are labelled with their number (= number of
        # waypoint).
        if self.mode == USER:
            return QVariant(int(section))
        else:
            wp = self.performance_waypoints[int(section)]
            return ("%i" % wp.wpnumber_major) if wp.wpnumber_minor == 0 \
                   else ("%i.%i" % (wp.wpnumber_major, wp.wpnumber_minor))
        

    def rowCount(self, index=QModelIndex()):
        """Number of waypoints in the model.
        """
        if self.mode == USER:
            return len(self.waypoints)
        else:
            return len(self.performance_waypoints)


    def columnCount(self, index=QModelIndex()):
        return 15


    def setData(self, index, value, role=Qt.EditRole, update=True):
        """Change a data element of the flight track; overrides the
           corresponding QAbstractTableModel method.

        NOTE: Performance computations loose their validity if a change is made.
        """
        if index.isValid() and 0 <= index.row() < len(self.waypoints):
            #print "\n>> SetData()"
            waypoint = self.waypoints[index.row()]
            column = index.column()
            index2 = index # in most cases only one field is being changed
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
                    index2 = self.createIndex(index.row(), FUEL_CUM)
                    # Delete the location name -- it won't be valid anymore
                    # after its coordinates have been changed.
                    waypoint.location = ""
            elif column == LON:
                try:
                    value, ok = float(value.toString()), True
                except:
                    ok = False
                if ok:
                    waypoint.lon = value
                    if update:
                        self.update_distances(index.row())
                    index2 = self.createIndex(index.row(), FUEL_CUM)
                    waypoint.location = ""
            elif column == FLIGHTLEVEL:
                try:
                    value, ok = float(value.toString()), True
                except:
                    ok = False
                if ok:
                    waypoint.flightlevel = value
                    waypoint.pressure = thermolib.flightlevel2pressure(value)
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
                    waypoint.flightlevel = thermolib.pressure2flightlevel(value)
                    index2 = self.createIndex(index.row(), FLIGHTLEVEL)
            elif column == COMMENTS:
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
        self.waypoints = self.waypoints[:position] + \
                         self.waypoints[position + rows:]
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

        Distances are computed along great circles using the geopy library.

        If rows=1, the distance to the previous waypoint is updated for
        waypoints <position> and <position+1>. The total flight track distance
        is updated for all waypoint following <position>.

        If rows>1, the distances to the previous waypoints are updated
        according to the number of modified waypoints.
        """
        if self.mode == USER:
            waypoints = self.waypoints
        else:
            waypoints = self.performance_waypoints

        pos = position
        for offset in range(rows):
            pos = position + offset
            wp1 = waypoints[pos]
            # The distance to the first waypoint is zero.
            if pos == 0:
                wp1.distance_to_prev = 0.
                wp1.distance_total = 0.
            else:
                wp0 = waypoints[pos-1]
                wp1.distance_to_prev = distance.distance((wp0.lat, wp0.lon),
                                                         (wp1.lat, wp1.lon)).km
                
        # Update the distance of the following waypoint as well.
        if pos < len(waypoints)-1:
            wp2 = waypoints[pos+1]
            wp2.distance_to_prev = distance.distance((wp1.lat, wp1.lon),
                                                     (wp2.lat, wp2.lon)).km

        # Update total distances of waypoint at index position and all
        # following waypoints.
        for i in range(max(min(position, 1), 1), len(waypoints)):
            wp0 = waypoints[i-1]
            wp1 = waypoints[i]
            wp1.distance_total = wp0.distance_total + wp1.distance_to_prev

        #for wp in self.waypoints:
        #    print wp.lat, wp.lon, wp.distance_to_prev, wp.distance_total

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

        self.waypoints = []
        self.insertRows(0, rows=len(waypoints_list),
                        waypoints=waypoints_list)

    def saveToCSV(self, filename=None):
        if filename:
            self.filename = filename
        if not self.filename:
            raise ValueError("filename to save flight track cannot be None")
        with open(filename, "w") as out_file:
            csv_writer = csv.writer(out_file, dialect='excel')
            csv_writer.writerow([self.name])
            csv_writer.writerow(["Index", "Location", "Lat (+-90)", "Lon (+-180)", "Flightlevel", "Pressure (hPa)",
                                 "Leg dist. (km)", "Cum. dist. (km)", "Comments"])
            for i in range(len(self.waypoints)):
                wp = self.waypoints[i]
                loc = str(wp.location)
                lat = "{:.3f}".format(wp.lat)
                lon = "{:.3f}".format(wp.lon)
                lvl = "{:.3f}".format(wp.flightlevel)
                pre = "{:.3f}".format(wp.pressure / 100.)
                leg = "{:.3f}".format(wp.distance_to_prev)
                cum = "{:.3f}".format(wp.distance_total)
                com = str(wp.comments)
                csv_writer.writerow([i, loc, lat, lon, lvl, pre, leg, cum, com])


    def loadFromCSV(self, filename):
        waypoints_list = []
        with open(filename, "r") as in_file:
            csv_reader = csv.reader(in_file, dialect='excel')
            self.name = csv_reader.next()[0]
            header = csv_reader.next()
            for row in csv_reader:
                wp = Waypoint()
                wp.location = row[1]
                wp.lat = float(row[2])
                wp.lon = float(row[3])
                wp.flightlevel = float(row[4])
                wp.pressure = float(row[5]) * 100.
                wp.distance_to_prev = float(row[6])
                wp.distance_total = float(row[7])
                wp.comments = QString(row[8])
                waypoints_list.append(wp)
        self.waypoints = []
        self.insertRows(0, rows=len(waypoints_list),
                        waypoints=waypoints_list)

    def saveToText(self, filename=None):
        if filename:
            self.filename = filename
        if not self.filename:
            raise ValueError("filename to save flight track cannot be None")
        max_loc_len, max_com_len = len("Location"), len("Comments")
        for wp in self.waypoints:
            if len(str(wp.location)) > max_loc_len:
                max_loc_len = len(str(wp.location))
            if len(str(wp.comments)) > max_com_len:
                max_com_len = len(str(wp.comments))
        with open(filename, "w") as out_file:
            out_file.write("# Do not modify if you plan to import this file again!\n")
            out_file.write("Track name: {:}\n".format(self.name))
            line = "{0:5d}  {1:{2}}  {3:10.3f}  {4:11.3f}  {5:11.3f}  {6:14.3f}  {7:14.1f}  {8:15.1f}  {9:{10}}\n"
            header = "Index  {0:{1}}  Lat (+-90)  Lon (+-180)  Flightlevel  Pressure (hPa)  "\
                     "Leg dist. (km)  Cum. dist. (km)  {2:{3}}\n".format("Location", max_loc_len, "Comments", max_com_len)
            out_file.write(header)
            for i in range(len(self.waypoints)):
                wp = self.waypoints[i]
                loc = str(wp.location)
                lat = wp.lat
                lon = wp.lon
                lvl = wp.flightlevel
                pre = wp.pressure / 100.
                leg = wp.distance_to_prev
                cum = wp.distance_total
                com = str(wp.comments)
                out_file.write(line.format(i, loc, max_loc_len, lat, lon, lvl, pre, leg, cum, com, max_com_len))

    def loadFromText(self, filename):
        def loadFXtxt(filename):
            with open(filename, 'r') as f:
                lines = f.readlines()

            data = {
            'name':[],
            'loc':[],
            }
            for line in lines:
                if line.startswith('FWP'):
                   line = line.split( )
                   data['name'].append(line[3])
                   alt = round(float(line[-1])/100., 2)
                   if line[4] == 'N':
                       NS = 1.
                   elif line[4] =='S':
                       NS = -1.
                   else:
                       NS = np.nan
                   lat = round((float(line[5]) + float(line[6]) / 60.) * NS, 2)
                   if line[7] == 'E':
                       EW = 1.
                   elif line[7] =='W':
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
            for n,l in zip(data['name'], data['loc']):
                wp = Waypoint()
                wp.location = n
                setattr(wp, "lat", float(l[0]))
                setattr(wp, "lon", float(l[1]))
                setattr(wp, "flightlevel", float(l[2]))
                wp.pressure = thermolib.flightlevel2pressure(float(wp.flightlevel))
                waypoints_list.append(wp)
            self.name = filename.split('/')[-1].strip('.txt')

        else:
            with open(filename, "r") as in_file:
                pos = []
                for line in in_file:
                    if line.startswith("#"):
                        continue
                    if line.startswith("Index"):
                        pos.append(0) # 0
                        pos.append(line.find("Location")) # 1
                        pos.append(line.find("Lat (+-90)")) # 2
                        pos.append(line.find("Lon (+-180)")) # 3
                        pos.append(line.find("Flightlevel")) # 4
                        pos.append(line.find("Pressure (hPa)")) # 5
                        pos.append(line.find("Leg dist. (km)")) # 6
                        pos.append(line.find("Cum. dist. (km)")) # 7
                        pos.append(line.find("Comments")) # 8
                        continue
                    if line.startswith("Track name: "):
                        self.name = line.split(':')[1].strip()
                        continue
                    if pos == {}:
                        print "ERROR"
                    wp = Waypoint()
                    attr_names = ["location", "lat", "lon", "flightlevel",
                                  "pressure", "distance_to_prev", "distance_total",
                                  "comments"]
                    setattr(wp, attr_names[0], line[pos[1]:pos[2]].strip())
                    setattr(wp, attr_names[7], line[pos[8]:].strip())
                    for i in xrange(2, len(pos)-1):
                        if pos[i] >= 0:
                            if i == 5:
                                setattr(wp, attr_names[i-1],
                                        float(line[pos[i]:pos[i+1]].strip())*100.)
                            else:
                                setattr(wp, attr_names[i-1],
                                        float(line[pos[i]:pos[i+1]].strip()))
                        else:
                            if i == 5:
                                print('calculate pressure from FL ' + str(thermolib.flightlevel2pressure(float(wp.flightlevel))))
                                setattr(wp, attr_names[i-1],
                                        thermolib.flightlevel2pressure(float(wp.flightlevel)))
                    waypoints_list.append(wp)
        self.waypoints = []
        self.insertRows(0, rows=len(waypoints_list),
                        waypoints=waypoints_list)


    def getFilename(self):
        return self.filename


    def setAircraftStateList(self, ac_state_list):
        """Import the results of a performance computation of the v2 aircraft
        performance module (mslib.performance).
        """
        # Reset performance data. Also reset data model so that the
        # table doesn't try to draw the old performance values while
        # the new ones are read.
        self.performance_waypoints = []
        self.performance_valid = False
        self.performance_remaining_fuel_capacity = 0
        self.performance_remaining_range_nm = 0
        self.reset()

        for ac_state in ac_state_list:

            wp = Waypoint(ac_state.lat, ac_state.lon, ac_state.alt_ft / 100.)
            wp.speed    = ac_state.speed_desc
            wp.leg_fuel = ac_state.fuel_since_last_state_lbs
            wp.cum_fuel = ac_state.fuel_since_takeoff_lbs
            wp.weight   = ac_state.grossweight
            wp.leg_time = ac_state.timedelta_since_last_state.seconds
            wp.cum_time = ac_state.timedelta_since_takeoff.seconds
            wp.utc_time = ac_state.time_utc

            wp.wpnumber_major = ac_state.stateID
            wp.wpnumber_minor = 0

            if wp.wpnumber_minor == 0:
                wp.location = self.waypoints[wp.wpnumber_major].location
                wp.comments = self.waypoints[wp.wpnumber_major].comments

            self.performance_waypoints.append(wp)


        if len(ac_state_list) > 0:
            self.performance_remaining_fuel_capacity = \
                ac_state_list[-1].remaining_fuel_lbs
            self.performance_remaining_range_nm = \
                ac_state_list[-1].remaining_range_default_cruise_nm


        if len(self.performance_waypoints) > 0:
            mode = self.mode
            self.mode = PERFORMANCE
            self.update_distances(0, rows=self.rowCount())
            self.mode = mode
            self.performance_valid = True

        self.reset()
        self.emit(QtCore.SIGNAL("performanceUpdated()"))


    def setPerformanceComputation(self, performance_string):
        """Interprets the results of the flight performance computation
           service and sets the corresponding internal data fields.

        Arguments:
        performance_string -- multiline string (i.e. text file) with the
                              results of a flight performance service
                              computation.
        """
        # Reset performance data. Also reset data model so that the
        # table doesn't try to draw the old performance values while
        # the new ones are read.
        self.performance_waypoints = []
        self.performance_valid = False
        self.performance_remaining_fuel_capacity = 0
        self.performance_remaining_range_nm = 0
        self.reset()

        for line in performance_string.splitlines():
            line = line.strip()
            if line.startswith("#"):
                # Comment lines and other things.
                if line.startswith("#remaining_fuel_capacity="):
                    self.performance_remaining_fuel_capacity = \
                                      float(line.split("=")[1].split(" ")[0])
                if line.startswith("#approximate_range_with_remaining_fuel_capacity="):
                    self.performance_remaining_range_nm = \
                                      float(line.split("=")[1].split(" ")[0])
            elif line.startswith("ERROR"):
                logging.error(line)
                QtGui.QMessageBox.critical(None, "Flight Performance", 
                    "An error occured while computine the flight performance. "\
                    "The error message is:\n\n%s" % line,
                    QtGui.QMessageBox.Ok)

            elif len(line) > 0:
                try:
                    #ID,LON(deg),Lat(deg),FL(hft),SPEED,FUEL(lbs),FUEL_TOT(lbs),
                    #          GROSS WEIGHT(lbs),TIME(sec),TIME_TOT(sec),TIME_UTC
                    values = line.split(",")

                    wpnumber = values[0].split(".")
                    wpnumber_major = int(wpnumber[0])
                    wpnumber_minor = int(wpnumber[1]) if len(wpnumber)>1 else 0
                
                    lon, lat, fl = [float(f) for f in values[1:4]]
                    speed = values[4]

                    leg_fuel, cum_fuel, weight, leg_time, \
                         cum_time = [float(f) for f in values[5:10]]

                    utc_time = datetime.strptime(values[10], "%Y-%m-%dT%H:%M:%SZ")
                    
                    wp = Waypoint(lat, lon, fl)
                    wp.speed = speed
                    wp.leg_fuel = leg_fuel
                    wp.cum_fuel = cum_fuel
                    wp.weight = weight
                    wp.leg_time = leg_time
                    wp.cum_time = cum_time
                    wp.utc_time = utc_time

                    wp.wpnumber_major = wpnumber_major
                    wp.wpnumber_minor = wpnumber_minor

                    if wpnumber_minor == 0:
                        wp.location = self.waypoints[wpnumber_major].location
                        wp.comments = self.waypoints[wpnumber_major].comments

                    self.performance_waypoints.append(wp)

                except Exception as e:
                    logging.error("ERROR: cannot interpret line <<%s>>, skipping." % line)
                    logging.error("ERROR message is: %s" % e)

        if len(self.performance_waypoints) > 0:
            mode = self.mode
            self.mode = PERFORMANCE
            self.update_distances(0, rows=self.rowCount())
            self.mode = mode
            self.performance_valid = True

        self.reset()
        self.emit(QtCore.SIGNAL("performanceUpdated()"))


    def remainingRangeInfo(self):
        """Generates a string that contains information about the remaining
           fuel capacity and the approximate remaining range with this fuel
           (information available after a performance computation).
        """
        if len(self.performance_waypoints) == 0:
            return "NO PERFORMANCE DATA AVAILABLE."
        try:
            str = "Remaining fuel capacity ~ %i lb. Approximate "\
                "remaining range at FL250 ~ %i km (%i nm)" \
                % (self.performance_remaining_fuel_capacity,
                   self.performance_remaining_range_nm * 1.852,
                   self.performance_remaining_range_nm)
        except:
            str = ""
        return str
        

################################################################################
###                       CLASS  WaypointDelegate                            ###
################################################################################

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
            colour = QtGui.QColor(170, 0, 0) # dark red
            newpalette.setColor(QtGui.QPalette.Text, colour)
            colour = QtGui.QColor(255, 255, 0) # yellow
            newpalette.setColor(QtGui.QPalette.HighlightedText, colour)
            option.palette = newpalette
        QItemDelegate.paint(self, painter, option, index)


    def createEditor(self, parent, option, index):
        """Create a combobox listing predefined locations in the LOCATION
           column.
        """
        if index.column() == LOCATION:
            combobox = QComboBox(parent)
            adds = locations.keys()
            if self.viewParent is not None:
                for loc in [wp.location for wp in self.viewParent.waypoints_model.allWaypointData() if wp.location != ""]:
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
