"""Table view of the MSUI.

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

This file is part of the Mission Support System User Interface (MSUI).

See the reference documentation, Supplement, for details on the
implementation.

To better understand of the code, look at the 'ships' example from
chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
Definitive Guide to PyQt Programming' (Mark Summerfield).

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
from datetime import datetime
import string
import random
import logging
import functools

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings

# local application imports
import ui_tableview_window as ui
import performance_control as perf
import performance_control_clientside as perf_cs
import flighttrack as ft
import mss_qt
import mss_settings

PERFORMANCE = 0
PERFORMANCE_OLD = 1


################################################################################
###                 USER INTERFACE CLASS FlightPlanTableView                 ###
################################################################################

class MSSTableViewWindow(mss_qt.MSSViewWindow, ui.Ui_TableViewWindow):
    """Implements the table view of the flight plan. Data comes from a
       flight track data model.
    """

    name = "Table View"

    def __init__(self, parent=None, model=None):
        """
        """
        super(MSSTableViewWindow, self).__init__(parent)
        self.setupUi(self)
        self.setFlightTrackModel(model)
        self.tableWayPoints.setItemDelegate(ft.WaypointDelegate(self))

        self.lblRemainingRange.setVisible(False)

        # Dock windows [Performance, Performance_Old].
        self.docks = [None, None]

        # Connect slots and signals.
        self.connect(self.btAddWayPointToFlightTrack, QtCore.SIGNAL("clicked()"),
                     self.addWayPoint)
        self.connect(self.btDeleteWayPoint, QtCore.SIGNAL("clicked()"),
                     self.removeWayPoint)
        self.connect(self.btInvertDirection, QtCore.SIGNAL("clicked()"),
                     self.invertDirection)

        self.connect(self.actionFlightPerformance,
                     QtCore.SIGNAL("triggered()"),
                     functools.partial(self.openTool, PERFORMANCE + 1))
        self.connect(self.actionFlightPerformance_old,
                     QtCore.SIGNAL("triggered()"),
                     functools.partial(self.openTool, PERFORMANCE_OLD + 1))

        self.connect(self.btViewPerformance, QtCore.SIGNAL("clicked()"),
                     self.viewPerformance)

        self.resizeColumns()

    def openTool(self, index):
        """Slot that handles requests to open tool windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == PERFORMANCE:
                # Open a flight performance control widget.
                title = "Flight Performance Control"
                widget = perf_cs.PerformanceControlWidget(default_FPS=mss_settings.default_VSEC_WMS,
                                                          model=self.waypoints_model)
            elif index == PERFORMANCE_OLD:
                # Open a flight performance control widget.
                title = "Flight Performance Service Control"
                widget = perf.PerformanceControlWidget(default_FPS=mss_settings.default_FPS,
                                                       model=self.waypoints_model)
            else:
                raise IndexError("invalid control index (%i)" % index)
            # Create the actual dock widget containing <widget>.
            logging.debug("opening %s" % title)
            self.createDockWidget(index, title, widget)

    def invertDirection(self):
        self.waypoints_model.invertDirection()
        self.setFlightTrackModel(self.waypoints_model)
        QtGui.QMessageBox.warning(None, "Invert waypoints",
                                  "Please redraw the map manually, if another view is open!",
                                  QtGui.QMessageBox.Ok)

    def addWayPoint(self):
        """Handler for button <btAddWayPointToFlightTrack>. Adds a new waypoint
           behind the currently selected waypoint.
        """
        tableView = self.tableWayPoints
        index = tableView.currentIndex()
        if not index.isValid():
            row = 0
            fl = 0
        else:
            row = index.row() + 1
            fl = self.waypoints_model.waypointData(row - 1).flightlevel
        # row = self.waypoints_model.rowCount() # Append to end
        locations = [str(wp.location) for wp in self.waypoints_model.allWaypointData()]
        locname = ""
        for letter in string.ascii_uppercase:
            if letter not in locations:
                locname = letter
                break
        if locname == "":
            for fletter in string.ascii_uppercase:
                for sletter in string.ascii_uppercase:
                    if fletter + sletter not in locations:
                        locname = fletter + sletter
                        break
                if locname != "":
                    break
        if locname == "":
            i = 3
            j = 0
            locname = random.sample(string.ascii_uppercase, i)
            while locname in locations:
                locname = random.sample(string.ascii_uppercase, i)
                j += 1
                if j == 10:
                    i += 1
        self.waypoints_model.insertRows(row, waypoints=[ft.Waypoint(lat=0, lon=0, flightlevel=fl, location=locname)])

        index = self.waypoints_model.index(row, 0)
        tableView = self.tableWayPoints
        tableView.setFocus()
        tableView.setCurrentIndex(index)
        # tableView.edit(index)
        tableView.resizeRowsToContents()

    def confirm_delete_waypoint(self, row):
        """Open a QMessageBox and ask the user if he really wants to
           delete the waypoint at index <row>.

        Returns TRUE if the user confirms the deletion.

        If the flight track consists of only two points deleting a waypoint
        is not possible. In this case the user is informed correspondingly.
        """
        wps = self.waypoints_model.allWaypointData(mode=ft.USER)
        if len(wps) < 3:
            QtGui.QMessageBox.warning(None, "Remove waypoint",
                                      "Cannot remove waypoint, the flight track needs to consist " \
                                      "of at least two points.", QtGui.QMessageBox.Ok)
            return False
        else:
            wp = wps[row]
            return (QtGui.QMessageBox.question(None, "Remove waypoint",
                                               "Remove waypoint at %.2f/%.2f, flightlevel %.2f?" \
                                               % (wp.lat, wp.lon, wp.flightlevel),
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes)

    def removeWayPoint(self):
        """Handler for button <btDeleteWayPoint>. Deletes the currently selected
           waypoint.
        """
        tableView = self.tableWayPoints
        index = tableView.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        # Let the user confirm the deletion.
        if self.confirm_delete_waypoint(row):
            self.waypoints_model.removeRows(row)

    def resizeColumns(self):
        for column in range(self.waypoints_model.columnCount()):
            self.tableWayPoints.resizeColumnToContents(column)

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance that the table displays.
        """
        super(MSSTableViewWindow, self).setFlightTrackModel(model)
        self.tableWayPoints.setModel(self.waypoints_model)
        self.connect(self.waypoints_model, QtCore.SIGNAL("performanceUpdated()"),
                     self.viewPerformance)
        self.connect(self.waypoints_model, QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                     self.viewPerformance)
        # Set the performance mode of the flight track.
        self.viewPerformance()

    def viewPerformance(self):
        """Slot to toggle the view mode of the table between 'USER' and
           'PERFORMANCE'.
        """
        if self.btViewPerformance.isChecked():
            self.waypoints_model.setMode(ft.PERFORMANCE)
            # Change the button face colour to "red".
            palette = QtGui.QPalette(self.btViewPerformance.palette())
            colour = QtGui.QColor(255, 0, 0)
            palette.setColor(QtGui.QPalette.Button, colour)
            self.btViewPerformance.setPalette(palette)
            # Set the entire table background to red if the performance
            # computations aren't valid anymore (i.e. after a change).
            if not self.waypoints_model.performanceValid():
                palette = QtGui.QPalette(self.tableWayPoints.palette())
                colour = QtGui.QColor(255, 60, 60)
                palette.setColor(QtGui.QPalette.Base, colour)
                colour = QtGui.QColor(255, 80, 80)
                palette.setColor(QtGui.QPalette.AlternateBase, colour)
                self.tableWayPoints.setPalette(palette)
            else:
                self.tableWayPoints.setPalette(self.palette())
            # Disable insert/delete buttons.
            self.btAddWayPointToFlightTrack.setEnabled(False)
            self.btDeleteWayPoint.setEnabled(False)
            # Show label that displays remaining range information.
            self.lblRemainingRange.setText(self.waypoints_model.remainingRangeInfo())
            self.lblRemainingRange.setVisible(True)
        else:
            self.waypoints_model.setMode(ft.USER)
            # Restore the original button face colour (as inherited from this
            # window's palette).
            self.btViewPerformance.setPalette(self.palette())
            self.tableWayPoints.setPalette(self.palette())
            self.btAddWayPointToFlightTrack.setEnabled(True)
            self.btDeleteWayPoint.setEnabled(True)
            self.lblRemainingRange.setVisible(False)

        self.resizeColumns()


################################################################################

if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    import sys

    # Create an initital flight track.
    initial_waypoints = [ft.Waypoint(flightlevel=0, location="EDMO", comments="take off OP"),
                         ft.Waypoint(48.10, 10.27, 200),
                         ft.Waypoint(52.32, 09.21, 200),
                         ft.Waypoint(52.55, 09.99, 200),
                         ft.Waypoint(flightlevel=0, location="Hamburg", comments="landing HH")]

    waypoints_model = ft.WaypointsTableModel(QtCore.QString(""))
    waypoints_model.insertRows(0, rows=len(initial_waypoints),
                               waypoints=initial_waypoints)

    app = QtGui.QApplication(sys.argv)
    win = MSSTableViewWindow(model=waypoints_model)
    win.show()

    # waypoints_model.setPerformanceComputation(testperformance)

    sys.exit(app.exec_())
