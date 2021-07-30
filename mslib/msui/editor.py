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
import copy
# import fs
# import logging
import json

# from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import ui_configuration_editor_window as ui_conf
from PyQt5 import QtWidgets, QtCore
# from mslib.msui import constants
from mslib.msui.constants import MSS_SETTINGS
# from mslib.msui.icons import icons
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default

from mslib.support.qt_json_view.view import JsonView
from mslib.support.qt_json_view.model import JsonModel
from mslib.support.qt_json_view.datatypes import match_type, ListType, DictType


class JsonSortFilterProxyModel(QtCore.QSortFilterProxyModel):

    def filterAcceptsRow(self, source_row, source_parent):
        # check if an item is currently accepted
        accepted = super(JsonSortFilterProxyModel, self).filterAcceptsRow(source_row, source_parent)

        if accepted:
            return True

        # checking if parent is accepted (works only for 2 levels)
        src_model = self.sourceModel()
        index = src_model.index(source_row, self.filterKeyColumn(), source_parent)
        has_parent = src_model.itemFromIndex(index).parent()
        if has_parent:
            parent_index = self.mapFromSource(has_parent.index())
            return super(JsonSortFilterProxyModel, self).filterAcceptsRow(has_parent.row(), parent_index)

        return accepted


class ConfigurationEditorWindow(QtWidgets.QMainWindow, ui_conf.Ui_ConfigurationEditorWindow):

    dict_option_structure = {
        "predefined_map_sections": {
            "new_map_section": {
                "CRS": "EPSG:",
                "map": {
                    "llcrnrlon": 0.0,
                    "llcrnrlat": 0.0,
                    "urcrnrlon": 0.0,
                    "urcrnrlat": 0.0,
                },
            }
        },
        "MSC_login": {
            "https://mscolab-server-url.com": ["username", "password"],
        },
        "WMS_login": {
            "https://wms-server-url.com": ["username", "password"],
        },
        "locations": {
            "new-location": [0.0, 0.0],
        },
        "export_plugins": {
            "plugin-name": ["extension", "module", "function", "default"],
        },
        "import_plugins": {
            "plugin-name": ["extension", "module", "function", "default"],
        },
        "proxies": {
            "https": "proxylink",
        },
    }

    fixed_dict_options = ["layout", "wms_prefetch", "topview", "sideview", "linearview"]

    list_option_structure = {
        "default_WMS": ["https://wms-server-url.com"],
        "default_VSEC_WMS": ["https://vsec-wms-server-url.com"],
        "default_LSEC_WMS": ["https://lsec-wms-server-url.com"],
        "default_MSCOLAB": ["https://mscolab-server-url.com"],
        "new_flighttrack_template": ["new-location"],
        "gravatar_ids": ["example@email.com"],
        "WMS_preload": [],
    }

    def __init__(self, parent=None):
        super(ConfigurationEditorWindow, self).__init__(parent)
        self.setupUi(self)

        self.default = dict(mss_default.__dict__)
        for key in ["__module__", "__doc__", "__dict__", "__weakref__", "config_descriptions"]:
            del self.default[key]
        self.options = copy.deepcopy(self.default)

        # Load mss_settings.json (if already exists), change \\ to / so fs can work with it
        # self.path = constants.CACHED_CONFIG_FILE
        # if self.path is not None:
        #     self.path = self.path.replace("\\", "/")
        #     dir_name, file_name = fs.path.split(self.path)
        #     with fs.open_fs(dir_name) as _fs:
        #         if _fs.exists(file_name):
        #             json_file_data = json.load(_fs)
        # else:
        self.path = MSS_SETTINGS
        self.path = self.path.replace("\\", "/")
        with open(self.path, "r") as file_obj:
            json_file_data = json.loads(file_obj.read())
        self.options.update(json_file_data)
        # for key in list(self.options.keys()):
        #     if self.options[key] == [] or self.options[key] == {}:
        #         del self.options[key]
        # print(json.dumps(self.dict_data, indent = 1))

        self.optCb.addItem("All")
        for option in sorted(self.options.keys(), key=str.lower):
            self.optCb.addItem(option)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setText("Save and Restart")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Open).setText("Import")
        self.addOptBtn.clicked.connect(self.add_option)
        self.removeOptBtn.clicked.connect(self.remove_option)
        self.optCb.currentIndexChanged.connect(self.selection_change)

        # Create view and place in widget
        self.view = JsonView()
        self.jsonWidget.setLayout(QtWidgets.QVBoxLayout())
        self.jsonWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.jsonWidget.layout().addWidget(self.view)

        # Create proxy model for filtering
        self.proxy_model = JsonSortFilterProxyModel()
        self.json_model = JsonModel(data=self.options, editable_keys=True, editable_values=True)
        self.json_model.setHorizontalHeaderLabels(['Option', 'Value'])

        # set tooltip
        # parent = QtCore.QModelIndex()
        # for r in range(self.json_model.rowCount(parent)):
        #     index = self.json_model.index(r, 0, parent)
        #     item = self.json_model.itemFromIndex(index)
        #     if item.text() in mss_default.config_descriptions:
        #         item.setData(mss_default.config_descriptions[item.text()], QtCore.Qt.ToolTipRole)

        # Set view model
        self.proxy_model.setSourceModel(self.json_model)
        self.view.setModel(self.proxy_model)

        # Setting proxy model and view attributes
        self.proxy_model.setFilterKeyColumn(0)
        self.view.setAlternatingRowColors(True)
        self.view.header().setSectionResizeMode(1)
        # self.view.header().setSectionResizeMode(0)

    def show_all(self):
        # self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setFilterRegExp("")
        # self.view.expandAll()
        # print(json.dumps(self.json_model.serialize(), indent = 1))

    def selection_change(self, index):
        # self.proxy_model.setFilterKeyColumn(-1)
        if self.optCb.currentText() == "All":
            self.show_all()
            return
        self.proxy_model.setFilterRegExp(self.optCb.currentText())
        self.view.expandAll()

    def add_option(self):
        filter_exp = self.proxy_model.filterRegExp().pattern()
        if filter_exp == "":
            self.statusbar.showMessage("Please select an option to add or remove.")
            return

        parent = QtCore.QModelIndex()
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            if item.text() == filter_exp:
                if isinstance(item.data(), DictType):
                    # json_data = self.json_model.serialize()[filter_exp]
                    # key, value = next(iter(json_data.items()))
                    # json_data = {key: value}
                    if filter_exp in self.dict_option_structure:
                        json_data = self.dict_option_structure[filter_exp]
                    elif filter_exp in self.fixed_dict_options:
                        self.statusbar.showMessage(
                            "Option already exists. Please change value to your preference or restore to default.")
                        return
                    else:
                        self.statusbar.showMessage("Sorry, could not recognize config option.")
                        return
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                    self.statusbar.showMessage("")
                    self.view.expandAll()
                elif isinstance(item.data(), ListType):
                    if filter_exp in self.list_option_structure:
                        json_data = self.list_option_structure[filter_exp]
                    else:
                        self.statusbar.showMessage("Sorry, could not recognize config option.")
                        return
                    # json_data = self.json_model.serialize()[filter_exp]
                    # json_data = [json_data[0]]
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                    # increase row count in view
                    rows = self.json_model.rowCount(index) - 1
                    new_item = self.json_model.itemFromIndex(self.json_model.index(rows, 0, index))
                    new_item.setData(rows, QtCore.Qt.DisplayRole)
                    # new_item = self.json_model.itemFromIndex(self.json_model.index(rows, 1, index))
                    # new_item.setData(None, QtCore.Qt.DisplayRole)
                    self.statusbar.showMessage("")
                    self.view.expandAll()
                else:
                    self.statusbar.showMessage(
                        "Option already exists. Please change value to your preference or restore to default.")
                break

    def remove_option(self):
        pass
