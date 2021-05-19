#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    mslib.msui.mss_pyui
    ~~~~~~~~~~~~~~~~~~~

    Mission Support System Python/Qt User Interface
    Main window of the user interface application. Manages view and tool windows
    (the user can open multiple windows) and provides functionality to open, save,
    and switch between flight tracks.

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

import argparse
import copy
import functools
import hashlib
import importlib
import logging
import os
import platform
import re
import requests
import shutil
import sys
import types
import fs

from mslib import __version__
from mslib.msui.mss_qt import ui_mainwindow as ui
from mslib.msui.mss_qt import ui_about_dialog as ui_ab
from mslib.msui import flighttrack as ft
from mslib.msui import tableview
from mslib.msui import topview
from mslib.msui import sideview
from mslib.msui import editor
from mslib.msui import constants
from mslib.msui import wms_control
from mslib.msui import mscolab
from mslib.utils import config_loader, setup_logging
from mslib.plugins.io.csv import load_from_csv, save_to_csv
from mslib.msui.icons import icons, python_powered
from mslib.msui.mss_qt import get_open_filename, get_save_filename
from PyQt5 import QtGui, QtCore, QtWidgets

# Add config path to PYTHONPATH so plugins located there may be found
sys.path.append(constants.MSS_CONFIG_PATH)


def clean_string(string):
    return re.sub(r'\W|^(?=\d)', '_', string)


class QActiveViewsListWidgetItem(QtWidgets.QListWidgetItem):
    """Subclass of QListWidgetItem, represents an open view in the list of
       open views. Keeps a reference to the view instance (i.e. the window) it
       represents in the list of open views.
    """

    # Class variable to assign a unique ID to each view.
    opened_views = 0

    def __init__(self, view_window, parent=None, viewsChanged=None,
                 type=QtWidgets.QListWidgetItem.UserType):
        """Add ID number to the title of the corresponding view window.
        """
        QActiveViewsListWidgetItem.opened_views += 1
        view_name = f"({QActiveViewsListWidgetItem.opened_views:d}) {view_window.name}"
        super(QActiveViewsListWidgetItem, self).__init__(view_name, parent, type)

        view_window.setWindowTitle(f"({QActiveViewsListWidgetItem.opened_views:d}) {view_window.windowTitle()}")
        view_window.setIdentifier(view_name)
        self.window = view_window
        self.parent = parent
        self.viewsChanged = viewsChanged

    def view_destroyed(self):
        """Slot that removes this QListWidgetItem from the parent (the
           QListWidget) if the corresponding view has been deleted.
        """
        if self.parent is not None:
            self.parent.takeItem(self.parent.row(self))
        if self.viewsChanged is not None:
            self.viewsChanged.emit()


class QFlightTrackListWidgetItem(QtWidgets.QListWidgetItem):
    """Subclass of QListWidgetItem, represents a flight track in the list of
       open flight tracks. Keeps a reference to the flight track instance
       (i.e. the instance of WaypointsTableModel).
    """

    def __init__(self, flighttrack_model, parent=None,
                 type=QtWidgets.QListWidgetItem.UserType):
        """Item class for the list widget that accommodates the open flight
           tracks.

        Arguments:
        flighttrack_model -- instance of a flight track model that is
                             associated with the item
        parent -- pointer to the QListWidgetItem that accommodates this item.
                  If not None, the itemChanged() signal of the parent is
                  connected to the nameChanged() slot of this class, reacting
                  to name changes of the item.
        """
        view_name = flighttrack_model.name
        super(QFlightTrackListWidgetItem, self).__init__(
            view_name, parent, type)

        self.parent = parent
        self.flighttrack_model = flighttrack_model


