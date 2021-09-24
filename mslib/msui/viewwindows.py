# -*- coding: utf-8 -*-
"""

    mslib.msui.viewindows
    ~~~~~~~~~~~~~~~~~~~~~

    Common PyQt-derived classes and methods required by all mss ui
    modules.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

from abc import abstractmethod

from PyQt5 import QtCore, QtWidgets
import logging


class MSSViewWindow(QtWidgets.QMainWindow):
    """
    Derives QMainWindow to provide some common functionality to all
    MSUI view windows.
    """
    name = "Abstract MSS View Window"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    # views for mscolab
    # viewClosesId = QtCore.Signal(int, name="viewClosesId")

    def __init__(self, parent=None, model=None, _id=None):
        super(MSSViewWindow, self).__init__(parent)

        # Object variables:
        self.waypoints_model = model  # pointer to the current flight track.

        # List that accommodates the dock window instances: Needs to be defined
        # in proper size in derived classes!
        self.docks = []

        # # emit _id if not none
        # logging.debug(_id)
        # self._id = _id
        # Used to force close window without the dialog popping up
        self.force_close = False
        # Flag variable to check whether tableview window exists or not.
        self.tv_window_exists = True

    def handle_force_close(self):
        self.force_close = True
        self.close()

    def closeEvent(self, event):
        """
        If force_close is True then close window without dialog
        else ask user if he/she wants to close the window.

        Overloads QtGui.QMainWindow.closeEvent(). This method is called if
        Qt receives a window close request for our application window.
        """
        if self.force_close:
            ret = QtWidgets.QMessageBox.Yes
        else:
            ret = QtWidgets.QMessageBox.warning(self, self.tr("Mission Support System"),
                                                self.tr(f"Do you want to close this {self.name}?"),
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)

        if ret == QtWidgets.QMessageBox.Yes:
            # if self._id is not None:
            #     self.viewClosesId.emit(self._id)
            #     logging.debug(self._id)
            # sets flag as False which shows tableview window had been closed.
            self.tv_window_exists = False
            self.viewCloses.emit()
            event.accept()
        else:
            event.ignore()

    def exists(self):
        """
        Returns the flag False if self.closeEvent() is triggered else returns True.
        This is only for helping as a flag information in
        force closing of tableview when main window closes.
        """
        return self.tv_window_exists

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the view displays.
        """
        # Update title flighttrack name
        if self.waypoints_model:
            self.setWindowTitle(self.windowTitle().replace(self.waypoints_model.name, model.name))

        self.waypoints_model = model

    def controlToBeCreated(self, index):
        """
        Check if the dock widget at index <index> exists. If yes, show
        the widget and return -1. Otherwise return <index-1>.
        """
        index -= 1
        if index >= 0 and self.docks[index] is not None:
            # The widget has already been created, but is not visible at
            # the moment.
            self.docks[index].show()
            self.docks[index].raise_()
            index = -1
        if hasattr(self, "cbTools"):
            self.cbTools.setCurrentIndex(0)
        return index

    def createDockWidget(self, index, title, widget):
        """
        Create a new dock widget. A pointer to the dock widget will be
        stored in self.docks[index]. The dock will have the title <title>
        and contain the Qt widget <widget>.
        """
        self.docks[index] = QtWidgets.QDockWidget(title, self)
        self.docks[index].setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        # setWidget transfers the widget's ownership to Qt -- no setParent()
        # call is necessary:
        self.docks[index].setWidget(widget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.docks[index])

        # Check if another dock widget occupies the dock area. If yes,
        # tabbify the old and the new widget.
        for dock in self.docks:
            if dock and not dock == self.docks[index] and not dock.isFloating():
                self.tabifyDockWidget(dock, self.docks[index])
                break
        self.docks[index].show()
        self.docks[index].raise_()

    @abstractmethod
    def getView(self):
        """
        Return view object that tools can interact with.

        ABSTRACT method, needs to be implemented in derived classes.
        """
        return None

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def enable_navbar_action_buttons(self):
        """
        function enables some control, used if access_level is appropriate
        """
        if self.name in ("Top View", "Side View", "Linear View"):
            actions = self.mpl.navbar.actions()
            for action in actions:
                action_text = action.text()
                if action_text == "Ins WP" or action_text == "Del WP" or action_text == "Mv WP":
                    action.setEnabled(True)
        else:
            # Table View
            self.btAddWayPointToFlightTrack.setEnabled(True)
            self.btCloneWaypoint.setEnabled(True)
            self.btDeleteWayPoint.setEnabled(True)
            self.btInvertDirection.setEnabled(True)
            self.btRoundtrip.setEnabled(True)
            self.cbTools.setEnabled(True)
            self.tableWayPoints.setEnabled(True)

    def disable_navbar_action_buttons(self):
        """
        function disables some control, used if access_level is not appropriate
        """
        if self.name in ("Top View", "Side View", "Linear View"):
            actions = self.mpl.navbar.actions()
            for action in actions:
                action_text = action.text()
                if action_text == "Ins WP" or action_text == "Del WP" or action_text == "Mv WP":
                    action.setEnabled(False)
        else:
            # Table View
            self.btAddWayPointToFlightTrack.setEnabled(False)
            self.btCloneWaypoint.setEnabled(False)
            self.btDeleteWayPoint.setEnabled(False)
            self.btInvertDirection.setEnabled(False)
            self.btRoundtrip.setEnabled(False)
            self.cbTools.setEnabled(False)
            self.tableWayPoints.setEnabled(False)


class MSSMplViewWindow(MSSViewWindow):
    """
    Adds Matplotlib-specific functionality to MSSViewWindow.
    """

    def __init__(self, parent=None, model=None, _id=None):
        super(MSSMplViewWindow, self).__init__(parent, model, _id)
        logging.debug(_id)
        self.mpl = None

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the view displays.
        """
        super().setFlightTrackModel(model)

        if self.mpl is not None:
            self.mpl.canvas.set_waypoints_model(model)

            # Update Top View flighttrack name
            if hasattr(self.mpl.canvas, "map"):
                text = self.mpl.canvas.map.crs_text.get_text()
                old_name = self.mpl.canvas.map.operation_name
                self.mpl.canvas.map.operation_name = model.name
                self.mpl.canvas.map.crs_text.set_text(text.replace(old_name, model.name))
                self.mpl.canvas.map.ax.figure.canvas.draw()

    def getView(self):
        """
        Return the MplCanvas instance of the window.
        """
        return self.mpl.canvas
