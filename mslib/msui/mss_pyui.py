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
import fs

from mslib import __version__
from mslib.msui.mss_qt import ui_mainwindow as ui
from mslib.msui.mss_qt import ui_about_dialog as ui_ab
from mslib.msui.mss_qt import ui_shortcuts as ui_sh
from mslib.msui import flighttrack as ft
from mslib.msui import tableview, topview, sideview, linearview
from mslib.msui import editor
from mslib.msui import constants
from mslib.msui import wms_control
from mslib.msui import mscolab
from mslib.msui.updater import UpdaterUI
from mslib.utils import setup_logging
from mslib.plugins.io.csv import load_from_csv, save_to_csv
from mslib.msui.icons import icons, python_powered
from mslib.msui.mss_qt import get_open_filename, get_save_filename, Worker, Updater
from mslib.utils.config import read_config_file, config_loader
from PyQt5 import QtGui, QtCore, QtWidgets, QtTest

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
    open_views = []

    def __init__(self, view_window, parent=None, viewsChanged=None, mscolab=False,
                 _type=QtWidgets.QListWidgetItem.UserType):
        """Add ID number to the title of the corresponding view window.
        """
        QActiveViewsListWidgetItem.opened_views += 1
        view_name = f"({QActiveViewsListWidgetItem.opened_views:d}) {view_window.name}"
        super(QActiveViewsListWidgetItem, self).__init__(view_name, parent, _type)

        view_window.setWindowTitle(f"({QActiveViewsListWidgetItem.opened_views:d}) {view_window.windowTitle()} - "
                                   f"{view_window.waypoints_model.name}")
        view_window.setIdentifier(view_name)
        self.window = view_window
        self.parent = parent
        self.viewsChanged = viewsChanged
        QActiveViewsListWidgetItem.open_views.append(view_window)

    def view_destroyed(self):
        """Slot that removes this QListWidgetItem from the parent (the
           QListWidget) if the corresponding view has been deleted.
        """
        if self.parent is not None:
            self.parent.takeItem(self.parent.row(self))
            for index, window in enumerate(QActiveViewsListWidgetItem.open_views):
                if window.identifier == self.window.identifier:
                    del QActiveViewsListWidgetItem.open_views[index]
                    break
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


