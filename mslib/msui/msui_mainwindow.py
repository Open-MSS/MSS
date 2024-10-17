#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    mslib.msui.msui_mainwindow
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Mission Support System Python/Qt User Interface
    Main window of the user interface application. Manages view and tool windows
    (the user can open multiple windows) and provides functionality to open, save,
    and switch between flight tracks.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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

import copy
import functools
import importlib
import logging
import os
import re
import sys
import fs

from slugify import slugify
from mslib import __version__
from mslib.msui.qt5 import ui_mainwindow as ui
from mslib.msui.qt5 import ui_about_dialog as ui_ab
from mslib.msui.qt5 import ui_shortcuts as ui_sh
from mslib.msui import flighttrack as ft
from mslib.msui import tableview, topview, sideview, linearview
from mslib.msui import constants, editor, mscolab
from mslib.plugins.io.csv import load_from_csv, save_to_csv
from mslib.msui.icons import icons, python_powered
from mslib.utils.qt import get_open_filenames, get_save_filename, show_popup
from mslib.utils.config import read_config_file, config_loader
from PyQt5 import QtGui, QtCore, QtWidgets
from mslib.utils import release_info

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Add config path to PYTHONPATH so plugins located there may be found
sys.path.append(constants.MSUI_CONFIG_PATH)


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
        super().__init__(view_name, parent, _type)

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
                 user_type=QtWidgets.QListWidgetItem.UserType):
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
        super().__init__(
            view_name, parent, user_type)

        self.parent = parent
        self.flighttrack_model = flighttrack_model


