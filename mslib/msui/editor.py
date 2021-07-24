# -*- coding: utf-8 -*-
"""

    mslib.msui.editor
    ~~~~~~~~~~~~~~~~~~~~~~

    config editor for mss_settings.json.

    This file is part of mss.

    :copyright: Copyright 2020 Vaibhav Mehra <veb7vmehra@gmail.com>
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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
import fs
import logging
import json

from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import ui_configuration_editor_window as ui_conf
from PyQt5 import QtWidgets, QtGui, QtCore, QtPrintSupport
from mslib.msui import constants
from mslib.msui.constants import MSS_CONFIG_PATH, MSS_SETTINGS
from mslib.msui.icons import icons

from mslib.support.qt_json_view import model
from mslib.support.qt_json_view.model import JsonModel
from mslib.support.qt_json_view.view import JsonView


class ConfigurationEditorWindow(QtWidgets.QMainWindow, ui_conf.Ui_ConfigurationEditorWindow):
    def __init__(self, parent=None):
        super(ConfigurationEditorWindow, self).__init__(parent)
        self.setupUi(self)

        self.frame.setStyleSheet("QFrame {border: 0;}")

        settings_options = [
            "filepicker_default",
            "import_plugins",
            "export_plugins",
            "locations",
            "predefined_map_sections",
            "traj_nas_lon_identifier",
            "traj_nas_lat_identifier",
            "traj_nas_p_identifier",
            "new_flighttrack_template",
            "new_flighttrack_flightlevel",
            "default_WMS",
            "default_VSEC_WMS",
            "WMS_login",
            "num_interpolation_points",
            "num_labels",
            "wms_cache_max_size_bytes",
            "wms_cache_max_size_bytes",
        ]
        for option in settings_options:
            self.comboBox.addItem(option)

        self.dict_data = {
            "filepicker_default": "qt",
            "import_plugins": {
                "FliteStar": [
                    "txt",
                    "mslib.plugins.io.flitestar",
                    "load_from_flitestar",
                ],
                "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"],
            },
            "export_plugins": {
                "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
                "KML": ["kml", "mslib.plugins.io.kml", "save_to_kml"],
            },
            "locations": {
                "EDMO": [48.08, 11.28],
                "Rio Grande": [-53.783, -67.7],
                "Machu Picchu Base": [-62.091, -58.47],
                "ElCalafate": [-50.28, -72.05],
                "Buenos Aires": [-34.82, -58.54],
                "SanMartin": [-68.13, -67.10],
                "Marambio Base": [-64.23, -56.616],
                "Sal": [16.73, -22.93],
                "Punta Arenas": [-53.16, -70.93],
                "Ushuaia": [-54.8, -68.28],
                "256TO": [-53.778, -67.780],
                "EKIPI": [-53.785, -68.045],
                "ESBON": [-53.7695, -67.4538],
                "ESPAT": [-53.788, -68.186],
                "ILMEN": [-53.6886, -67.4216],
                "GEDAB": [-53.59, -68.407],
                "KOVSI": [-53.868, -68.0398],
                "MUBES": [-52.8025, -68.4792],
                "PUKOX": [-53.765, -67.3135],
                "REDET": [-53.701, -68.051],
                "LOBID": [-53.8526, -67.447],
            },
            "predefined_map_sections": {
                "00 global (cyl)": {
                    "CRS": "EPSG:4326",
                    "map": {
                        "llcrnrlon": -180.0,
                        "llcrnrlat": -90.0,
                        "urcrnrlon": 180.0,
                        "urcrnrlat": 90.0,
                    },
                },
                "01 SADPAP (stereo)": {
                    "CRS": "EPSG:77890290",
                    "map": {
                        "llcrnrlon": -150.0,
                        "llcrnrlat": -45.0,
                        "urcrnrlon": -25.0,
                        "urcrnrlat": -20.0,
                    },
                },
                "02 SADPAP zoom (stereo)": {
                    "CRS": "EPSG:77890290",
                    "map": {
                        "llcrnrlon": -120.0,
                        "llcrnrlat": -65.0,
                        "urcrnrlon": -45.0,
                        "urcrnrlat": -28.0,
                    },
                },
                "03 SADPAP (cyl)": {
                    "CRS": "EPSG:4326",
                    "map": {
                        "llcrnrlon": -100.0,
                        "llcrnrlat": -75.0,
                        "urcrnrlon": -30.0,
                        "urcrnrlat": -30.0,
                    },
                },
                "04 Southern Hemisphere (stereo)": {
                    "CRS": "EPSG:77889270",
                    "map": {
                        "llcrnrlon": 135.0,
                        "llcrnrlat": 0.0,
                        "urcrnrlon": -45.0,
                        "urcrnrlat": 0.0,
                    },
                },
                "05 Europe (cyl)": {
                    "CRS": "EPSG:4326",
                    "map": {
                        "llcrnrlon": -15.0,
                        "llcrnrlat": 35.0,
                        "urcrnrlon": 30.0,
                        "urcrnrlat": 65.0,
                    },
                },
                "06 Germany (cyl)": {
                    "CRS": "EPSG:4326",
                    "map": {
                        "llcrnrlon": 5.0,
                        "llcrnrlat": 45.0,
                        "urcrnrlon": 15.0,
                        "urcrnrlat": 57.0,
                    },
                },
                "07 EDMO-SAL (cyl)": {
                    "CRS": "EPSG:4326",
                    "map": {
                        "llcrnrlon": -40,
                        "llcrnrlat": 10,
                        "urcrnrlon": 30,
                        "urcrnrlat": 60,
                    },
                },
                "08 SAL-BA (cyl)": {
                    "CRS": "EPSG:4326",
                    "map": {
                        "llcrnrlon": -80,
                        "llcrnrlat": -40,
                        "urcrnrlon": -10,
                        "urcrnrlat": 30,
                    },
                },
            },
            "traj_nas_lon_identifier": ["GPS LON", "LONGITUDE"],
            "traj_nas_lat_identifier": ["GPS LAT", "LATITUDE"],
            "traj_nas_p_identifier": ["STATIC PRESSURE"],
            "new_flighttrack_template": ["Rio Grande", "256TO", "GEDAB", "MUBES"],
            "new_flighttrack_flightlevel": 351,
            "default_WMS": [
                "https://forecast.fz-juelich.de/SouthTrac",
                "http://mss.pa.op.dlr.de/mss_wms",
                "https://forecast.fz-juelich.de/campaigns2019",
                "https://forecast.fz-juelich.de/campaigns2017",
                "http://eumetview.eumetsat.int/geoserver/wms",
                "http://osmwms.itc-halle.de/maps/osmfree",
                "http://localhost:8081",
                "https://forecast.fz-juelich.de/mssdevju",
                "https://neowms.sci.gsfc.nasa.gov/wms/wms",
                "https://firms.modaps.eosdis.nasa.gov/wms/",
                "http://eumetview.eumetsat.int/geoserver/wms",
                "https://apps.ecmwf.int/wms/?token=public",
                "https://maps.dwd.de/geoserver/wms",
                "http://msgcpp-ogc-realtime.knmi.nl/msgrt.cgi",
                "http://geoservices.knmi.nl/cgi-bin/HARM_N25.cgi",
            ],
            "default_VSEC_WMS": [
                "https://forecast.fz-juelich.de/SouthTrac",
                "http://mss.pa.op.dlr.de/mss_wms",
                "https://forecast.fz-juelich.de/campaigns2019",
                "https://forecast.fz-juelich.de/campaigns2017",
            ],
            "WMS_login": {
                "https://forecast.fz-juelich.de/campaigns2019": ["user", "pwd"],
                "https://forecast.fz-juelich.de/campaigns2017": ["user", "pwd"],
                "https://forecast.fz-juelich.de/SouthTrac": ["user", "pwd"],
                "http://mss.pa.op.dlr.de/mss_wms": ["user", "pwd"],
            },
            "num_interpolation_points": 201,
            "num_labels": 10,
            "wms_cache_max_size_bytes": 200971520,
            "wms_cache_max_age_seconds": 432000,
        }

        self.view = JsonView()

        self.widget.setLayout(QtWidgets.QHBoxLayout())
        self.widget.layout().addWidget(self.view)

        self.show_all()

        self.comboBox.currentIndexChanged.connect(self.selection_change)

        self.pushButton_2.clicked.connect(self.show_all)

    def show_all(self):
        self.proxy = model.JsonSortFilterProxyModel()
        self.json_model = JsonModel(
            data=self.dict_data, editable_keys=True, editable_values=True
        )
        self.proxy.setSourceModel(self.json_model)
        self.view.setModel(self.proxy)

    def selection_change(self, index):
        data = {self.comboBox.currentText(): self.dict_data[self.comboBox.currentText()]}
        self.proxy = model.JsonSortFilterProxyModel()
        self.json_model = JsonModel(
            data=data, editable_keys=True, editable_values=True
        )
        self.proxy.setSourceModel(self.json_model)
        self.view.setModel(self.proxy)


class EditorMainWindow(QtWidgets.QMainWindow):
    name = "MSSEditor"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    restartApplication = QtCore.pyqtSignal(name="restartApplication")

    def __init__(self, parent=None):
        super(EditorMainWindow, self).__init__(parent)
        self.path = None

        self.file_content = None
        self.layout = QtWidgets.QVBoxLayout()
        # Could also use a QTextEdit and set self.editor.setAcceptRichText(False)
        self.editor = QtWidgets.QPlainTextEdit()

        # Load mss_settings.json (if already exists), change \\ to / so fs can work with it
        self.path = constants.CACHED_CONFIG_FILE
        if self.path is not None:
            self.path = self.path.replace("\\", "/")
            dir_name, file_name = fs.path.split(self.path)
            with fs.open_fs(dir_name) as _fs:
                if _fs.exists(file_name):
                    self.file_content = _fs.readtext(file_name)
                    self.editor.setPlainText(self.file_content)
                    self.update_title()
        else:
            self.path = MSS_SETTINGS
            self.path = self.path.replace("\\", "/")
        self.last_saved = self.editor.toPlainText()

        # Setup the QTextEdit editor configuration
        fixedfont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        fixedfont.setPointSize(12)
        self.editor.setFont(fixedfont)

        self.layout.addWidget(self.editor)

        self.container = QtWidgets.QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        self.file_toolbar = QtWidgets.QToolBar("File")
        self.file_toolbar.setIconSize(QtCore.QSize(14, 14))
        self.addToolBar(self.file_toolbar)
        self.file_menu = self.menuBar().addMenu("&File")

        self.open_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                    'Folder-new.svg')), "Open file...", self)
        self.open_file_action.setStatusTip("Open file")
        self.open_file_action.triggered.connect(self.file_open)
        self.file_menu.addAction(self.open_file_action)
        self.file_toolbar.addAction(self.open_file_action)

        self.save_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                    'Document-save.svg')), "Save and Quit", self)
        self.save_file_action.setStatusTip("Save current page")
        self.save_file_action.triggered.connect(self.file_save_and_quit)
        self.file_menu.addAction(self.save_file_action)
        self.file_toolbar.addAction(self.save_file_action)

        self.saveas_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                      'Document-save-as.svg')), "Save As...", self)
        self.saveas_file_action.setStatusTip("Save current page to specified file")
        self.saveas_file_action.triggered.connect(self.file_saveas)
        self.file_menu.addAction(self.saveas_file_action)
        self.file_toolbar.addAction(self.saveas_file_action)

        self.print_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                'Document-print.svg')), "Print...", self)
        self.print_action.setStatusTip("Print current page")
        self.print_action.triggered.connect(self.file_print)
        self.file_menu.addAction(self.print_action)
        self.file_toolbar.addAction(self.print_action)

        self.quit_action = QtWidgets.QAction("Quit", self)
        self.quit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.quit_action)

        self.edit_toolbar = QtWidgets.QToolBar("Edit")
        self.edit_toolbar.setIconSize(QtCore.QSize(16, 16))
        self.addToolBar(self.edit_toolbar)
        self.edit_menu = self.menuBar().addMenu("&Edit")

        self.undo_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Edit-undo.svg')), "Undo", self)
        self.undo_action.setStatusTip("Undo last change")
        self.undo_action.triggered.connect(self.editor.undo)
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Edit-redo.svg')), "Redo", self)
        self.redo_action.setStatusTip("Redo last change")
        self.redo_action.triggered.connect(self.editor.redo)
        self.edit_toolbar.addAction(self.redo_action)
        self.edit_menu.addAction(self.redo_action)

        self.edit_menu.addSeparator()

        self.cut_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                              'Edit-cut.svg')), "Cut", self)
        self.cut_action.setStatusTip("Cut selected text")
        self.cut_action.triggered.connect(self.editor.cut)
        self.edit_toolbar.addAction(self.cut_action)
        self.edit_menu.addAction(self.cut_action)

        self.copy_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Edit-copy.svg')), "Copy", self)
        self.copy_action.setStatusTip("Copy selected text")
        self.copy_action.triggered.connect(self.editor.copy)
        self.edit_toolbar.addAction(self.copy_action)
        self.edit_menu.addAction(self.copy_action)

        self.paste_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                'Edit-paste.svg')), "Paste", self)
        self.paste_action.setStatusTip("Paste from clipboard")
        self.paste_action.triggered.connect(self.editor.paste)
        self.edit_toolbar.addAction(self.paste_action)
        self.edit_menu.addAction(self.paste_action)

        self.select_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                 'Edit-select-all.svg')), "Select all", self)
        self.select_action.setStatusTip("Select all text")
        self.select_action.triggered.connect(self.editor.selectAll)
        self.edit_menu.addAction(self.select_action)

        self.edit_menu.addSeparator()

        self.wrap_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Go-next.svg')), "Wrap text to window", self)
        self.wrap_action.setStatusTip("Toggle wrap text to window")
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)
        self.wrap_action.triggered.connect(self.edit_toggle_wrap)
        self.edit_menu.addAction(self.wrap_action)
        self.update_title()
        self.show()

    def file_open(self):
        file_path = get_open_filename(self, "Open file", MSS_CONFIG_PATH, "Text documents (*.json)")
        if file_path is not None:
            file_name = fs.path.basename(file_path)
            with fs.open_fs(fs.path.dirname(file_path)) as file_dir:
                self.file_content = file_dir.readtext(file_name)
                self.last_saved = self.file_content
                self.editor.setPlainText(self.file_content)
                self.update_title()

    def check_modified(self):
        if self.last_saved != self.editor.toPlainText():
            return True
        return False

    def check_json(self):
        try:
            json.loads(self.editor.toPlainText())
        except json.JSONDecodeError as ex:
            QtWidgets.QMessageBox.warning(
                self, self.tr("Mission Support System"),
                self.tr("This JSON file contains Syntax errors and will not be saved.\n") + str(ex))
            return False
        return True

    def file_save_and_quit(self):
        if self.check_modified():
            if self.check_json():
                self._save_to_path(self.path)
                ret = QtWidgets.QMessageBox.warning(
                    self, self.tr("Mission Support System"),
                    self.tr("Do you want to restart the application?\n"
                            "(This is necessary to apply changes)"),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No)
                if ret == QtWidgets.QMessageBox.Yes:
                    self.restartApplication.emit()
        self.close()

    def file_saveas(self):
        if self.check_json():
            default_filename = constants.CACHED_CONFIG_FILE
            if default_filename is None:
                default_filename = MSS_SETTINGS
            path = get_save_filename(
                self, "Save file", default_filename, "Text documents (*.json)")
            # If dialog is cancelled, will return ''
            if path:
                self._save_to_path(path)

    def _save_to_path(self, filename):
        logging.debug("save config file to: %s", filename)
        text = self.editor.toPlainText()
        self.last_saved = text
        dir_name, file_name = fs.path.split(filename)
        with fs.open_fs(dir_name) as _fs:
            _fs.writetext(file_name, text)
        self.update_title()
        constants.CACHED_CONFIG_FILE = self.path

    def file_print(self):
        dlg = QtPrintSupport.QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle(f"{fs.path.basename(self.path)} - Config-Settings" if self.path else "Untitled")

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(1 if self.editor.lineWrapMode() == 0 else 0)

    def closeEvent(self, event):
        if self.check_modified() and self.check_json():
            ret = QtWidgets.QMessageBox.question(
                self, self.tr("Mission Support System"),
                self.tr("Save Changes to default mss_settings.json?\n"
                        "You need to restart the gui for changes to take effect."),
                QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if ret == QtWidgets.QMessageBox.Yes:
                self.file_save_and_quit()

        self.viewCloses.emit()
        event.accept()
