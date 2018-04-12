# -*- coding: utf-8 -*-
"""

    mslib.msui.trajectory_item_tree
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tree model for trajectory items loaded into the trajectory tool and drawn
    on any views.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

from builtins import str

import datetime
import logging
import os
from mslib.utils import config_loader
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
# related third party imports
from mslib.msui.mss_qt import QtCore, QtGui
import numpy

try:
    import nappy
    HAVE_NAPPY = True
except ImportError:
    logging.warning("*** NAppy is not available. You will not be able to read NASA Ames files. ***")
    HAVE_NAPPY = False

from mslib.msui import lagranto_output_reader


class LagrantoTreeModelUnsupportedOperationError(Exception):
    """Exception class to handle wrong method arguments.
    """
    pass


class AbstractLagrantoDataItem(object):
    """Base class for all trajectory instances that are loaded into a
       trajectory tool.

    An AbstractLagrantoDataItem is a node in the tree of trajectory items
    that are drawn on any view. Hence, it has children and a parent. The
    class provides all methods required by Qt for display in a QTreeView.
    It also provides methods common to all trajectory items, including
    in which views it is visible.
    """

    def __init__(self, name, visible, parent=None):
        # Parent and children of the node in the tree.
        self.parentItem = parent
        self.childItems = []
        self.itemName = name
        self.hasMetadata = False

        # gxElements stores properties of the item, including colour,
        # line style and thickness, and plot instances of any view
        # (each view is free to store whatever it likes).
        self.gxElements = {}
        # List of views in which the item is visible. Each view is stored
        # by its identification string.
        self.views = []

        # If this item has a parent, register it as a child in the parent
        # node.
        if parent is not None:
            parent.appendChild(self)

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def treeViewData(self, column):
        """Return string data for display in the tree view.
        """
        if column == 0:
            # Item name.
            return self.itemName
        elif column == 1:
            # Connected views.
            return '; '.join(self.views)
        elif column == 2:
            # Item line properties (if not applicable return empty string).
            try:
                return str(self.gxElements['general']['colour']) + '/' + str(
                    self.gxElements['general']['linestyle']) + '/' + str(
                        self.gxElements['general']['linewidth'])
            except Exception as ex:
                logging.debug(u"caught a wildcard Exception: %s, %s", type(ex), ex)
                return ''
        elif column == 3:
            # Item markers.
            s = ''
            try:
                s += u'time({})'.format(self.gxElements['general']['timeMarkerInterval'].strftime('%H:%M'))
            except Exception as ex:
                logging.debug(u"caught a wildcard Exception: %s, %s", type(ex), ex)
            return s
        else:
            return ''

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem is not None:
            return self.parentItem.childItems.index(self)
        else:
            return 0

    def setVisibleInView(self, view_id, visible):
        """Set the visibility of this item in the view with the identifier
           <view_id>.
        """
        if visible:
            if view_id not in self.views:
                self.views.append(view_id)
                if self.parentItem:
                    self.parentItem.setVisibleInView(view_id, visible)
        else:
            if view_id in self.views:
                self.views.remove(view_id)

    def isVisible(self, view_id):
        """Is this item visible in the view with identifier <view_id>?
        """
        #         logging.debug("%s is visible on %s: %s" % (self.itemName,
        #                                                    view_id,
        #                                                    view_id in self.views))
        return view_id in self.views

    def getName(self):
        return self.itemName

    def isRoot(self):
        """Return True if item is the root item of a tree (ie., it has no
           parent).
        """
        return not self.parentItem

    def setGxElementProperty(self, element, eproperty, value):
        """
        """
        if element not in self.gxElements:
            self.gxElements[element] = {}
        self.gxElements[element][eproperty] = value

    def getGxElements(self):
        return self.gxElements

    def getGxElementProperty(self, element, eproperty):
        return self.gxElements[element][eproperty]

    def hasMetadata(self):
        return self.hasMetadata

    def getMetadata(self):
        """Return metadata dictionary of the item.

        This method is ABSTRACT and has to be implemented in the derived
        classes.
        """
        raise NotImplementedError("Abstract AbstractLagrantoDataItem.getMetadata called.")

    def getMetadataValue(self, key):
        """Return the value belonging to a metadata key.

        This method is ABSTRACT and has to be implemented in the derived
        classes.
        """
        raise NotImplementedError("Abstract AbstractLagrantoDataItem.getMetadataValue called.")


class LagrantoMapItem(AbstractLagrantoDataItem):
    """
    """

    def __init__(self, name, visible, parent=None):
        """
        """
        AbstractLagrantoDataItem.__init__(self, name, visible, parent)
        self.timeVariableChild = None
        self.lonVariableChild = None
        self.latVariableChild = None
        self.pressureVariableChild = None
        self.timeMarkerIndexes = None

        self.setGxElementProperty("general", "colour", None)
        self.setGxElementProperty("general", "linestyle", None)
        self.setGxElementProperty("general", "linewidth", None)
        self.setGxElementProperty("general", "timeMarkerInterval", None)

    def treeViewData(self, column):
        """Return string data for display in the tree view.

        Overrides AbstractLagrantoDataItem.treeViewData() to provide data
        for column 4 (start coordinates).
        """
        if column < 4:
            return AbstractLagrantoDataItem.treeViewData(self, column)
        elif column == 4:
            # Start coordinates from first elements of lon/lat/p variables.
            try:
                return "{:.2f}, {:.2f}, {:.1f}".format(
                    self.lonVariableChild.getVariableData()[0],
                    self.latVariableChild.getVariableData()[0],
                    self.pressureVariableChild.getVariableData()[0])
            except Exception as ex:
                logging.debug("Wildecard Exception %s - %s.", type(ex), ex)
                return ''
        else:
            return ''

    def getTimeVariable(self):
        """Return the child item that holds the time variable.
        """
        return self.timeVariableChild

    def getLonVariable(self):
        """Return the child item that holds the longitude variable.
        """
        return self.lonVariableChild

    def getLatVariable(self):
        """Return the child item that holds the latitude variable.
        """
        return self.latVariableChild

    def getPressureVariable(self):
        """Return the child item that holds the pressure variable.
        """
        return self.pressureVariableChild

    def getTimeMarkerIndexes(self):
        """Return an array containing the indexes of the time marker points.
        """
        return self.timeMarkerIndexes

    def setGxElementProperty(self, element, eproperty, value):
        """Overloads AbstractLagrantoDataItem.setGxElementProperty(). Calls
           the inherited method, and if the 'general' property
           'timeMarkerInterval' is set the data array indexes of the
           time markers are computed with __computeTimeMarkerPoints().
        """
        AbstractLagrantoDataItem.setGxElementProperty(self, element,
                                                      eproperty, value)
        if element == "general" and eproperty == "timeMarkerInterval":
            self.__computeTimeMarkerIndexes(value)
            try:
                self.timeSeriesPlotter.update()
            except Exception as ex:
                logging.debug("Wildecard Exception %s - %s.", type(ex), ex)
                pass

    def __computeTimeMarkerIndexes(self, requestedInterval):
        """Computes the indexes for the variable arrays at which time markers
           should be placed.

        The argument 'requestedInterval' is a datetime object representing the
        time interval between the marker points (e.g. three hours). If the
        requested time interval is smaller than the time distance between two
        points in the time variable, the interval value that's being used is
        set to this minumum value (this can be checked by comparing the
        requested value to the value that's contained in gxElements/general/
        timeMarkerInterval after this method has been called.

        A numpy.array containing the indexes (that can be used to index the
        lon/lat variables, for instance) is accessible via
        getTimeMarkerIndexes() after this method has been called.
        """
        #
        # Convert the requested interval from the datetime object to an int
        # value representing seconds.
        try:
            requestedInterval = requestedInterval.hour * 3600 + requestedInterval.minute * 60
        except Exception as ex:
            logging.debug("Wildecard Exception %s - %s.", type(ex), ex)
            pass

        #
        # If the requested time interval is zero or a None-tpye is passed,
        # no marker points will be computed.
        if not requestedInterval or requestedInterval == 0:
            self.timeMarkerIndexes = None
            self.gxElements["general"]["timeMarkerInterval"] = None
            return
        #
        # If this object (self) has no time variable skip the computation
        # of the indexes. The value of 'requestedInterval' will still be
        # stored in gxElements, so that it can be handed down to the
        # children.
        if not self.timeVariableChild:
            self.timeMarkerIndexes = None
            return

        #
        # Get the time variable of this object (which is returned in hours)
        # and convert to seconds (to get better accuracy in searchsorted()
        # below?!? Maybe it's not needed..).
        timeDataInSeconds = 3600. * self.timeVariableChild.getVariableData()
        #
        # Determine the mininum possible time interval (difference between to
        # data points in the time variable).
        minInterval = timeDataInSeconds[1] - timeDataInSeconds[0]

        #
        # The interval we'll use is the larger value of the two.
        interval = max(requestedInterval, minInterval)
        #
        # If we're not using the requested interval store the new interval value
        # to gxElements.
        if interval != requestedInterval:
            self.gxElements["general"]["timeMarkerInterval"].replace(hour=0,
                                                                     minute=0)
            self.gxElements["general"]["timeMarkerInterval"] += datetime.timedelta(seconds=interval)

        #
        # Compute the time marker times: arange from the first to the last data
        # point in the time variable, spacing is 'interval'.
        # Use min/max functions to handle backwards trajectories. In this case
        # the last element of timeDateInSeconds is smaller than the first,
        # which would lead to an empty list from arange.
        if timeDataInSeconds[-1] < 0:
            timeDataInSeconds = timeDataInSeconds[::-1]
        markerTimesInSeconds = numpy.arange(timeDataInSeconds[0],
                                            timeDataInSeconds[-1],
                                            interval)
        #
        # Find the indexes in the time variable array that correspond to these
        # times.
        self.timeMarkerIndexes = timeDataInSeconds.searchsorted(
            markerTimesInSeconds)

    def translateQueryString(self, qstring):
        """Translate a user query string containing %lon, %lat, %pres and %meta
           identifiers into a Python statement that can be evaluated with
           eval().

        The function replaces the %-identifiers by the appropriate Python
        statements that access the data.

        Arguments:
        qstring -- user query string.
        """
        qstring = qstring.replace('%lon',
                                  'self.lonVariableChild.getVariableData()[0]')
        qstring = qstring.replace('%lat',
                                  'self.latVariableChild.getVariableData()[0]')
        qstring = qstring.replace('%pres',
                                  'self.pressureVariableChild.getVariableData()[0]')
        qstring = qstring.replace('%meta', 'self.getMetadataValue')
        return qstring

    def query(self, qstring):
        """Evaluate the translated query string qstring. Note that the query
           must be translated into a Python statement by using
           'translateQueryString()' before calling this function.

        Arguments:
        qstring -- user query string.
        """
        return eval(qstring)


class FlightTrackItem(LagrantoMapItem):
    """Holds flight track data stored in a NASA Ames file.
    """

    def __init__(self, nasFileName, visible, parent=None):
        """Constructor.

        Arguments:
        nasFileName -- full path NASA Ames file
        visible,
            parent  -- inherited from LagrantoMapItem
        """
        LagrantoMapItem.__init__(self, os.path.basename(nasFileName),
                                 visible, parent)
        self.setGxElementProperty("general", "colour", "blue")
        self.setGxElementProperty("general", "linestyle", "-")
        self.setGxElementProperty("general", "linewidth", 1)

        self.nasFileName = nasFileName
        self.nafile = None
        self.__readNasaAmesFile()

        if self.nafile is None:
            logging.error("could not read NASA Ames file")
            raise RuntimeError("could not read NASA Ames file")

        #
        # Add all variable names contained in self.data as child nodes, so
        # that they are added to the tree view.
        variableNames = self.nafile.VNAME
        for variable in variableNames:
            FlightTrackVariableItem(variable, False, self)

        self.timeVariableChild = None
        for identifier in [self.nafile.XNAME[0]]:
            for item in self.childItems:
                if item.getName().find(identifier) >= 0:
                    self.timeVariableChild = item
                    logging.debug(u"identified time variable <%s>", item.getName())
                    #
                    # The time variable has to be modified a bit: convert
                    # seconds to hours and change the name correspondingly.
                    index = self.nafile.VNAME.index(item.getName())
                    self.nafile.V[index, :] = (self.nafile.V[index, :] / 3600.)
                    self.nafile.VNAME[index] = "(1/3600) * " + self.nafile.VNAME[index]
                    item.itemName = self.nafile.VNAME[index]
                    break
            if self.timeVariableChild is not None:
                break

        self.lonVariableChild = None
        for identifier in config_loader(dataset="traj_nas_lon_identifier", default=mss_default.traj_nas_lon_identifier):
            for item in self.childItems:
                if item.getName().upper().find(identifier) >= 0:
                    self.lonVariableChild = item
                    logging.debug(u"identified longitude variable <%s> with "
                                  u"identifier <%s>", item.getName(), identifier)
                    break
            if self.lonVariableChild is not None:
                break

        self.latVariableChild = None
        for identifier in config_loader(dataset="nas_lat_identifier", default=mss_default.traj_nas_lat_identifier):
            for item in self.childItems:
                if item.getName().upper().find(identifier) >= 0:
                    self.latVariableChild = item
                    logging.debug(u"identified latitude variable <%s> with "
                                  u"identifier <%s>", item.getName(), identifier)
                    break
            if self.latVariableChild is not None:
                break

        self.pressureVariableChild = None
        for identifier in config_loader(dataset="traj_nas_p_identifier", default=mss_default.traj_nas_p_identifier):
            for item in self.childItems:
                if item.getName().upper().find(identifier) >= 0:
                    self.pressureVariableChild = item
                    logging.debug(u"identified pressure variable <%s> with "
                                  u"identifier <%s>", item.getName(), identifier)
                    break
            if self.pressureVariableChild is not None:
                break

    def __readNasaAmesFile(self):
        """Read the NASA Ames file 'self.nasFileName'.
        """
        if not HAVE_NAPPY:
            self.nafile = None
            return
        #
        # Open the NASA Ames file and read the data.
        try:
            self.nafile = nappy.openNAFile(self.nasFileName)
            self.nafile.readData()
        except TypeError as ex:  # catch TypeError as nappy itself triggers Exception when raising
            self.nafile = None
            logging.error(u"%s %s", type(ex), ex)
            return
        #
        # Convert variable array of nafile from 'list' to 'NumPy array' for
        # faster access (the array can be large!).
        #  -- Should be moved to nappy, not a great solution..
        self.nafile.V = numpy.array(self.nafile.V)
        # independent variable
        self.nafile.X = numpy.array(self.nafile.X)

        # Convert to masked array to correctly handle missing values.
        Vtemp = []
        for i in range(self.nafile.V.shape[0]):
            Vtemp.append(numpy.ma.masked_values(self.nafile.V[i],
                                                self.nafile.VMISS[i]))
        # Append independent variable to list of variables. Independent
        # variables don't have a missing value, hence the dummy -9999.. here.
        # TODO: This should be revised; the individual FlightTrackVariableItem shouldn't
        #       access their parent's 'self.nafile.V' attribute to access the data;
        #       instead they should own their own data array.
        Vtemp.append(numpy.ma.masked_values(self.nafile.X,
                                            -99999999))
        self.nafile.VNAME.append(self.nafile.XNAME[0])

        self.nafile.V = numpy.ma.masked_array(Vtemp)

    def getMetadataValue(self, key):
        """Return the value belonging to a metadata key.

        Implements AbstractLagrantoDataItem.getMetadataValue(). Always returns
        None as flight track items have no metadata.
        """
        return None

    def getStartTime(self):
        """Return the start time of the trajectory as a datetime object.
        """
        # Get the date from the NASA Ames file as a list [YYYY, MM, DD].
        nas_date = self.nafile.getFileDates()[0]
        return datetime.datetime(nas_date[0], nas_date[1], nas_date[2])


class LagrantoOutputItem(LagrantoMapItem):
    """Holds all data stored in a Lagranto output directory.
    """

    def __init__(self, path, visible, parent=None):
        """Constructor.

        Arguments:
        path -- full path to directory in which Lagranto output files are
                stored
        visible,
        parent -- inherited from LagrantoMapItem
        """
        LagrantoMapItem.__init__(self, os.path.basename(os.path.normpath(path)),
                                 visible, parent)

        self.path = path
        self.loutput = None
        self.__readLagrantoOutput()

    def __readLagrantoOutput(self):
        """
        """
        #
        # Read the data via a LagrantoOutputReader object.
        self.loutput = lagranto_output_reader.LagrantoOutputReader(self.path)
        #
        # Instantiate a new TrajectoryItem for each trajectory read by
        # LagrantoOutputReader.
        for i, (trajectory, metadata) in enumerate(zip(self.loutput.data,
                                                       self.loutput.meta)):
            trname = "{:04d} ".format(i)
            if "startcoordinates" in metadata:
                trname += str(
                    [u"{:.2f}".format(r) for r in metadata["startcoordinates"]]).replace('\'', '')
            TrajectoryItem(trname, True, self, trajectory, metadata)


class TrajectoryItem(LagrantoMapItem):
    """Holds the data from an individual trajectory computed by Lagranto.

    Data is accessible as TrajectoryItem.data['varname']; all available
    variables can be queried with TrajectoryItem.data.keys().
    """

    def __init__(self, trajectoryname, visible, parent=None, trdata=None,
                 trmetadata=None):
        """Constructor.

        Arguments:
        trajectoryname -- name of the trajectory
        visible,
            parent -- inherited from LagrantoMapItem
        trdata   -- dictionary with trajectory data (trdata['varname'] ==
                    NumPy array)
        trmetadata -- trajectory metadata dictionary, as returned by
                      LagrantoOutputReader
        """
        LagrantoMapItem.__init__(self, trajectoryname, visible, parent)
        self.setGxElementProperty("general", "colour", "red")
        self.setGxElementProperty("general", "linestyle", "-")
        self.setGxElementProperty("general", "linewidth", 1)
        self.data = trdata
        self.metadata = trmetadata
        self.hasMetadata = True

        #
        # Add all variable names contained in self.data as child nodes, so
        # that they are added to the tree view.
        for variable in self.data:
            #
            # Per default, plot only variables listed here in a new time
            # series window.
            visible = variable in ['p', 'T', 'TH', 'RH']
            newItem = TrajectoryVariableItem(variable, visible, self)
            #
            # Remember the items that store time, lon, lat, pressure variables
            # for later access with getTimeVariable() etc.
            if variable == "time":
                self.timeVariableChild = newItem
                self.timeVariableChild.itemName += " [hr since " + \
                                                   self.getStartTime().strftime("%Y-%m-%d %H:%M UTC") + "]"
                self.data[self.timeVariableChild.itemName] = self.data[variable]
            elif variable == "lon":
                self.lonVariableChild = newItem
            elif variable == "lat":
                self.latVariableChild = newItem
            elif variable == "p":
                self.pressureVariableChild = newItem

    def treeViewData(self, column):
        """Return string data for display in the tree view.

        Overrides LagrantoMapItem.treeViewData() to provide data
        for columns 5 and 6 (start time & duration, metadata).
        """
        if column < 5:
            return LagrantoMapItem.treeViewData(self, column)
        elif column == 5:
            return "{} for {:f} hrs" \
                .format(self.getStartTime().strftime("%Y-%m-%d %H:%M UTC"),
                        self.timeVariableChild.getVariableData()[-1])
        elif column == 6:
            s = ''
            for key, value in self.metadata.items():
                if key not in ["starttime", "file", "starttime_filename",
                               "startcoordinates", "duration"]:
                    s += u"{} = {}, ".format(key, str(value))
            return s

    def getStartTime(self):
        """Return the start time of the trajectory as a datetime object.
        """
        try:
            return self.metadata["starttime"]
        except KeyError:
            return self.metadata["starttime_filename"]

    def getMetadata(self):
        """Return the metadata dictionary.

        This method implements AbstractLagrantoDataItem.getMetadata().
        """
        return self.metadata

    def getMetadataValue(self, key):
        """Return the value belonging to a metadata key.

        Implements AbstractLagrantoDataItem.getMetadataValue(). Returns None
        if the key is not contained in the metadata dictionary.
        """
        try:
            return self.metadata[key]
        except KeyError:
            return None


class AbstractVariableItem(AbstractLagrantoDataItem):
    """Tree node for variables contained in a flight track or trajectory file.
       Such variable can be visible on a time series plot, or they can be used
       to colour the track plotted on the map. Variable data are stored in
       flight track and trajectory nodes, and since these data fields can be
       large they shouldn't be copied into the variable nodes. Hence, only
       the name of the variables is stored locally (accessible via
       getVariableName()), and the data have to be made accessible by
       overloading getVariableData() in derived classes. The overloaded methods
       should then access the data structure of their parent and return the
       data, so that 'users' such as LagrantoMap or LagrantoTimeSeriesPlotter
       can use the common interface and not bother about the data is stored
       in respective parent nodes.
    """

    def __init__(self, name, visible, parent=None):
        """The constructor takes the same arguments as AbstractLagrantoDataItem.
           Only the constructor of the superclass is called.
        """
        AbstractLagrantoDataItem.__init__(self, name, visible, parent)

    def getVariableName(self):
        """Return the name of the variable.
        """
        return self.itemName

    def getVariableData(self):
        """Return the data associated with this variable. This method depends
           on the type of parent (ie. flight track or trajectory) and has
           to be overloaded in the derived class so that efficient data
           access is possible.

        This method is ABSTRACT and has to be implemented in the derived
        classes.
        """
        raise NotImplementedError("Abstract AbstractVariableNameItem.getVariableData called.")

    def exceedsThreshold(self, threshold=0.):
        """Determines time intervals in which the value of the variable
           exceeds a given threshold.

        Returns a list of two-element-lists of form
                        [ [ts1, te1], [ts2, te2], ..],
        where each two-element-list describes a time interval in which the
        value of the variables exceeds the given threshold.

        Arguments:
        threshold -- threshold to be exceeded. Default is 0.
        """
        myData = self.getVariableData()
        timeData = self.parentItem.getTimeVariable().getVariableData()

        aboveThreshold = False
        timeWindows = []
        for i, data in enumerate(myData):
            if not aboveThreshold and data > threshold:
                aboveThreshold = True
                windowStartTime = timeData[i]
            elif aboveThreshold and data <= threshold:
                aboveThreshold = False
                timeWindows.append([windowStartTime, timeData[i]])

        return timeWindows

    def setGxElementProperty(self, element, eproperty, value):
        """Overloads AbstractLagrantoDataItem.setGxElementProperty(). Calls
           the inherited method, and if the 'general' property
           'timeMarkerInterval' is set the data array indexes of the
           time markers are computed with __computeTimeMarkerPoints().
        """
        if element == "general":
            raise LagrantoTreeModelUnsupportedOperationError("Setting " + element + "/" + eproperty +
                                                             " is not supported by AbstractVariableItem.")
        else:
            AbstractLagrantoDataItem.setGxElementProperty(self, element,
                                                          eproperty, value)


class FlightTrackVariableItem(AbstractVariableItem):
    """
    """

    def getVariableData(self):
        """Return the data associated with this variable.

        Implements AbstractVariableItem.getVariableData().
        """
        naVNames = self.parentItem.nafile.VNAME
        index = naVNames.index(self.itemName)
        return self.parentItem.nafile.V[index, :]

    def getGxElementProperty(self, element, eproperty):
        """Return graphics properties (colour etc.) that are stored in the
           'general' element from the parent item.
        """
        if element == "general":
            return self.parentItem.getGxElementProperty(element, eproperty)
        else:
            return AbstractVariableItem.getGxElementProperty(self, element,
                                                             eproperty)


class TrajectoryVariableItem(AbstractVariableItem):
    """
    """

    def getVariableData(self):
        """Return the data associated with this variable.

        Implements AbstractVariableItem.getVariableData().
        """
        return self.parentItem.data[self.itemName]


class LagrantoMapItemsTreeModel(QtCore.QAbstractItemModel):
    """

    .. the model should know nothing about the kind of viewports which
       observe it..

    """

    def __init__(self, data=None, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)

        self.header = ['Items', 'Connected Views', 'Line Properties', 'Marker',
                       'Start [lon, lat, p]', 'Start Time', 'Metadata']

        self.rootItem = LagrantoMapItem("All items", True)
        self.rootFlightTracks = LagrantoMapItem("flight tracks", True,
                                                self.rootItem)
        self.rootTrajectories = LagrantoMapItem("trajectories", True,
                                                self.rootItem)

        self.lastChange = "INIT"

    def getRootItem(self):
        return self.rootItem

    def columnCount(self, parent):
        """Return number of columns to be displayed in the tree view.

        Implementation of QAbstractItemModel.columnCount(self,
        QModelIndex parent = QModelIndex()). Here, the number of columns
        is independent of the parent.
        """
        return len(self.header)

    def data(self, index, role):
        """Return data to be displayed in the tree view.
        """
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        item = index.internalPointer()

        return QtCore.QVariant(item.treeViewData(index.column()))

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        """Return descriptions of the columns ('sections') in the tree view
           for display in the header.
        """
        #
        # Return value has to be casted as QVariant.
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.header[section])

        return QtCore.QVariant()

    def index(self, row, column, parent):
        """
        Arguments:
        int row, column
        QModelIndex parent
        """
        if not ((0 <= row < self.rowCount(parent)) and (0 <= column < self.columnCount(parent))):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def addFlightTrack(self, flighttrack):
        """

        Arguments:
        flighttrack -- full path to NASA Ames file that contains the flight
                       track data.
        """
        #
        # Create a new FlightTrackItem as a child of self.rootFlightTracks,
        # create an index to return.
        newFlightTrackItem = FlightTrackItem(flighttrack, True,
                                             self.rootFlightTracks)
        index = self.createIndex(newFlightTrackItem.row(), 0,
                                 newFlightTrackItem)

        #
        # Emit dataChanged() (for LagrantoMap) and layoutChanged() (for
        # QTreeView) signals to inform event listeners about the changes
        # in the data structure. self.lastChange is set to "FLIGHT_TRACK_ADDED"
        # so LagrantoMap can query the kind of change that occured.
        self.lastChange = "FLIGHT_TRACK_ADDED"
        self.dataChanged.emit(index, index)
        self.layoutChanged.emit()

        return index

    def addTrajectoryDirectory(self, path):
        """

        Arguments:
        path -- full path to Lagranto output directory that contains the
                trajectory files (ls* and lsl*).
        """
        #
        # Create a new FlightTrackItem as a child of self.rootFlightTracks,
        # create an index to return.
        newLagrantoOutputItem = LagrantoOutputItem(path, True,
                                                   self.rootTrajectories)
        index = self.createIndex(newLagrantoOutputItem.row(), 0,
                                 newLagrantoOutputItem)

        #
        # Emit dataChanged() (for LagrantoMap) and layoutChanged() (for
        # QTreeView) signals to inform event listeners about the changes
        # in the data structure. self.lastChange is set to "FLIGHT_TRACK_ADDED"
        # so LagrantoMap can query the kind of change that occured.
        self.lastChange = "TRAJECTORY_DIR_ADDED"
        self.dataChanged.emit(index, index)
        self.layoutChanged.emit()

        return index

    def setItemVisibleInView(self, index, view_window, visible,
                             emit_change=True):
        """
        """
        if index.isValid():
            index.internalPointer().setVisibleInView(view_window.identifier,
                                                     visible)
            if emit_change:
                self.lastChange = "VISIBILITY_CHANGE"
                self.dataChanged.emit(index, index)
                self.layoutChanged.emit()

    def setItemVisibleInView_list(self, indices, view_window, visible,
                                  emit_change=True):
        """
        """
        for index in indices:
            if index.isValid():
                index.internalPointer().setVisibleInView(view_window.identifier,
                                                         visible)
            else:
                indices.remove(index)
        if emit_change:
            self.lastChange = "VISIBILITY_CHANGE"
            self.dataChanged.emit(indices[0], indices[-1])
            self.layoutChanged.emit()

    def emitChange(self, index1, index2, mode="GXPROPERTY_CHANGE"):
        self.lastChange = mode
        self.dataChanged.emit(index1, index2)
        self.layoutChanged.emit()

    def getLastChange(self):
        """Returns a description of the last change that has been made
           to the data structure. This method can be called from a listener
           that reacts to the 'dataChanged()' signal if information
           is needed about the type of change that occurred.

        Possible return values (strings) are:
            GXPROPERTY_CHANGE
            VISIBILITY_CHANGE
            TRAJECTORY_DIR_ADDED
            FLIGHT_TRACK_ADDED
            MARKER_CHANGE
        """
        return self.lastChange

    def changeItemGxProperty(self, index, element, eproperty, value):
        """Change a graphics property of the item given by index. Specify
           graphics element, property to be changed and the new value.
           The new value is set and 'dataChanged()' and 'layoutChanged()'
           signals are emitted in order to update a view.
        """
        if index.isValid():
            item = index.internalPointer()
            item.setGxElementProperty(element, eproperty, value)
            self.lastChange = "GXPROPERTY_CHANGE"
            self.dataChanged.emit(index, index)
            self.layoutChanged.emit()

    def changeItemGxProperty_list(self, indices, element, eproperty, value):
        """Change a graphics property of the items given by the list indices.
           Specify graphics element, property to be changed and the new value.
           The new value is set and 'dataChanged()' and 'layoutChanged()'
           signals are emitted in order to update a view.
        """
        for index in indices:
            if index.isValid():
                item = index.internalPointer()
                item.setGxElementProperty(element, eproperty, value)
            else:
                indices.remove(index)
        if len(indices) > 0:
            self.lastChange = "GXPROPERTY_CHANGE"
            self.dataChanged.emit(indices[0], indices[-1])
            self.layoutChanged.emit()

    def setTimeMarker(self, index, interval, emit_change=True):
        """Set the time marker interval property of the item given by the
           index. If the given time interval is smaller than the interval
           between the individual data points of the item, the item will
           automatically set the time interval to this minimum value.
           This method returns the value that has actually been set.
        """
        if index.isValid():
            item = index.internalPointer()
            item.setGxElementProperty("general", "timeMarkerInterval",
                                      interval)
            if emit_change:
                self.lastChange = "MARKER_CHANGE"
                self.dataChanged.emit(index, index)
                self.layoutChanged.emit()

            return item.getGxElementProperty("general", "timeMarkerInterval")

    def selectionFromQuery(self, query, index=None):
        """Translate a selection query string into a Python statement and
           check for each item in the tree if the query is fulfilled.
           Return a QItemSelection of all items that match the query.

        Arguments:
        query -- string of format '%lat >= 20. and %pres >= 500.'. See
                 LagrantoMapItem.translateQueryString() for exact syntax.

        Keyword arguments:
        index -- if the query should only be applied to children of a specific
                 item pass this item's index in this argument. If index is None
                 (default), the query will be applied to all items in the tree.
        """
        if index is not None and index.isValid():
            itemStack = [index.internalPointer()]
        else:
            itemStack = [self.rootItem]

        # Translate the query string into a Python statement that can
        # be evaluated by eval().
        queryTranslation = self.rootItem.translateQueryString(query)

        # Create an instance of a QItemSelection that can store a list of
        # all items that match the query.
        #
        # FROM THE PYQT DOCUMENTATION:
        # A QItemSelection is basically a list of selection ranges, see
        # QItemSelectionRange. QItemSelection saves memory, and avoids
        # unnecessary work, by working with selection ranges rather than
        # recording the model item index for each item in the selection.
        # Generally, an instance of this class will contain a list of
        # non-overlapping selection ranges.
        itemSelection = QtGui.QItemSelection()

        # Traverse the tree:
        # Operate on the items in the stack until the stack is empty.
        while len(itemStack) > 0:
            #
            # Get a new item from the stack.
            item = itemStack.pop()
            #
            # Push all children of the current item onto the stack that are
            # instances of LagrantoMapItem (VariableItems are not plotted on
            # the map and cannot be selected).
            itemStack.extend([child for child in item.childItems
                              if isinstance(child, LagrantoMapItem)])
            #
            # Only flight tracks and trajectories can be queried and selected.
            # Check if the item matches the query.
            if isinstance(item, (FlightTrackItem, TrajectoryItem)) and item.query(queryTranslation):
                # The properties of the current item fulfil the query and
                # the item should be selected. Hence create an index.
                index = self.createIndex(item.row(), 0, item)
                #
                # QtGui.QItemSelectionRange.__init__ (self,
                #     QModelIndex index)
                itemSelectionRange = QtGui.QItemSelectionRange(index)
                itemSelection.append(itemSelectionRange)

        return itemSelection