class MSS_ShortcutsDialog(QtWidgets.QDialog, ui_sh.Ui_ShortcutsDialog):
    """
    Dialog showing shortcuts for all currently open windows
    """
    def __init__(self):
        super(MSS_ShortcutsDialog, self).__init__(QtWidgets.QApplication.activeWindow())
        self.setupUi(self)
        self.treeWidget.itemDoubleClicked.connect(self.double_clicked)
        self.treeWidget.itemClicked.connect(self.clicked)
        self.leShortcutFilter.textChanged.connect(self.filter_shortcuts)
        self.filterRemoveAction = self.leShortcutFilter.addAction(QtGui.QIcon(icons("64x64", "remove.png")),
                                                                  QtWidgets.QLineEdit.TrailingPosition)
        self.filterRemoveAction.setVisible(False)
        self.filterRemoveAction.setToolTip("Click to remove the filter")
        self.filterRemoveAction.triggered.connect(lambda: self.leShortcutFilter.setText(""))
        self.cbNoShortcut.stateChanged.connect(self.fill_list)
        self.cbAdvanced.stateChanged.connect(lambda i: (self.cbNoShortcut.setVisible(i),
                                                        self.leShortcutFilter.setVisible(i),
                                                        self.cbDisplayType.setVisible(i),
                                                        self.label.setVisible(i),
                                                        self.label_2.setVisible(i),
                                                        self.line.setVisible(i)))
        self.cbDisplayType.currentTextChanged.connect(self.fill_list)
        self.cbAdvanced.stateChanged.emit(self.cbAdvanced.checkState())

    def reset_highlight(self):
        """
        Iterates through all shortcuts and resets the stylesheet
        """
        for shortcuts in self.current_shortcuts.values():
            for shortcut in shortcuts.values():
                if shortcut[-1] and hasattr(shortcut[-1], "setStyleSheet"):
                    shortcut[-1].setStyleSheet("")

    def clicked(self, item):
        """
        Highlights the selected item in the GUI as yellow
        """
        self.reset_highlight()
        if hasattr(item, "source_object") and item.source_object and hasattr(item.source_object, "setStyleSheet"):
            item.source_object.setStyleSheet("background-color:yellow;")

    def double_clicked(self, item):
        """
        Executes the shortcut for the doubleclicked item
        """
        if hasattr(item, "source_object") and item.source_object:
            self.reset_highlight()
            self.hide()
            obj = item.source_object
            if isinstance(obj, QtWidgets.QShortcut):
                obj.activated.emit()
            elif isinstance(obj, QtWidgets.QAction):
                obj.trigger()
            elif isinstance(obj, QtWidgets.QAbstractButton):
                obj.click()
            elif isinstance(obj, QtWidgets.QComboBox):
                QtCore.QTimer.singleShot(200, obj.showPopup)
            elif isinstance(obj, QtWidgets.QLineEdit) or isinstance(obj, QtWidgets.QAbstractSpinBox):
                obj.setFocus()

    def fill_list(self):
        """
        Fills the treeWidget with all relevant windows as top level items and their shortcuts as children
        """
        self.treeWidget.clear()
        self.current_shortcuts = self.get_shortcuts()
        for widget in self.current_shortcuts:
            name = widget.window().windowTitle()
            if len(name) == 0 or widget.window().isHidden():
                continue
            header = QtWidgets.QTreeWidgetItem(self.treeWidget)
            header.setText(0, name)
            if widget.window() == self.parent():
                header.setExpanded(True)
                header.setSelected(True)
                self.treeWidget.setCurrentItem(header)
            for description, shortcut in self.current_shortcuts[widget].items():
                item = QtWidgets.QTreeWidgetItem(header)
                item.source_object = shortcut[-1]
                item.setText(0, f"{description}: {shortcut[0]}")
                header.addChild(item)
        self.filter_shortcuts(self.leShortcutFilter.text())

    def get_shortcuts(self):
        """
        Iterates through all top level widgets and puts their shortcuts in a dictionary
        """
        d_type = self.cbDisplayType.currentText()
        shortcuts = {}
        for qobject in QtWidgets.QApplication.topLevelWidgets():
            actions = [(qobject.window(), "Show Current Shortcuts", "Alt+S", None)]
            actions.extend([
                (action.parent().window(), action.objectName() if d_type == "ObjectName" else action.toolTip(),
                 ",".join([shortcut.toString() for shortcut in action.shortcuts()]), action)
                for action in qobject.findChildren(QtWidgets.QAction) if len(action.shortcuts()) > 0 or
                self.cbNoShortcut.checkState()])
            actions.extend([(shortcut.parentWidget().window(), shortcut.objectName() if d_type == "ObjectName" else
                            shortcut.whatsThis(), shortcut.key().toString(), shortcut)
                            for shortcut in qobject.findChildren(QtWidgets.QShortcut)])
            actions.extend([(button.window(), button.toolTip() if d_type == "Tooltip" else button.text() if
                            d_type == "Text" else button.objectName(),
                             button.shortcut().toString() if button.shortcut() else "", button)
                            for button in qobject.findChildren(QtWidgets.QAbstractButton) if button.shortcut() or
                            self.cbNoShortcut.checkState()])

            # Additional objects which have no shortcuts, if requested
            actions.extend([(obj.window(), obj.toolTip() if d_type == "Tooltip" else obj.currentText() if
                            d_type == "Text" else obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QComboBox) if self.cbNoShortcut.checkState()])
            actions.extend([(obj.window(), obj.toolTip() if d_type == "Tooltip" else obj.text() if
                            d_type == "Text" else obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QAbstractSpinBox) +
                            qobject.findChildren(QtWidgets.QLineEdit)
                            if self.cbNoShortcut.checkState()])
            actions.extend([(obj.window(), obj.toolTip() if d_type == "Tooltip" else obj.toPlainText() if
                            d_type == "Text" else obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QPlainTextEdit) +
                            qobject.findChildren(QtWidgets.QTextEdit)
                            if self.cbNoShortcut.checkState()])

            for item in actions:
                if item[0] not in shortcuts:
                    shortcuts[item[0]] = {}
                shortcuts[item[0]][item[1].replace(f"({item[2]})", "").strip()] = [item[2], item[3]]

        return shortcuts

    def filter_shortcuts(self, text):
        """
        Hides all shortcuts not containing the text
        """
        for window in self.treeWidget.findItems("", QtCore.Qt.MatchContains):
            wms_hits = 0

            for child_index in range(window.childCount()):
                widget = window.child(child_index)
                if text.lower() in widget.text(0).lower() or text.lower() in window.text(0).lower():
                    widget.setHidden(False)
                    wms_hits += 1
                else:
                    widget.setHidden(True)
            if wms_hits == 0 and len(text) > 0:
                window.setHidden(True)
            else:
                window.setHidden(False)

        self.filterRemoveAction.setVisible(len(text) > 0)


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
        self.lblVersion.setText(f"Version: {__version__}")
        self.milestone_url = f'https://github.com/Open-MSS/MSS/issues?q=is%3Aclosed+milestone%3A{__version__[:-1]}'
        self.lblChanges.setText(f'<a href="{self.milestone_url}">New Features and Changes</a>')
        blub = QtGui.QPixmap(python_powered())
        self.lblPython.setPixmap(blub)