class MSUI_ShortcutsDialog(QtWidgets.QDialog, ui_sh.Ui_ShortcutsDialog):
    """
    Dialog showing shortcuts for all currently open windows
    """

    def __init__(self, tutorial_mode=False):
        super().__init__(QtWidgets.QApplication.activeWindow())
        self.tutorial_mode = tutorial_mode
        self.setupUi(self)
        self.current_shortcuts = None
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
        self.cbHighlight.stateChanged.connect(self.filter_shortcuts)
        self.cbDisplayType.currentTextChanged.connect(self.fill_list)
        self.cbAdvanced.stateChanged.emit(self.cbAdvanced.checkState())
        self.oldReject = self.reject
        self.reject = self.custom_reject

    def custom_reject(self):
        """
        Reset highlighted objects when closing the shortcuts dialog
        """
        self.reset_highlight()
        self.oldReject()

    def reset_highlight(self):
        """
        Iterates through all shortcuts and resets the stylesheet
        """
        if self.current_shortcuts:
            for shortcuts in self.current_shortcuts.values():
                for shortcut in shortcuts.values():
                    try:
                        if shortcut[-1] and hasattr(shortcut[-1], "setStyleSheet"):
                            shortcut[-1].setStyleSheet("")
                    except RuntimeError:
                        # when we have deleted a QAction we have to update the list
                        # Because we cannot test if the underlying object exist we have to catch that
                        self.fill_list()

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
            if hasattr(widget, "window"):
                name = widget.window().windowTitle()
            else:
                name = widget.objectName()
            if len(name) == 0 or (hasattr(widget, "window") and widget.window().isHidden()):
                continue
            header = QtWidgets.QTreeWidgetItem(self.treeWidget)
            header.setText(0, name)
            if hasattr(widget, "window") and widget.window() == self.parent():
                header.setExpanded(True)
                header.setSelected(True)
                self.treeWidget.setCurrentItem(header)
            for objectName in self.current_shortcuts[widget].keys():
                description, text, _, shortcut, obj = self.current_shortcuts[widget][objectName]
                if obj is None:
                    continue
                item = QtWidgets.QTreeWidgetItem(header)
                item.source_object = obj
                itemText = description if self.cbDisplayType.currentText() == 'Tooltip' \
                    else text if self.cbDisplayType.currentText() == 'Text' else obj.objectName()
                item.setText(0, f"{itemText}: {shortcut}")
                item.setToolTip(0, f"ToolTip: {description}\nText: {text}\nObjectName: {objectName}")
                header.addChild(item)
        self.filter_shortcuts(self.leShortcutFilter.text())

    def get_shortcuts(self):
        """
        Iterates through all top level widgets and puts their shortcuts in a dictionary
        """
        shortcuts = {}
        for qobject in QtWidgets.QApplication.allWidgets():
            actions = []
            # QAction
            actions.extend([
                (action.parent().window() if hasattr(action.parent(), "window") else action.parent(),
                 action.toolTip(), action.text().replace("&&", "%%").replace("&", "").replace("%%", "&"),
                 action.objectName(),
                 ",".join([shortcut.toString() for shortcut in action.shortcuts()]), action)
                for action in qobject.findChildren(
                    QtWidgets.QAction) if len(action.shortcuts()) > 0 or self.cbNoShortcut.checkState()])

            # QShortcut
            actions.extend([(shortcut.parentWidget().window(), shortcut.whatsThis(), "",
                             shortcut.objectName(), shortcut.key().toString(), shortcut)
                            for shortcut in qobject.findChildren(QtWidgets.QShortcut)])

            # QAbstractButton
            actions.extend([(button.window(), button.toolTip(), button.text().replace("&&", "%%").replace("&", "")
                             .replace("%%", "&"), button.objectName(),
                             button.shortcut().toString() if button.shortcut() else "", button)
                            for button in qobject.findChildren(QtWidgets.QAbstractButton) if button.shortcut() or
                            self.cbNoShortcut.checkState()])

            # Additional objects which have no shortcuts, if requested
            # QComboBox
            actions.extend([(obj.window(), obj.toolTip(), obj.currentText(), obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QComboBox) if self.cbNoShortcut.checkState()])

            # QAbstractSpinBox, QLineEdit, QDoubleSpinBox
            actions.extend([(obj.window(), obj.toolTip(), obj.text(), obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QAbstractSpinBox) +
                            qobject.findChildren(QtWidgets.QLineEdit) + qobject.findChildren(QtWidgets.QDoubleSpinBox)
                            if self.cbNoShortcut.checkState()])
            # QPlainTextEdit, QTextEdit
            actions.extend([(obj.window(), obj.toolTip(), obj.toPlainText(), obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QPlainTextEdit) +
                            qobject.findChildren(QtWidgets.QTextEdit)
                            if self.cbNoShortcut.checkState()])

            # QLabel
            actions.extend([(obj.window(), obj.toolTip(), obj.text(), obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QLabel)
                            if self.cbNoShortcut.checkState()])

            # FigureCanvas
            actions.extend([(obj.window(), "", obj.figure.axes[0].get_title(), obj.objectName(), "", obj)
                           for obj in qobject.findChildren(FigureCanvas)
                           if self.cbNoShortcut.checkState()])

            # QMenu
            actions.extend([(obj.window(), obj.toolTip(), obj.title(), obj.objectName(), "", obj)
                           for obj in qobject.findChildren(QtWidgets.QMenu)
                           if self.cbNoShortcut.checkState()])

            # QMenuBar
            actions.extend([(obj.window(), "menubar", "menubar", obj.objectName(), "", obj)
                            for obj in qobject.findChildren(QtWidgets.QMenuBar)
                            if self.cbNoShortcut.checkState()])

            if not any(action for action in actions if action[3] == "actionShortcuts"):
                actions.append((qobject.window(), "Show Current Shortcuts", "Show Current Shortcuts",
                                "Show Current Shortcuts", "Alt+S", None))
            if not any(action for action in actions if action[3] == "actionSearch"):
                actions.append((qobject.window(), "Search for interactive text in the UI",
                                "Search for interactive text in the UI", "Search for interactive text in the UI",
                                "Ctrl+F", None))

            if "://" in constants.MSUI_CONFIG_PATH:
                # Todo remove all os.path dependencies, when needed use getsyspath
                pix_dir = fs.path.combine(constants.MSUI_CONFIG_PATH, 'tutorial_images')
                try:
                    _fs = fs.open_fs(pix_dir)
                except fs.errors.CreateFailed:
                    dir_path, name = fs.path.split(pix_dir)
                    _fs = fs.open_fs(dir_path)
                    _fs.makedir(name)
            else:
                pix_dir = os.path.join(constants.MSUI_CONFIG_PATH, 'tutorial_images')
                if not os.path.exists(pix_dir):
                    os.makedirs(pix_dir)
            for item in actions:
                if len(item[2]) > 0:
                    # These are twice defined, but only one can be used for highlighting
                    if (item[2] in ['Pan', 'Home', 'Forward',
                                    'Back', 'Zoom', 'Save', 'Mv WP',
                                    'Ins WP', 'Del WP'] and isinstance(item[5], QtWidgets.QAction) or
                            len(item[0].objectName()) == 0):
                        continue

                    if item[0] not in shortcuts:
                        shortcuts[item[0]] = {}
                    shortcuts[item[0]][item[5]] = item[1:]
                    if self.tutorial_mode:
                        try:
                            prefix = item[0].objectName()
                            attr = item[2]
                            if item[5] is None:
                                continue
                            pixmap = item[5].grab()
                            pix_name = slugify(f"{prefix}-{attr}")
                            if pix_name.startswith("Search") is False:
                                pix_file = f"{pix_name}.png"
                                _fs = fs.open_fs(pix_dir)
                                pix_file = os.path.join(_fs.getsyspath("."), pix_file)
                                pixmap.save(pix_file, 'png')
                        except AttributeError:
                            pass
        return shortcuts

    def filter_shortcuts(self, text="Nothing", rerun=True):
        """
        Hides all shortcuts not containing the text
        """
        text = self.leShortcutFilter.text()
        self.reset_highlight()

        window_count = 0
        for window in self.treeWidget.findItems("", QtCore.Qt.MatchContains):
            if not window.isHidden():
                window_count += 1

        for window in self.treeWidget.findItems("", QtCore.Qt.MatchContains):
            wms_hits = 0

            for child_index in range(window.childCount()):
                widget = window.child(child_index)
                if text.lower() in widget.text(0).lower() or text.lower() in window.text(0).lower():
                    widget.setHidden(False)
                    wms_hits += 1
                else:
                    widget.setHidden(True)

            if wms_hits == 1 and (self.cbHighlight.isChecked() or window_count == 1):
                for child_index in range(window.childCount()):
                    widget = window.child(child_index)
                    if (not widget.isHidden()) and hasattr(widget.source_object, "setStyleSheet"):
                        widget.source_object.setStyleSheet("background-color: yellow;")
                        break

            if wms_hits == 0 and len(text) > 0:
                window.setHidden(True)
            else:
                window.setHidden(False)

        self.filterRemoveAction.setVisible(len(text) > 0)
        if rerun:
            self.filter_shortcuts(text, False)