class MSS_AboutDialog(QtWidgets.QDialog, ui_ab.Ui_AboutMSUIDialog):
    """Dialog showing information about MSUI. Most of the displayed text is
       defined in the QtDesigner file.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSS_AboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.lblVersion.setText("Version: {}".format(__version__))
        self.milestone_url = f'https://github.com/Open-MSS/MSS/issues?q=is%3Aclosed+milestone%3A{__version__[:-1]}'
        self.lblChanges.setText(f'<a href="{self.milestone_url}">New Features and Changes</a>')
        blub = QtGui.QPixmap(python_powered())
        self.lblPython.setPixmap(blub)


class MSSMainWindow(QtWidgets.QMainWindow, ui.Ui_MSSMainWindow):
    """MSUI main window class. Provides user interface elements for managing
       flight tracks and views.
    """

    viewsChanged = QtCore.pyqtSignal(name="viewsChanged")

    def __init__(self, *args):
        super(MSSMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('32x32')))
        # This code is required in Windows 7 to use the icon set by setWindowIcon in taskbar
        # instead of the default Icon of python/pythonw
        try:
            import ctypes
            myappid = f"mss.mss_pyui.{__version__}"  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except (ImportError, AttributeError) as error:
            logging.debug("AttributeError, ImportError Exception %s", error)
        # Reference to the flight track that is currently displayed in the
        # views.
        self.active_flight_track = None
        self.last_save_directory = config_loader(dataset="data_dir")
        self.mscolab_window = None
        self.config_editor = None

        # Connect Qt SIGNALs:
        # ===================

        # File menu.
        self.actionNewFlightTrack.triggered.connect(functools.partial(self.create_new_flight_track, None, None))
        self.actionOpenFlightTrack.triggered.connect(self.open_flight_track)
        self.actionActivateSelectedFlightTrack.triggered.connect(self.activate_selected_flight_track)
        self.actionCloseSelectedFlightTrack.triggered.connect(self.close_selected_flight_track)
        self.actionSaveActiveFlightTrack.triggered.connect(self.save_flight_track)
        self.actionSaveActiveFlightTrackAs.triggered.connect(self.save_flight_track_as)

        # Views menu.
        self.actionTopView.triggered.connect(self.create_new_view)
        self.actionSideView.triggered.connect(self.create_new_view)
        self.actionTableView.triggered.connect(self.create_new_view)

        # mscolab menu
        self.actionMscolabProjects.triggered.connect(self.activate_mscolab_window)

        # Help menu.
        self.actionOnlineHelp.triggered.connect(self.show_online_help)
        self.actionAboutMSUI.triggered.connect(self.show_about_dialog)

        # Config
        self.actionLoadConfigurationFile.triggered.connect(self.load_config_file)
        self.actionConfigurationEditor.triggered.connect(self.open_config_editor)

        # Flight Tracks.
        self.listFlightTracks.itemActivated.connect(self.activate_flight_track)

        # Views.
        self.listViews.itemActivated.connect(self.activate_sub_window)

        self.add_import_filter("CSV", "csv", load_from_csv, pickertag="filepicker_default")
        self.add_export_filter("CSV", "csv", save_to_csv, pickertag="filepicker_default")

        self._imported_plugins, self._exported_plugins = {}, {}
        self.add_plugins()

        preload_urls = config_loader(dataset="WMS_preload")
        self.preload_wms(preload_urls)

        # Status Bar
        self.labelStatusbar.setText(self.status())

    @staticmethod
    def preload_wms(urls):
        """
        This method accesses a list of WMS servers and load their capability documents.
        :param urls: List of URLs
        """
        pdlg = QtWidgets.QProgressDialog("Preloading WMS servers...", "Cancel", 0, len(urls))
        pdlg.reset()
        pdlg.setValue(0)
        pdlg.setModal(True)
        pdlg.show()
        QtWidgets.QApplication.processEvents()
        for i, base_url in enumerate(urls):
            pdlg.setValue(i)
            QtWidgets.QApplication.processEvents()
            # initialize login cache from config file, but do not overwrite existing keys
            for key, value in config_loader(dataset="WMS_login").items():
                if key not in constants.WMS_LOGIN_CACHE:
                    constants.WMS_LOGIN_CACHE[key] = value
            username, password = constants.WMS_LOGIN_CACHE.get(base_url, (None, None))

            try:
                request = requests.get(base_url)
                if pdlg.wasCanceled():
                    break

                wms = wms_control.MSSWebMapService(request.url, version=None,
                                                   username=username, password=password)
                wms_control.WMS_SERVICE_CACHE[wms.url] = wms
                logging.info("Stored WMS info for '%s'", wms.url)
            except Exception as ex:
                logging.error("Error in preloading '%s': '%s'", type(ex), ex)
            if pdlg.wasCanceled():
                break
        logging.debug("Contents of WMS_SERVICE_CACHE: %s", wms_control.WMS_SERVICE_CACHE.keys())
        pdlg.close()

    def add_plugins(self):
        picker_default = config_loader(
            dataset="filepicker_default")

        self._imported_plugins = config_loader(dataset="import_plugins")
        for name in self._imported_plugins:
            extension, module, function = self._imported_plugins[name][:3]
            picker_type = picker_default
            if len(self._imported_plugins[name]) == 4:
                picker_type = self._imported_plugins[name][3]
            try:
                imported_module = importlib.import_module(module)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on import: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self._imported_plugins}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            try:
                self.add_import_filter(name, extension, getattr(imported_module, function), pickertype=picker_type)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on installing plugin: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self._imported_plugins}\n\nthrows {type(ex)} error:\n{ex}"))

                continue

        self._exported_plugins = config_loader(dataset="export_plugins")
        for name in self._exported_plugins:
            extension, module, function = self._exported_plugins[name][:3]
            picker_type = picker_default
            if len(self._exported_plugins[name]) == 4:
                picker_type = self._exported_plugins[name][3]
            try:
                imported_module = importlib.import_module(module)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on import: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self._exported_plugins,}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            try:
                self.add_export_filter(name, extension, getattr(imported_module, function), pickertype=picker_type)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on installing plugin: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error"),
                    self.tr(f"ERROR: Configuration for export {self._exported_plugins} plugins\n\n{type(ex)}\n"
                            f"\nthrows error:\n{ex}"))
                continue

    def remove_plugins(self):
        for name in self._imported_plugins:
            full_name = "actionImportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuImport_Flight_Track.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuImport_Flight_Track.removeAction(actions[0])
            delattr(self, full_name)

        for name in self._exported_plugins:
            full_name = "actionExportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuExport_Active_Flight_Track.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuExport_Active_Flight_Track.removeAction(actions[0])
            delattr(self, full_name)

    def add_import_filter(self, name, extension, function, pickertag=None, pickertype=None):
        full_name = "actionImportFlightTrack" + clean_string(name)
        if hasattr(self, full_name):
            raise ValueError(f"'{full_name}' has already been set!")

        action = QtWidgets.QAction(self)
        action.setObjectName(full_name)
        action.setText(QtCore.QCoreApplication.translate("MSSMainWindow", name, None))
        self.menuImport_Flight_Track.addAction(action)

        def load_function_wrapper(self):
            filename = get_open_filename(
                self, "Import Flight Track", self.last_save_directory,
                "All Files (*." + extension + ")", pickertype=pickertype)
            if filename is not None:
                self.last_save_directory = fs.path.dirname(filename)
                try:
                    ft_name, new_waypoints = function(filename)
                # wildcard exception to be resilient against error introduced by user code
                except Exception as ex:
                    logging.error("file io plugin error: %s %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("file io plugin error"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
                else:
                    if not ft_name:
                        ft_name = filename
                    waypoints_model = ft.WaypointsTableModel(name=ft_name, waypoints=new_waypoints)

                    listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
                    listitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                    self.listFlightTracks.setCurrentItem(listitem)
                    self.activate_flight_track(listitem)

        setattr(self, full_name, types.MethodType(load_function_wrapper, self))
        action.triggered.connect(getattr(self, full_name))

    def add_export_filter(self, name, extension, function, pickertag=None, pickertype=None):
        full_name = "actionExportFlightTrack" + clean_string(name)
        if hasattr(self, full_name):
            raise ValueError(f"'{full_name}' has already been set!")

        action = QtWidgets.QAction(self)
        action.setObjectName(full_name)
        action.setText(QtCore.QCoreApplication.translate("MSSMainWindow", name, None))
        self.menuExport_Active_Flight_Track.addAction(action)

        def save_function_wrapper(self):
            default_filename = os.path.join(self.last_save_directory, self.active_flight_track.name) + "." + extension
            filename = get_save_filename(
                self, "Export Flight Track", default_filename,
                name + " (*." + extension + ")", pickertype=pickertype)
            if filename is not None:
                self.last_save_directory = fs.path.dirname(filename)
                try:
                    function(filename, self.active_flight_track.name, self.active_flight_track.waypoints)
                # wildcard exception to be resilient against error introduced by user code
                except Exception as ex:
                    logging.error("file io plugin error: %s %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("file io plugin error"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))

        setattr(self, full_name, types.MethodType(save_function_wrapper, self))
        action.triggered.connect(getattr(self, full_name))

    def closeEvent(self, event):
        """Ask user if he/she wants to close the application. If yes, also
           close all views that are open.

        Overloads QtGui.QMainWindow.closeEvent(). This method is called if
        Qt receives a window close request for our application window.
        """
        ret = QtWidgets.QMessageBox.warning(
            self, self.tr("Mission Support System"),
            self.tr("Do you want to close the Mission Support System application?"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if ret == QtWidgets.QMessageBox.Yes:
            # Table View stick around after MainWindow closes - maybe some dangling reference?
            # This removes them for sure!
            while self.listViews.count() > 0:
                self.listViews.item(0).window.handle_force_close()
            self.listViews.clear()
            self.listFlightTracks.clear()
            # cleanup mscolab window
            if self.mscolab_window is not None:
                self.mscolab_window.close()
            if self.config_editor is not None:
                self.config_editor.close()
            event.accept()
        else:
            event.ignore()

    def create_new_view(self):
        """Method called when the user selects a new view to be opened. Creates
           a new instance of the view and adds a QActiveViewsListWidgetItem to
           the list of open views (self.listViews).
        """
        layout = config_loader(dataset="layout")
        view_window = None
        if self.sender() == self.actionTopView:
            # Top view.
            view_window = topview.MSSTopViewWindow(model=self.active_flight_track)
            view_window.mpl.resize(layout['topview'][0], layout['topview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['topview'][0], layout['topview'][1])
        elif self.sender() == self.actionSideView:
            # Side view.
            view_window = sideview.MSSSideViewWindow(model=self.active_flight_track)
            view_window.mpl.resize(layout['sideview'][0], layout['sideview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['sideview'][0], layout['sideview'][1])
        elif self.sender() == self.actionTableView:
            # Table view.
            view_window = tableview.MSSTableViewWindow(model=self.active_flight_track)
            view_window.centralwidget.resize(layout['tableview'][0], layout['tableview'][1])
        if view_window is not None:
            # Make sure view window will be deleted after being closed, not
            # just hidden (cf. Chapter 5 in PyQt4).
            view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            # Open as a non-modal window.
            view_window.show()
            # Add an entry referencing the new view to the list of views.
            listitem = QActiveViewsListWidgetItem(view_window, self.listViews, self.viewsChanged)
            view_window.viewCloses.connect(listitem.view_destroyed)
            self.listViews.setCurrentItem(listitem)
            self.viewsChanged.emit()

    def activate_sub_window(self, item):
        """When the user clicks on one of the open view or tool windows, this
           window is brought to the front. This function implements the slot to
           activate a window if the user selects it in the list of views or
           tools.
        """
        # Restore the activated view and bring it to the front.
        item.window.showNormal()
        item.window.raise_()
        item.window.activateWindow()

    def close_mscolab_window(self):
        self.mscolab_window = None

    def activate_mscolab_window(self):
        # initiate mscolab window
        if self.mscolab_window is None:
            self.mscolab_window = mscolab.MSSMscolabWindow(parent=self)
            self.mscolab_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.mscolab_window.viewCloses.connect(self.close_mscolab_window)
            self.mscolab_window.show()
        else:
            self.mscolab_window.setWindowState(QtCore.Qt.WindowNoState)
            self.mscolab_window.raise_()
            self.mscolab_window.activateWindow()

    new_flight_track_counter = 0

    def create_new_flight_track(self, template=None, filename=None):
        """Creates a new flight track model from a template. Adds a new entry to
           the list of flight tracks. Called when the user selects the 'new/open
           flight track' menu entries.

        Arguments:
        template -- copy the specified template to the new flight track (so that
                    it is not empty).
        filename -- if not None, load the flight track in the specified file.
        """
        if template is None:
            template = []
            waypoints = config_loader(dataset="new_flighttrack_template")
            default_flightlevel = config_loader(dataset="new_flighttrack_flightlevel")
            for wp in waypoints:
                template.append(ft.Waypoint(flightlevel=default_flightlevel, location=wp))
            if len(template) < 2:
                QtWidgets.QMessageBox.critical(
                    self, self.tr("flighttrack template"),
                    self.tr("ERROR:Flighttrack template in configuration is too short. "
                            "Please add at least two valid locations."))

        if filename is not None:
            waypoints_model = ft.WaypointsTableModel(filename=filename)
        else:
            # Create a new flight track from the waypoints template.
            self.new_flight_track_counter += 1
            waypoints_model = ft.WaypointsTableModel(
                name=f"new flight track ({self.new_flight_track_counter:d})")
            # Make a copy of the template. Otherwise all new flight tracks would
            # use the same data structure in memory.
            template_copy = copy.deepcopy(template)
            waypoints_model.insertRows(0, rows=len(template_copy), waypoints=template_copy)
        # Create a new list entry for the flight track. Make the item name
        # editable.
        listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
        listitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        self.activate_flight_track(listitem)

    def restart_application(self):
        while self.listViews.count() > 0:
            self.listViews.item(0).window.handle_force_close()
        self.listViews.clear()
        self.remove_plugins()
        self.add_plugins()

    def load_config_file(self):
        """
        Loads a config file and potentially restarts the application
        """
        ret = QtWidgets.QMessageBox.warning(
            self, self.tr("Mission Support System"),
            self.tr("Opening a config file will reset application. Continue?"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if ret == QtWidgets.QMessageBox.Yes:
            filename = get_open_filename(
                self, "Open Config file", constants.MSS_CONFIG_PATH, "Config Files (*.json)")
            if filename is not None:
                constants.CACHED_CONFIG_FILE = filename
                self.restart_application()

    def open_config_editor(self):
        """
        Opens up a JSON config editor
        """
        if self.config_editor is None:
            self.config_editor = editor.EditorMainWindow(parent=self)
            self.config_editor.viewCloses.connect(self.close_config_editor)
            self.config_editor.restartApplication.connect(self.restart_application)
        else:
            self.config_editor.showNormal()
            self.config_editor.activateWindow()

    def close_config_editor(self):
        self.config_editor = None

    def open_flight_track(self):
        """Slot for the 'Open Flight Track' menu entry. Opens a QFileDialog and
           passes the result to createNewFlightTrack().
        """
        filename = get_open_filename(
            self, "Open Flight Track", self.last_save_directory, "Flight Track Files (*.ftml)",
            pickertag="filepicker_default")
        if filename is not None:
            self.last_save_directory = fs.path.dirname(filename)
            try:
                if filename.endswith('.ftml'):
                    self.create_new_flight_track(filename=filename)
                else:
                    QtWidgets.QMessageBox.warning(self, "Open flight track",
                                                  f"No supported file extension recognized!\n{filename:}")

            except (SyntaxError, OSError, IOError) as ex:
                QtWidgets.QMessageBox.critical(
                    self, self.tr("Problem while opening flight track FTML:"),
                    self.tr(f"ERROR: {type(ex)} {ex}"))

    def activate_selected_flight_track(self):
        item = self.listFlightTracks.currentItem()
        self.activate_flight_track(item)

    def close_selected_flight_track(self):
        """Slot to close the currently selected flight track. Flight tracks can
           only be closed if at least one other flight track remains open. The
           currently active flight track cannot be closed.
        """
        if self.listFlightTracks.count() < 2:
            QtWidgets.QMessageBox.information(self, self.tr("Flight Track Management"),
                                              self.tr("At least one flight track has to be open."))
            return
        item = self.listFlightTracks.currentItem()
        if item.flighttrack_model == self.active_flight_track:
            QtWidgets.QMessageBox.information(self, self.tr("Flight Track Management"),
                                              self.tr("Cannot close currently active flight track."))
            return
        if item.flighttrack_model.modified:
            ret = QtWidgets.QMessageBox.warning(self, self.tr("Mission Support System"),
                                                self.tr("The flight track you are about to close has "
                                                        "been modified. Close anyway?"),
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                self.listFlightTracks.takeItem(self.listFlightTracks.currentRow())

    def save_flight_track(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        filename = self.active_flight_track.get_filename()
        if filename and filename.endswith('.ftml'):
            sel = QtWidgets.QMessageBox.question(self, "Save flight track",
                                                 f"Saving flight track to '{filename:s}'. Continue?",
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if sel == QtWidgets.QMessageBox.Yes:
                try:
                    self.active_flight_track.save_to_ftml(filename)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while saving flight track to FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
        else:
            self.save_flight_track_as()

    def save_flight_track_as(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        default_filename = os.path.join(self.last_save_directory, self.active_flight_track.name + ".ftml")
        filename = get_save_filename(
            self, "Save Flight Track", default_filename, "Flight Track (*.ftml)", pickertag="filepicker_default")
        logging.debug("filename : '%s'", filename)
        if filename:
            self.last_save_directory = fs.path.dirname(filename)
            if filename.endswith('.ftml'):
                try:
                    self.active_flight_track.save_to_ftml(filename)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while saving flight track to FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
                for idx in range(self.listFlightTracks.count()):
                    if self.listFlightTracks.item(idx).flighttrack_model == self.active_flight_track:
                        self.listFlightTracks.item(idx).setText(self.active_flight_track.name)
            else:
                QtWidgets.QMessageBox.warning(self, "Save flight track",
                                              f"File extension is not '.ftml'!\n{filename:}")

    def activate_flight_track(self, item):
        """Set the currently selected flight track to be the active one, i.e.
           the one that is displayed in the views (only one flight track can be
           displayed at a time).
        """
        self.active_flight_track = item.flighttrack_model
        for i in range(self.listViews.count()):
            view_item = self.listViews.item(i)
            view_item.window.setFlightTrackModel(self.active_flight_track)
        font = QtGui.QFont()
        for i in range(self.listFlightTracks.count()):
            self.listFlightTracks.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def show_online_help(self):
        """Open Documentation in a browser"""
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl("http://mss.readthedocs.io/en/stable"))

    def show_about_dialog(self):
        """Show the 'About MSUI' dialog to the user.
        """
        dlg = MSS_AboutDialog(parent=self)
        dlg.setModal(True)
        dlg.exec_()

    def status(self):
        if constants.CACHED_CONFIG_FILE is None:
            return ("Status : System Configuration")
        else:
            filename = constants.CACHED_CONFIG_FILE
            head_filename, tail_filename = os.path.split(filename)
            return("Status : User Configuration '" + tail_filename + "' loaded")


def main():
    try:
        prefix = os.environ["CONDA_DEFAULT_ENV"]
    except KeyError:
        prefix = ""
    app_prefix = prefix
    if prefix:
        app_prefix = f"-{prefix}"
    icon_hash = hashlib.md5('.'.join([__version__, app_prefix]).encode('utf-8')).hexdigest()

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)
    parser.add_argument("--debug", help="show debugging log messages on console", action="store_true", default=False)
    parser.add_argument("--logfile", help="Specify logfile location. Set to empty string to disable.", action="store",
                        default=os.path.join(constants.MSS_CONFIG_PATH, "mss_pyui.log"))
    parser.add_argument("-m", "--menu", help="adds mss to menu", action="store_true", default=False)
    parser.add_argument("-d", "--deinstall", help="removes mss from menu", action="store_true", default=False)

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    setup_logging(args)

    if args.menu:
        # Experimental feature to get mss into application menu
        if platform.system() == "Linux":
            icon_size = '48x48'
            src_icon_path = icons(icon_size)
            icon_destination = constants.POSIX["icon_destination"].format(icon_size, icon_hash)
            dirname = os.path.dirname(icon_destination)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            shutil.copyfile(src_icon_path, icon_destination)
            desktop = constants.POSIX["desktop"]
            application_destination = constants.POSIX["application_destination"].format(app_prefix)
            dirname = os.path.dirname(application_destination)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            if prefix:
                prefix = f"({prefix})"
            desktop = desktop.format(prefix,
                                     os.path.join(sys.prefix, "bin", "mss"),
                                     icon_destination)
            with open(application_destination, 'w') as f:
                f.write(desktop)
            logging.info("menu entry created")
        sys.exit()
    if args.deinstall:
        application_destination = constants.POSIX["application_destination"].format(app_prefix)
        if os.path.exists(application_destination):
            os.remove(application_destination)
        icon_size = '48x48'
        icon_destination = constants.POSIX["icon_destination"].format(icon_size, icon_hash)
        if os.path.exists(icon_destination):
            os.remove(icon_destination)
        logging.info("menu entry removed")
        sys.exit()

    logging.info("MSS Version: %s", __version__)
    logging.info("Python Version: %s", sys.version)
    logging.info("Platform: %s (%s)", platform.platform(), platform.architecture())
    logging.info("Launching user interface...")

    application = QtWidgets.QApplication(sys.argv)
    application.setWindowIcon(QtGui.QIcon(icons('128x128')))
    application.setApplicationDisplayName("MSS")
    mainwindow = MSSMainWindow()
    mainwindow.create_new_flight_track()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