class MSSMainWindow(QtWidgets.QMainWindow, ui.Ui_MSSMainWindow):
    """MSUI new main window class. Provides user interface elements for managing
       flight tracks, views and MSColab functionalities.
    """

    viewsChanged = QtCore.pyqtSignal(name="viewsChanged")

    def __init__(self, mscolab_data_dir=None, *args):
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

        self.config_editor = None
        self.local_active = True
        self.new_flight_track_counter = 0

        # Reference to the flight track that is currently displayed in the views.
        self.active_flight_track = None
        self.last_save_directory = config_loader(dataset="data_dir")

        # bind meta (ctrl in macOS) to override automatic translation of ctrl to command by qt
        if sys.platform == 'darwin':
            self.actionTopView.setShortcut(QtGui.QKeySequence("Meta+h"))
            self.actionSideView.setShortcut(QtGui.QKeySequence("Meta+v"))
            self.actionTableView.setShortcut(QtGui.QKeySequence("Meta+t"))
            self.actionLinearView.setShortcut(QtGui.QKeySequence("Meta+l"))
            self.actionConfiguration.setShortcut(QtGui.QKeySequence("Ctrl+,"))

        # File menu.
        self.actionNewFlightTrack.triggered.connect(functools.partial(self.create_new_flight_track, None, None))
        self.actionSaveActiveFlightTrack.triggered.connect(self.save_handler)
        self.actionSaveActiveFlightTrackAs.triggered.connect(self.save_as_handler)
        self.actionCloseSelectedFlightTrack.triggered.connect(self.close_selected_flight_track)

        # Views menu.
        self.actionTopView.triggered.connect(functools.partial(self.create_view_handler, "topview"))
        self.actionSideView.triggered.connect(functools.partial(self.create_view_handler, "sideview"))
        self.actionTableView.triggered.connect(functools.partial(self.create_view_handler, "tableview"))
        self.actionLinearView.triggered.connect(functools.partial(self.create_view_handler, "linearview"))

        # Help menu.
        self.actionOnlineHelp.triggered.connect(self.show_online_help)
        self.actionAboutMSUI.triggered.connect(self.show_about_dialog)
        self.actionShortcuts.triggered.connect(self.show_shortcuts)
        self.actionShortcuts.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.actionSearch.triggered.connect(lambda: self.show_shortcuts(True))
        self.actionSearch.setShortcutContext(QtCore.Qt.ApplicationShortcut)

        # # Config
        self.actionConfiguration.triggered.connect(self.open_config_editor)

        # Raise Main Window to front with Ctrl/Cmnd + up keyboard shortcut
        self.addAction(self.actionBringMainWindowToFront)
        self.actionBringMainWindowToFront.triggered.connect(self.bring_main_window_to_front)
        self.actionBringMainWindowToFront.setShortcutContext(QtCore.Qt.ApplicationShortcut)

        # Flight Tracks.
        self.listFlightTracks.itemActivated.connect(self.activate_flight_track)

        # Views.
        self.listViews.itemActivated.connect(self.activate_sub_window)

        # Add default and plugins from settings
        picker_default = config_loader(dataset="filepicker_default")
        self.add_plugin_submenu("FTML", "ftml", None, picker_default, plugin_type="Import")
        self.add_plugin_submenu("FTML", "ftml", None, picker_default, plugin_type="Export")
        self.add_plugins()

        preload_urls = config_loader(dataset="WMS_preload")
        self.preload_wms(preload_urls)

        # Status Bar
        self.statusBar.showMessage(self.status())

        # Create MSColab instance to handle all MSColab functionalities
        self.mscolab = mscolab.MSSMscolab(parent=self, data_dir=mscolab_data_dir)

        # Setting up MSColab Tab
        self.connectBtn.clicked.connect(self.mscolab.open_connect_window)

        self.shortcuts_dlg = None

        # Don't start the updater during a test run of mss_pyui
        if "pytest" not in sys.modules:
            self.updater = UpdaterUI(self)
            self.actionUpdater.triggered.connect(self.updater.show)

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

    def bring_main_window_to_front(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def menu_handler(self):
        self.menuImportFlightTrack.setEnabled(True)
        if not self.local_active and self.mscolab.access_level == "viewer":
            # viewer has no import access to server
            self.menuImportFlightTrack.setEnabled(False)

        # enable/disable flight track menus
        self.actionSaveActiveFlightTrack.setEnabled(self.local_active)
        self.actionSaveActiveFlightTrackAs.setEnabled(self.local_active)

    def add_plugins(self):
        picker_default = config_loader(dataset="filepicker_default")
        self.add_plugin_submenu("CSV", "csv", load_from_csv, picker_default, plugin_type="Import")
        self.add_plugin_submenu("CSV", "csv", save_to_csv, picker_default, plugin_type="Export")
        self.import_plugins = {"csv": load_from_csv}
        self.export_plugins = {"csv": save_to_csv}
        self.add_import_plugins(picker_default)
        self.add_export_plugins(picker_default)

    def add_plugin_submenu(self, name, extension, function, pickertype, plugin_type="Import"):
        if plugin_type == "Import":
            menu = self.menuImportFlightTrack
            action_name = "actionImportFlightTrack" + clean_string(extension)
            handler = self.handle_import_local
        elif plugin_type == "Export":
            menu = self.menuExportActiveFlightTrack
            action_name = "actionExportFlightTrack" + clean_string(extension)
            handler = self.handle_export_local

        if hasattr(self, action_name):
            raise ValueError(f"'{action_name}' has already been set!")
        action = QtWidgets.QAction(self)
        action.setObjectName(action_name)
        action.setText(QtCore.QCoreApplication.translate("MSSMainWindow", name, None))
        action.triggered.connect(functools.partial(handler, extension, function, pickertype))
        menu.addAction(action)
        setattr(self, action_name, action)

    def add_import_plugins(self, picker_default):
        plugins = config_loader(dataset="import_plugins")
        for name in plugins:
            extension, module, function = plugins[name][:3]
            picker_type = picker_default
            if len(plugins[name]) == 4:
                picker_type = plugins[name][3]
            try:
                imported_module = importlib.import_module(module)
                imported_function = getattr(imported_module, function)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on import: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{plugins,}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            try:
                self.add_plugin_submenu(name, extension, imported_function, picker_type, plugin_type="Import")
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on installing plugin: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self.import_plugins}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            self.import_plugins[extension] = imported_function

    def add_export_plugins(self, picker_default):
        plugins = config_loader(dataset="export_plugins")
        for name in plugins:
            extension, module, function = plugins[name][:3]
            picker_type = picker_default
            if len(plugins[name]) == 4:
                picker_type = plugins[name][3]
            try:
                imported_module = importlib.import_module(module)
                imported_function = getattr(imported_module, function)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on import: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error export plugins"),
                    self.tr(f"ERROR: Configuration\n\n{plugins,}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            try:
                self.add_plugin_submenu(name, extension, imported_function, picker_type, plugin_type="Export")
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on installing plugin: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self.export_plugins}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            self.export_plugins[extension] = imported_function

    def remove_plugins(self):
        for name in self.import_plugins:
            full_name = "actionImportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuImportFlightTrack.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuImportFlightTrack.removeAction(actions[0])
            delattr(self, full_name)
        self.import_plugins = {}

        for name in self.export_plugins:
            full_name = "actionExportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuExportActiveFlightTrack.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuExportActiveFlightTrack.removeAction(actions[0])
            delattr(self, full_name)
        self.export_plugins = {}

    def handle_import_local(self, extension, function, pickertype):
        filename = get_open_filename(
            self, "Import Flight Track",
            self.last_save_directory,
            f"Flight Track (*.{extension});;All files (*.*)",
            pickertype=pickertype)
        if self.local_active:
            if filename is not None:
                self.last_save_directory = fs.path.dirname(filename)
                self.create_new_flight_track(filename=filename, function=function)
        else:
            self.mscolab.handle_import_msc(filename, extension, function, pickertype)

    def handle_export_local(self, extension, function, pickertype):
        if self.local_active:
            default_filename = f'{os.path.join(self.last_save_directory, self.active_flight_track.name)}.{extension}'
            filename = get_save_filename(
                self, "Export Flight Track",
                default_filename, f"Flight Track (*.{extension})",
                pickertype=pickertype)
            if filename is not None:
                self.last_save_directory = fs.path.dirname(filename)
                try:
                    if function is None:
                        doc = self.active_flight_track.get_xml_doc()
                        dirname, name = fs.path.split(filename)
                        file_dir = fs.open_fs(dirname)
                        with file_dir.open(name, 'w') as file_object:
                            doc.writexml(file_object, indent="  ", addindent="  ", newl="\n", encoding="utf-8")
                        file_dir.close()
                    else:
                        function(filename, self.active_flight_track.name, self.active_flight_track.waypoints)
                # wildcard exception to be resilient against error introduced by user code
                except Exception as ex:
                    logging.error("file io plugin error: %s %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("file io plugin error"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
        else:
            self.mscolab.handle_export_msc(extension, function, pickertype)

    def create_new_flight_track(self, template=None, filename=None, function=None):
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

        waypoints_model = None
        if filename is not None:
            # function is none if ftml file is selected
            if function is None:
                try:
                    waypoints_model = ft.WaypointsTableModel(filename=filename)
                except (SyntaxError, OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while opening flight track FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
            else:
                try:
                    ft_name, new_waypoints = function(filename)
                    waypoints_model = ft.WaypointsTableModel(name=ft_name, waypoints=new_waypoints)
                # wildcard exception to be resilient against error introduced by user code
                except Exception as ex:
                    logging.error("file io plugin error: %s %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("file io plugin error"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
            if waypoints_model is not None:
                for i in range(self.listFlightTracks.count()):
                    fltr = self.listFlightTracks.item(i)
                    if fltr.flighttrack_model.name == waypoints_model.name:
                        waypoints_model.name += " - imported from file"
                        break
        else:
            # Create a new flight track from the waypoints template.
            self.new_flight_track_counter += 1
            waypoints_model = ft.WaypointsTableModel(
                name=f"new flight track ({self.new_flight_track_counter:d})")
            # Make a copy of the template. Otherwise all new flight tracks would
            # use the same data structure in memory.
            template_copy = copy.deepcopy(template)
            waypoints_model.insertRows(0, rows=len(template_copy), waypoints=template_copy)

        if waypoints_model is not None:
            # Create a new list entry for the flight track. Make the item name editable.
            listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
            listitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            # Activate new item
            self.activate_flight_track(listitem)

    def activate_flight_track(self, item):
        """Set the currently selected flight track to be the active one, i.e.
           the one that is displayed in the views (only one flight track can be
           displayed at a time).
        """
        self.mscolab.switch_to_local()
        # self.setWindowModality(QtCore.Qt.NonModal)
        self.active_flight_track = item.flighttrack_model
        for i in range(self.listViews.count()):
            view_item = self.listViews.item(i)
            view_item.window.setFlightTrackModel(self.active_flight_track)
        font = QtGui.QFont()
        for i in range(self.listFlightTracks.count()):
            self.listFlightTracks.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)
        self.menu_handler()

    def activate_selected_flight_track(self):
        item = self.listFlightTracks.currentItem()
        self.activate_flight_track(item)

    def switch_to_mscolab(self):
        self.local_active = False
        font = QtGui.QFont()
        for i in range(self.listFlightTracks.count()):
            self.listFlightTracks.item(i).setFont(font)
        # disable appropriate menu options
        self.menu_handler()

    def save_handler(self):
        """Slot for the 'Save Active Flight Track' menu entry.
        """
        filename = self.active_flight_track.get_filename()
        if filename:
            self.save_flight_track(filename)
        else:
            self.save_as_handler()

    def save_as_handler(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        default_filename = os.path.join(self.last_save_directory, self.active_flight_track.name + ".ftml")
        file_type = ["Flight track (*.ftml)"] + [f"Flight track (*.{ext})" for ext in self.export_plugins.keys()]
        filename = get_save_filename(
            self, "Save Flight Track", default_filename, ";;".join(file_type), pickertag="filepicker_default"
        )
        logging.debug("filename : '%s'", filename)
        if filename:
            self.save_flight_track(filename)

    def save_flight_track(self, file_name):
        if file_name:
            if file_name.endswith('.ftml'):
                try:
                    self.active_flight_track.save_to_ftml(file_name)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while saving flight track to FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
            else:
                ext = fs.path.splitext(file_name)[-1]
                file_path = fs.path.basename(file_name)
                _function = self.export_plugins[ext[1:]]
                _function(file_name, file_path, self.active_flight_track.waypoints)
                self.active_flight_track.filename = file_name
                self.active_flight_track.name = fs.path.basename(file_name.replace(f"{ext}", "").strip())

            for idx in range(self.listFlightTracks.count()):
                if self.listFlightTracks.item(idx).flighttrack_model == self.active_flight_track:
                    self.listFlightTracks.item(idx).setText(self.active_flight_track.name)

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
        if item.flighttrack_model == self.active_flight_track and self.local_active:
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

    def create_view_handler(self, _type):
        if self.local_active:
            self.create_view(_type, self.active_flight_track)
        else:
            self.mscolab.create_view_msc(_type)

    def create_view(self, _type, model):
        """Method called when the user selects a new view to be opened. Creates
           a new instance of the view and adds a QActiveViewsListWidgetItem to
           the list of open views (self.listViews).
        """
        layout = config_loader(dataset="layout")
        view_window = None
        if _type == "topview":
            # Top view.
            view_window = topview.MSSTopViewWindow(model=model)
            view_window.mpl.resize(layout['topview'][0], layout['topview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['topview'][0], layout['topview'][1])
        elif _type == "sideview":
            # Side view.
            view_window = sideview.MSSSideViewWindow(model=model)
            view_window.mpl.resize(layout['sideview'][0], layout['sideview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['sideview'][0], layout['sideview'][1])
        elif _type == "tableview":
            # Table view.
            view_window = tableview.MSSTableViewWindow(model=model)
            view_window.centralwidget.resize(layout['tableview'][0], layout['tableview'][1])
        elif _type == "linearview":
            # Linear view.
            view_window = linearview.MSSLinearViewWindow(model=model)
            view_window.mpl.resize(layout['linearview'][0], layout['linearview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['linearview'][0], layout['linearview'][1])

        if view_window is not None:
            # Set view type to window
            view_window.view_type = _type
            # Make sure view window will be deleted after being closed, not
            # just hidden (cf. Chapter 5 in PyQt4).
            view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            # Open as a non-modal window.
            view_window.show()
            # Add an entry referencing the new view to the list of views.
            # listitem = QActiveViewsListWidgetItem(view_window, self.listViews, self.viewsChanged, mscolab)
            listitem = QActiveViewsListWidgetItem(view_window, self.listViews, self.viewsChanged)
            view_window.viewCloses.connect(listitem.view_destroyed)
            self.listViews.setCurrentItem(listitem)
            # self.active_view_windows.append(view_window)
            self.viewsChanged.emit()

    def get_active_views(self):
        active_view_windows = []
        for i in range(self.listViews.count()):
            active_view_windows.append(self.listViews.item(i).window)
        return active_view_windows

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

    def restart_application(self):
        while self.listViews.count() > 0:
            self.listViews.item(0).window.handle_force_close()
        self.listViews.clear()
        self.remove_plugins()
        self.add_plugins()
        if self.mscolab.token is not None:
            self.mscolab.logout()
        read_config_file()

    def open_config_editor(self):
        """
        Opens up a JSON config editor
        """
        if self.config_editor is None:
            self.config_editor = editor.ConfigurationEditorWindow(parent=self)
            self.config_editor.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.config_editor.destroyed.connect(self.close_config_editor)
            self.config_editor.restartApplication.connect(self.restart_application)
            self.config_editor.show()
        else:
            self.config_editor.showNormal()
            self.config_editor.activateWindow()

    def close_config_editor(self):
        self.config_editor = None

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

    def show_shortcuts(self, search_mode=False):
        """Show the shortcuts dialog to the user.
        """
        self.shortcuts_dlg = MSS_ShortcutsDialog() if not self.shortcuts_dlg else self.shortcuts_dlg

        # In case the dialog gets deleted by QT, recreate it
        try:
            self.shortcuts_dlg.setModal(True)
        except RuntimeError:
            self.shortcuts_dlg = MSS_ShortcutsDialog()

        self.shortcuts_dlg.setParent(QtWidgets.QApplication.activeWindow(), QtCore.Qt.Dialog)
        self.shortcuts_dlg.fill_list()
        self.shortcuts_dlg.show()
        if search_mode:
            self.shortcuts_dlg.cbDisplayType.setCurrentIndex(1)
            self.shortcuts_dlg.leShortcutFilter.setText("")
            self.shortcuts_dlg.cbAdvanced.setCheckState(2)
            self.shortcuts_dlg.cbNoShortcut.setCheckState(2)
            self.shortcuts_dlg.leShortcutFilter.setFocus()

    def status(self):
        if config_loader() != config_loader(default=True):
            return ("Status : System Configuration")
        else:
            return (f"Status : User Configuration '{constants.MSS_SETTINGS}' loaded")

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
            if self.mscolab.help_dialog is not None:
                self.mscolab.help_dialog.close()
            # cleanup mscolab widgets
            if self.mscolab.token is not None:
                self.mscolab.logout()
            # Table View stick around after MainWindow closes - maybe some dangling reference?
            # This removes them for sure!
            while self.listViews.count() > 0:
                self.listViews.item(0).window.handle_force_close()
            self.listViews.clear()
            self.listFlightTracks.clear()
            # close configuration editor
            if self.config_editor is not None:
                self.config_editor.restart_on_save = False
                self.config_editor.close()
                QtTest.QTest.qWait(5)
                if self.config_editor is not None:
                    self.statusBar.showMessage("Save your config changes and try closing again")
                    event.ignore()
                    return
            event.accept()
        else:
            event.ignore()


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
    parser.add_argument("--update", help="Updates MSS to the newest version", action="store_true", default=False)

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    if args.update:
        updater = Updater()
        updater.on_update_available.connect(lambda old, new: updater.update_mss())
        updater.on_log_update.connect(lambda s: print(s.replace("\n", "")))
        updater.on_status_update.connect(lambda s: print(s.replace("\n", "")))
        updater.run()
        while Worker.workers:
            list(Worker.workers)[0].wait()
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

    read_config_file()
    logging.info("Launching user interface...")

    application = QtWidgets.QApplication(sys.argv)
    application.setWindowIcon(QtGui.QIcon(icons('128x128')))
    application.setApplicationDisplayName("MSS")
    application.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)
    mainwindow = MSSMainWindow()
    mainwindow.setStyleSheet("QListWidget { border: 1px solid grey; }")
    mainwindow.create_new_flight_track()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