class MSUI_AboutDialog(QtWidgets.QDialog, ui_ab.Ui_AboutMSUIDialog):
    """Dialog showing information about MSUI. Most of the displayed text is
       defined in the QtDesigner file.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super().__init__(parent)
        self.setupUi(self)
        self.lblVersion.setText(f"Version: {__version__}")
        self.lblNewVersion.setText(f"{release_info.check_for_new_release()[0]}")
        self.milestone_url = f'https://github.com/Open-MSS/MSS/issues?q=is%3Aclosed+milestone%3A{__version__[:-1]}'
        self.lblChanges.setText(f'<a href="{self.milestone_url}">New Features and Changes</a>')
        blub = QtGui.QPixmap(python_powered())
        self.lblPython.setPixmap(blub)


class MSUIMainWindow(QtWidgets.QMainWindow, ui.Ui_MSUIMainWindow):
    """MSUI new main window class. Provides user interface elements for managing
       flight tracks, views and MSColab functionalities.
    """

    viewsChanged = QtCore.pyqtSignal(name="viewsChanged")
    signal_activate_flighttrack = QtCore.pyqtSignal(ft.WaypointsTableModel, name="signal_activate_flighttrack")
    signal_activate_operation = QtCore.pyqtSignal(int, name="signal_activate_operation")
    signal_operation_added = QtCore.pyqtSignal(int, str, name="signal_operation_added")
    signal_operation_removed = QtCore.pyqtSignal(int, name="signal_operation_removed")
    signal_login_mscolab = QtCore.pyqtSignal(str, str, name="signal_login_mscolab")
    signal_logout_mscolab = QtCore.pyqtSignal(name="signal_logout_mscolab")
    signal_listFlighttrack_doubleClicked = QtCore.pyqtSignal()
    signal_permission_revoked = QtCore.pyqtSignal(int)
    signal_render_new_permission = QtCore.pyqtSignal(int, str)
    refresh_signal_connect = QtCore.pyqtSignal()

    def __init__(self, local_operations_data=None, tutorial_mode=False, *args):
        super().__init__(*args)
        self.tutorial_mode = tutorial_mode
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('32x32')))
        # This code is required in Windows 7 to use the icon set by setWindowIcon in taskbar
        # instead of the default Icon of python/pythonw
        try:
            import ctypes
            myappid = f"msui.msui.{__version__}"  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except (ImportError, AttributeError) as error:
            logging.debug("AttributeError, ImportError Exception %s", error)

        self.config_editor = None
        self.local_active = True
        self.new_flight_track_counter = 0
        edit = editor.ConfigurationEditorWindow(self)
        # ToDo review if this can replace of other config_loader() calls
        self.config_for_gui = edit.last_saved
        # automated_plotting_* parameters must be stored or loaded by the mssautoplot.json file
        self.config_for_gui["automated_plotting_flights"].clear()
        self.config_for_gui["automated_plotting_hsecs"].clear()
        self.config_for_gui["automated_plotting_vsecs"].clear()
        self.config_for_gui["automated_plotting_lsecs"].clear()

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
        self.add_plugin_submenu("CSV", "csv", load_from_csv, picker_default, plugin_type="Import")
        self.add_plugin_submenu("CSV", "csv", save_to_csv, picker_default, plugin_type="Export")
        self.add_plugins()

        # Status Bar
        self.statusBar.showMessage(self.status())

        # Create MSColab instance to handle all MSColab functionalities
        self.mscolab = mscolab.MSUIMscolab(parent=self, local_operations_data=local_operations_data)

        # Setting up MSColab Tab
        self.connectBtn.clicked.connect(self.mscolab.open_connect_window)

        self.shortcuts_dlg = None

        # deactivate vice versa selection of Operation, inactive operation or Flight Track

        self.listFlightTracks.itemClicked.connect(
            lambda: self.listOperationsMSC.setCurrentItem(None))
        self.listOperationsMSC.itemClicked.connect(
            lambda: self.listFlightTracks.setCurrentItem(None))
        # disable category until connected/login into mscolab
        self.filterCategoryCb.setEnabled(False)
        self.mscolab.signal_unarchive_operation.connect(self.activate_operation_slot)
        self.mscolab.signal_operation_added.connect(self.add_operation_slot)
        self.mscolab.signal_operation_removed.connect(self.remove_operation_slot)
        self.mscolab.signal_login_mscolab.connect(lambda d, t: self.signal_login_mscolab.emit(d, t))
        self.mscolab.signal_logout_mscolab.connect(lambda: self.signal_logout_mscolab.emit())
        self.mscolab.signal_listFlighttrack_doubleClicked.connect(
            lambda: self.signal_listFlighttrack_doubleClicked.emit())
        self.mscolab.signal_permission_revoked.connect(lambda op_id: self.signal_permission_revoked.emit(op_id))
        self.mscolab.signal_render_new_permission.connect(
            lambda op_id, path: self.signal_render_new_permission.emit(op_id, path))

        self.openOperationsGb.hide()

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
        self.import_plugins = {}
        self.export_plugins = {}
        self.add_import_plugins(picker_default)
        self.add_export_plugins(picker_default)

    @QtCore.pyqtSlot(int)
    def activate_operation_slot(self, active_op_id):
        self.signal_activate_operation.emit(active_op_id)

    @QtCore.pyqtSlot(int, str)
    def add_operation_slot(self, op_id, path):
        self.signal_operation_added.emit(op_id, path)

    @QtCore.pyqtSlot(int)
    def remove_operation_slot(self, op_id):
        self.signal_operation_removed.emit(op_id)

    def add_plugin_submenu(self, name, extension, function, pickertype, plugin_type="Import"):
        if plugin_type == "Import":
            menu = self.menuImportFlightTrack
            action_name = "actionImportFlightTrack" + clean_string(name)
            handler = self.handle_import_local
        elif plugin_type == "Export":
            menu = self.menuExportActiveFlightTrack
            action_name = "actionExportFlightTrack" + clean_string(name)
            handler = self.handle_export_local

        if hasattr(self, action_name):
            raise ValueError(f"'{action_name}' has already been set!")
        action = QtWidgets.QAction(self)
        action.setObjectName(action_name)
        action.setText(QtCore.QCoreApplication.translate("MSUIMainWindow", name, None))
        action.triggered.connect(functools.partial(handler, extension, function, pickertype))
        menu.addAction(action)
        setattr(self, action_name, action)

    def update_treewidget_op_fl(self, op_fl, flight):
        if op_fl == "operation":
            for index in range(self.listOperationsMSC.count()):
                item = self.listOperationsMSC.item(index)
                if flight == item.operation_path:
                    item = self.listOperationsMSC.item(index)
                    self.mscolab.set_active_op_id(item)
                    break
        else:
            for index in range(self.listFlightTracks.count()):
                item = self.listFlightTracks.item(index)
                if flight == item.text():
                    item = self.listFlightTracks.item(index)
                    self.activate_flight_track(item)
                    break

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
            self.import_plugins[name] = (imported_function, extension)

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
            self.export_plugins[name] = (imported_function, extension)

    def remove_plugins(self):
        for name, _ in self.import_plugins.items():
            full_name = "actionImportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuImportFlightTrack.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuImportFlightTrack.removeAction(actions[0])
            delattr(self, full_name)
        self.import_plugins = {}

        for name, _ in self.export_plugins.items():
            full_name = "actionExportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuExportActiveFlightTrack.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuExportActiveFlightTrack.removeAction(actions[0])
            delattr(self, full_name)
        self.export_plugins = {}

    def handle_import_local(self, extension, function, pickertype):
        filenames = get_open_filenames(
            self, "Import Flight Track",
            self.last_save_directory,
            f"Flight Track (*.{extension});;All files (*.*)",
            pickertype=pickertype)
        if self.local_active:
            if filenames is not None:
                activate = True
                if len(filenames) > 1:
                    activate = False
                for name in filenames:
                    self.create_new_flight_track(filename=name, function=function, activate=activate)
                self.last_save_directory = fs.path.dirname(name)
        else:
            for name in filenames:
                self.mscolab.handle_import_msc(name, extension, function, pickertype)

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

    def create_new_flight_track(self, template=None, filename=None, function=None, activate=True):
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
            # Create a new flight track from the waypoints' template.
            self.new_flight_track_counter += 1
            waypoints_model = ft.WaypointsTableModel(
                name=f"new flight track ({self.new_flight_track_counter:d})")
            # Make a copy of the template. Otherwise, all new flight tracks would
            # use the same data structure in memory.
            template_copy = copy.deepcopy(template)
            waypoints_model.insertRows(0, rows=len(template_copy), waypoints=template_copy)

        if waypoints_model is not None:
            # Create a new list entry for the flight track. Make the item name editable.
            listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
            listitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            # Activate new item
            if activate:
                self.activate_flight_track(listitem)

    def activate_flight_track(self, item):
        """Set the currently selected flight track to be the active one, i.e.
           the one that is displayed in the views (only one flight track can be
           displayed at a time).
        """
        self.mscolab.switch_to_local()
        # self.setWindowModality(QtCore.Qt.NonModal)
        self.active_flight_track = item.flighttrack_model
        self.update_active_flight_track()
        font = QtGui.QFont()
        for i in range(self.listFlightTracks.count()):
            self.listFlightTracks.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)
        self.userCountLabel.hide()
        self.menu_handler()
        self.signal_activate_flighttrack.emit(self.active_flight_track)

    def update_active_flight_track(self, old_flight_track_name=None):
        logging.debug("update_active_flight_track")
        for i in range(self.listViews.count()):
            view_item = self.listViews.item(i)
            view_item.window.setFlightTrackModel(self.active_flight_track)
            # local we have always all options enabled
            view_item.window.enable_navbar_action_buttons()
            if old_flight_track_name is not None:
                view_item.window.setWindowTitle(view_item.window.windowTitle().replace(old_flight_track_name,
                                                                                       self.active_flight_track.name))

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
            self.save_as()

    def save_as_handler(self):
        self.save_as()

    def save_as(self):
        """
        Slot for the 'Save Active Flight Track As' menu entry.
        """
        default_filename = os.path.join(self.last_save_directory, self.active_flight_track.name + ".ftml")
        file_type = ["Flight track (*.ftml)"]
        filepicker_default = config_loader(dataset="filepicker_default")
        filename = get_save_filename(
            self, "Save Flight Track", default_filename, ";;".join(file_type), pickertype=filepicker_default
        )
        logging.debug("filename : '%s'", filename)
        if filename:
            ext = "ftml"
            self.save_flight_track(filename)
            self.last_save_directory = fs.path.dirname(filename)
            self.active_flight_track.filename = filename
            self.active_flight_track.name = fs.path.basename(filename.replace(f"{ext}", "").strip())

    def save_flight_track(self, file_name):
        ext = ".ftml"
        if file_name:
            if file_name.endswith(ext):
                try:
                    self.active_flight_track.save_to_ftml(file_name)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while saving flight track to FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))

            for idx in range(self.listFlightTracks.count()):
                if self.listFlightTracks.item(idx).flighttrack_model == self.active_flight_track:
                    old_filght_track_name = self.listFlightTracks.item(idx).text()
                    self.listFlightTracks.item(idx).setText(self.active_flight_track.name)

            self.update_active_flight_track(old_filght_track_name)

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
            try:
                self.mscolab.waypoints_model.name = self.mscolab.active_operation_name
                self.create_view(_type, self.mscolab.waypoints_model)
            except AttributeError:
                # can happen, when the servers secret was changed
                show_popup(self.mscolab.ui, "Error", "Session expired, new login required")

    def create_view(self, _type, model):
        """Method called when the user selects a new view to be opened. Creates
           a new instance of the view and adds a QActiveViewsListWidgetItem to
           the list of open views (self.listViews).
        """
        layout = config_loader(dataset="layout")
        view_window = None
        if _type == "topview":
            # Top view.
            view_window = topview.MSUITopViewWindow(mainwindow=self, model=model,
                                                    active_flighttrack=self.active_flight_track,
                                                    mscolab_server_url=self.mscolab.mscolab_server_url,
                                                    token=self.mscolab.token, tutorial_mode=self.tutorial_mode,
                                                    config_settings=self.config_for_gui)
            view_window.refresh_signal_emit.connect(self.refresh_signal_connect.emit)
            view_window.mpl.resize(layout['topview'][0], layout['topview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['topview'][0], layout['topview'][1])
        elif _type == "sideview":
            # Side view.
            view_window = sideview.MSUISideViewWindow(mainwindow=self, model=model, tutorial_mode=self.tutorial_mode,
                                                      config_settings=self.config_for_gui)
            view_window.refresh_signal_emit.connect(self.refresh_signal_connect.emit)
            view_window.mpl.resize(layout['sideview'][0], layout['sideview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['sideview'][0], layout['sideview'][1])
        elif _type == "tableview":
            # Table view.
            view_window = tableview.MSUITableViewWindow(model=model, tutorial_mode=self.tutorial_mode)
            view_window.centralwidget.resize(layout['tableview'][0], layout['tableview'][1])
        elif _type == "linearview":
            # Linear view.
            view_window = linearview.MSUILinearViewWindow(mainwindow=self, model=model,
                                                          tutorial_mode=self.tutorial_mode,
                                                          config_settings=self.config_for_gui)
            view_window.refresh_signal_emit.connect(self.refresh_signal_connect.emit)
            view_window.mpl.resize(layout['linearview'][0], layout['linearview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['linearview'][0], layout['linearview'][1])

        if view_window is not None:
            # Set view type to window
            view_window.view_type = view_window.name
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
            # disable navbar actions in the view for viewer
            try:
                if self.mscolab.access_level == "viewer":
                    view_window.disable_navbar_action_buttons()
            except AttributeError:
                view_window.enable_navbar_action_buttons()
            self.viewsChanged.emit()
            # this triggers the changeEvent to get the screen position.
            # On X11, a window does not have a frame until the window manager decorates it.
            view_window.showMaximized()
            view_window.showNormal()

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
        if self.mscolab.token is not None:
            self.mscolab.logout()
        read_config_file()
        self.add_plugins()

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
        dlg = MSUI_AboutDialog(parent=self)
        dlg.setModal(True)
        dlg.show()

    def show_shortcuts(self, search_mode=False):
        """Show the shortcuts dialog to the user.
        """
        if QtWidgets.QApplication.activeWindow() == self.shortcuts_dlg:
            return

        self.shortcuts_dlg = MSUI_ShortcutsDialog(
            tutorial_mode=self.tutorial_mode) if not self.shortcuts_dlg else self.shortcuts_dlg

        # In case the dialog gets deleted by QT, recreate it
        try:
            self.shortcuts_dlg.setModal(True)
        except RuntimeError:
            self.shortcuts_dlg = MSUI_ShortcutsDialog(tutorial_mode=self.tutorial_mode)

        self.shortcuts_dlg.setParent(QtWidgets.QApplication.activeWindow(), QtCore.Qt.Dialog)
        self.shortcuts_dlg.reset_highlight()
        self.shortcuts_dlg.fill_list()
        if self.tutorial_mode:
            self.shortcuts_dlg.hide()
        else:
            self.shortcuts_dlg.show()

        self.shortcuts_dlg.cbAdvanced.setHidden(True)
        self.shortcuts_dlg.cbHighlight.setHidden(True)
        self.shortcuts_dlg.cbAdvanced.setCheckState(0)
        self.shortcuts_dlg.cbHighlight.setCheckState(0)
        self.shortcuts_dlg.leShortcutFilter.setText("")
        self.shortcuts_dlg.setWindowTitle("Shortcuts")

        if search_mode:
            self.shortcuts_dlg.setWindowTitle("Search")
            self.shortcuts_dlg.cbAdvanced.setHidden(False)
            self.shortcuts_dlg.cbHighlight.setHidden(False)
            self.shortcuts_dlg.cbDisplayType.setCurrentIndex(1)
            self.shortcuts_dlg.leShortcutFilter.setText("")
            self.shortcuts_dlg.cbAdvanced.setCheckState(2)
            self.shortcuts_dlg.cbNoShortcut.setCheckState(2)
            self.shortcuts_dlg.leShortcutFilter.setFocus()

    def status(self):
        if config_loader() != config_loader(default=True):
            return ("Status : System Configuration")
        else:
            return (f"Status : User Configuration '{constants.MSUI_SETTINGS}' loaded")

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
                if self.config_editor is not None:
                    self.statusBar.showMessage("Save your config changes and try closing again")
                    event.ignore()
                    return
            event.accept()
        else:
            event.ignore()
