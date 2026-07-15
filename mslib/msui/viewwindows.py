# -*- coding: utf-8 -*-
"""

    mslib.msui.viewindows
    ~~~~~~~~~~~~~~~~~~~~~

    Common PyQt-derived classes and methods required by all msui ui
    modules.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

from abc import abstractmethod

from PyQt5 import QtCore, QtWidgets
from mslib.msui import constants
from mslib.utils.config import load_settings_qsettings, save_settings_qsettings


class MSUIViewWindow(QtWidgets.QMainWindow):
    """
    Derives QMainWindow to provide some common functionality to all
    MSUI view windows.
    """
    name = "Abstract MSS View Window"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    # views for mscolab
    # viewClosesId = QtCore.pyqtSignal(int, name="viewClosesId")

    def __init__(self, parent=None, model=None, _id=None):
        super().__init__(parent)

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
            for dock in self.docks:
                if dock is not None:
                    widget = dock.widget()
                    if widget is not None and hasattr(widget, "cleanup_threads"):
                        widget.cleanup_threads()
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

        if getattr(self, "tutorial_mode", False):
            self._track_tutorial_flighttrack(model)

    def enable_tutorial_flighttrack_save(self):
        """
        Start mirroring the displayed flight track to the tutorial FTML.

        Views receive their model through the constructor, which bypasses
        setFlightTrackModel (where the mirroring is normally wired). The view
        creator calls this once after construction, in tutorial mode, so the
        initial track is written and later edits are tracked.
        """
        self._track_tutorial_flighttrack(self.waypoints_model)

    def _track_tutorial_flighttrack(self, model):
        """
        In tutorial mode, keep a silent FTML copy of the displayed flight track
        current, so coordinate-based tutorials can resolve waypoint names and
        entry order before a delete/move.

        Connects to the model's change signals so edits made in *any* view (the
        model object is shared across Top/Side/Table/Linear views) and
        collaborative mscolab updates -- which also arrive through
        setFlightTrackModel -- trigger a rewrite. The previously tracked model
        is disconnected when the displayed model is swapped.
        """
        signals = ("dataChanged", "rowsInserted", "rowsRemoved", "layoutChanged", "modelReset")
        previous = getattr(self, "_tutorial_ft_model", None)
        if previous is not None and previous is not model:
            for sig in signals:
                try:
                    getattr(previous, sig).disconnect(self._save_tutorial_flighttrack)
                except (TypeError, RuntimeError):
                    pass
        if model is not None and model is not previous:
            for sig in signals:
                getattr(model, sig).connect(self._save_tutorial_flighttrack)
        self._tutorial_ft_model = model
        self._save_tutorial_flighttrack()

    def _save_tutorial_flighttrack(self, *args):
        """
        Write the current flight track to a fixed FTML path for the tutorials.

        Uses get_xml_content() rather than save_to_ftml() so the model's own
        name/filename are not overwritten.
        """
        model = self.waypoints_model
        if model is None:
            return
        path = os.path.join(constants.MSUI_CONFIG_PATH, "tutorial_flighttrack.ftml")
        try:
            with open(path, "w") as file_object:
                file_object.write(model.get_xml_content())
        except OSError as ex:
            logging.warning("Could not write tutorial flight track (%s: %s)", type(ex), ex)

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
        if self.name in ("Top View", "Table View"):
            # Make Roundtrip Button
            self.btRoundtrip.setEnabled(self.is_roundtrip_possible())
        if self.name in ("Top View", "Side View", "Linear View"):
            actions = self.mpl.navbar.actions()
            for action in actions:
                action_text = action.text()
                if action_text in ("Ins WP", "Del WP", "Mv WP"):
                    action.setEnabled(True)
        else:
            # Table View
            self.btAddWayPointToFlightTrack.setEnabled(True)
            self.btCloneWaypoint.setEnabled(True)
            self.btDeleteWayPoint.setEnabled(True)
            self.btInvertDirection.setEnabled(True)
            self.cbTools.setEnabled(True)
            self.tableWayPoints.setEnabled(True)

    def disable_navbar_action_buttons(self):
        """
        function disables some control, used if access_level is not appropriate
        """
        if self.name in ("Top View", "Table View"):
            # Make Roundtrip Button
            self.btRoundtrip.setEnabled(False)
        if self.name in ("Top View", "Side View", "Linear View"):
            actions = self.mpl.navbar.actions()
            for action in actions:
                action_text = action.text()
                if action_text in ("Ins WP", "Del WP", "Mv WP"):
                    action.setEnabled(False)
                    if str(self.mpl.navbar.mode) == "insert waypoint" and action_text == "Ins WP":
                        action.trigger()
                    elif str(self.mpl.navbar.mode) == "delete waypoint" and action_text == "Del WP":
                        action.trigger()
                    elif str(self.mpl.navbar.mode) == "move waypoint" and action_text == "Mv WP":
                        action.trigger()
        else:
            # Table View
            self.btAddWayPointToFlightTrack.setEnabled(False)
            self.btCloneWaypoint.setEnabled(False)
            self.btDeleteWayPoint.setEnabled(False)
            self.btInvertDirection.setEnabled(False)
            self.cbTools.setEnabled(False)
            self.tableWayPoints.setEnabled(False)

    def _tutorial_screen_settings(self):
        """
        Build the on-screen geometry persisted for the tutorials.

        Records the view window rectangle and, for Matplotlib views, the figure
        canvas rectangle -- both in Qt logical points (mapToGlobal / width /
        height). The canvas rectangle lets coordinate-based tutorials map plot
        pixels to screen points deterministically and independent of the display
        scale (Retina/HiDPI).

        :return: dict with ``os_screen_region`` and, when a canvas is present,
          ``canvas_screen_region``, each an (x, y, width, height) tuple.
        """
        top_left = self.mapToGlobal(QtCore.QPoint(0, 0))
        settings = {'os_screen_region': (top_left.x(), top_left.y(), self.width(), self.height())}
        canvas = getattr(getattr(self, 'mpl', None), 'canvas', None)
        if canvas is not None:
            canvas_top_left = canvas.mapToGlobal(QtCore.QPoint(0, 0))
            settings['canvas_screen_region'] = (canvas_top_left.x(), canvas_top_left.y(),
                                                canvas.width(), canvas.height())
        return settings

    def _save_tutorial_screen_settings(self):
        """
        Save the on-screen geometry, without clobbering other
        settings already stored under ``self.settings_tag`` (e.g. the map's
        current extent, saved separately by NavigationToolbar.push_current on
        pan/zoom) -- save_settings_qsettings replaces the whole per-tag dict,
        so it has to be merged with what is already there.
        """
        settings = load_settings_qsettings(self.settings_tag, {})
        settings.update(self._tutorial_screen_settings())
        save_settings_qsettings(self.settings_tag, settings)

    def changeEvent(self, event):
        """
        Change event method

        This method is called when a change event is triggered for the linearview, tableview, topview, sideview widget.
        It is an overridden method of the QWidget class.

        Parameters:
        :event: The QEvent object representing the change event.
        """
        if self.tutorial_mode:
            top_left = self.mapToGlobal(QtCore.QPoint(0, 0))
            if top_left.x() != 0:
                # we have to save this to reuse it by the tutorials
                self._save_tutorial_screen_settings()
            QtWidgets.QWidget.changeEvent(self, event)

    def moveEvent(self, event):
        """
        Move event method

        This method is called when a move event is triggered for the linearview, tableview, topview, sideview widget.
        It is an overridden method of the QWidget class.

        Parameters:
        :event: The QEvent object representing the move event.
        """
        if self.tutorial_mode:
            top_left = self.mapToGlobal(QtCore.QPoint(0, 0))
            if top_left.x() != 0:
                # we have to save this to reuse it by the tutorials
                self._save_tutorial_screen_settings()
            QtWidgets.QWidget.moveEvent(self, event)


class MSUIMplViewWindow(MSUIViewWindow):
    """
    Adds Matplotlib-specific functionality to MSUIViewWindow.
    """

    def __init__(self, parent=None, model=None, _id=None):
        super().__init__(parent, model, _id)
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
                self.mpl.canvas.map.ax.figure.suptitle(f"{model.name}", x=0.95, ha='right')
                self.mpl.canvas.map.ax.figure.canvas.draw()

            elif hasattr(self.mpl.canvas, 'plotter'):
                self.mpl.canvas.plotter.fig.suptitle(f"{model.name}", x=0.95, ha='right')
                self.mpl.canvas.plotter.fig.canvas.draw()

    def getView(self):
        """
        Return the MplCanvas instance of the window.
        """
        return self.mpl.canvas
