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
import fs
# import logging
import json

# from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import ui_configuration_editor_window as ui_conf
from PyQt5 import QtWidgets, QtCore
from mslib.msui import constants
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

        # checking if parent is accepted (works only for indexes with depth 2)
        src_model = self.sourceModel()
        index = src_model.index(source_row, self.filterKeyColumn(), source_parent)
        has_parent = src_model.itemFromIndex(index).parent()
        if has_parent:
            parent_index = self.mapFromSource(has_parent.index())
            return super(JsonSortFilterProxyModel, self).filterAcceptsRow(has_parent.row(), parent_index)

        return accepted


class ConfigurationEditorWindow(QtWidgets.QMainWindow, ui_conf.Ui_ConfigurationEditorWindow):

    # Dictionary options with fixed key/value pairs
    fixed_dict_options = ["layout", "wms_prefetch", "topview", "sideview", "linearview"]

    # Dictionary options with predefined structure
    dict_option_structure = {
        "predefined_map_sections": {
            "new_map_section": {
                "CRS": "crs_value",
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
            "https": "https://proxy.com",
        },
    }

    # List options with predefined structure
    list_option_structure = {
        "default_WMS": ["https://wms-server-url.com"],
        "default_VSEC_WMS": ["https://vsec-wms-server-url.com"],
        "default_LSEC_WMS": ["https://lsec-wms-server-url.com"],
        "default_MSCOLAB": ["https://mscolab-server-url.com"],
        "new_flighttrack_template": ["new-location"],
        "gravatar_ids": ["example@email.com"],
        "WMS_preload": ["https://wms-preload-url.com"],
    }

    # Fixed key/value pair options
    key_value_options = [
        'filepicker_default',
        'mss_dir',
        'data_dir',
        'num_labels',
        'num_interpolation_points',
        'new_flighttrack_flightlevel',
        'MSCOLAB_mailid',
        'MSCOLAB_password',
        'mscolab_server_url',
        'wms_cache',
        'wms_cache_max_size_bytes',
        'wms_cache_max_age_seconds',
        'WMS_request_timeout',
    ]

    def __init__(self, parent=None):
        super(ConfigurationEditorWindow, self).__init__(parent)
        self.setupUi(self)

        self.default_options = dict(mss_default.__dict__)
        for key in ["__module__", "__doc__", "__dict__", "__weakref__", "config_descriptions"]:
            del self.default_options[key]
        self.options = copy.deepcopy(self.default_options)

        # Load mss_settings.json (if already exists), change \\ to / so fs can work with it
        self.path = constants.CACHED_CONFIG_FILE
        json_file_data = {}
        if self.path is not None:
            self.path = self.path.replace("\\", "/")
            dir_name, file_name = fs.path.split(self.path)
            with fs.open_fs(dir_name) as _fs:
                if _fs.exists(file_name):
                    file_content = _fs.readtext(file_name)
                    json_file_data = json.loads(file_content)
        else:
            self.path = MSS_SETTINGS
            self.path = self.path.replace("\\", "/")
        if json_file_data:
            self.merge_data(json_file_data)
        # print(json.dumps(self.options, indent=4))

        self.optCb.addItem("All")
        for option in sorted(self.options.keys(), key=str.lower):
            self.optCb.addItem(option)

        self.moveUpTb.hide()
        self.moveDownTb.hide()
        self.moveUpTb.setAutoRaise(True)
        self.moveUpTb.setArrowType(QtCore.Qt.UpArrow)
        self.moveUpTb.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.moveDownTb.setAutoRaise(True)
        self.moveDownTb.setArrowType(QtCore.Qt.DownArrow)
        self.moveDownTb.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setText("Save and Restart")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Open).setText("Import")
        self.addOptBtn.clicked.connect(self.add_option_handler)
        self.removeOptBtn.clicked.connect(self.remove_option_handler)
        self.optCb.currentIndexChanged.connect(self.selection_change)

        # Create view and place in widget
        self.view = JsonView()
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.jsonWidget.setLayout(QtWidgets.QVBoxLayout())
        self.jsonWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.jsonWidget.layout().addWidget(self.view)

        # Create proxy model for filtering
        self.proxy_model = JsonSortFilterProxyModel()
        self.json_model = JsonModel(data=self.options, editable_keys=True, editable_values=True)
        self.json_model.setHorizontalHeaderLabels(['Option', 'Value'])

        self.set_noneditable_items(QtCore.QModelIndex())

        # Set view model
        self.proxy_model.setSourceModel(self.json_model)
        self.view.setModel(self.proxy_model)

        # Setting proxy model and view attributes
        self.proxy_model.setFilterKeyColumn(0)
        self.view.setAlternatingRowColors(True)
        self.view.setColumnWidth(0, self.view.width() // 2)

    def set_noneditable_items(self, parent):
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            item.setEditable(False)
            if item.text() in self.fixed_dict_options:
                self.set_noneditable_items(index)
            # if item.text() in mss_default.config_descriptions:
            #     item.setData(mss_default.config_descriptions[item.text()], QtCore.Qt.ToolTipRole)

    def compare_data(self, default, user_data):
        # If data is neither list not dict type, compare individual type
        if not isinstance(default, dict) and not isinstance(default, list):
            if isinstance(default, float) and isinstance(user_data, int):
                user_data = float(default)
            if isinstance(match_type(default), type(match_type(user_data))):
                return user_data, True
            else:
                return default, False

        data = copy.deepcopy(default)
        trues = []
        # If data is list type, compare all values in list
        if isinstance(default, list):
            if isinstance(user_data, list):
                if len(default) == len(user_data):
                    for i in range(len(default)):
                        data[i], match = self.compare_data(default[i], user_data[i])
                        trues.append(match)
                else:
                    return default, False
            else:
                return default, False

        # If data is dict type, goes through the dict and update
        elif isinstance(default, dict):
            for key in default:
                if key in user_data:
                    data[key], match = self.compare_data(default[key], user_data[key])
                    trues.append(match)
                else:
                    trues.append(False)

        return data, all(trues)

    def merge_data(self, json_file_data):
        # Check if dictionary options with fixed key/value pairs match data types from default
        for key in self.fixed_dict_options:
            if key in json_file_data:
                self.options[key] = self.compare_data(self.options[key], json_file_data[key])[0]

        # Check if dictionary options with predefined structure match data types from default
        dos = copy.deepcopy(self.dict_option_structure)
        # adding plugin structure : ["extension", "module", "function"] to recognize
        # user plugins that don't have optional filepicker option set
        dos["import_plugins"]["plugin-name-a"] = dos["import_plugins"]["plugin-name"][:3]
        dos["export_plugins"]["plugin-name-a"] = dos["export_plugins"]["plugin-name"][:3]
        for key in dos:
            if key in json_file_data:
                temp_data = {}
                for option_key in json_file_data[key]:
                    for dos_key_key in dos[key]:
                        if isinstance(match_type(option_key), type(match_type(dos_key_key))):
                            data, match = self.compare_data(dos[key][dos_key_key], json_file_data[key][option_key])
                            if match:
                                temp_data[option_key] = json_file_data[key][option_key]
                                break
                if temp_data != {}:
                    self.options[key] = temp_data

        # add filepicker default to import plugins if missing
        for plugin in self.options["import_plugins"]:
            if len(self.options["import_plugins"][plugin]) == 3:
                self.options["import_plugins"][plugin].append("default")

        # add filepicker default to export plugins if missing
        for plugin in self.options["export_plugins"]:
            if len(self.options["export_plugins"][plugin]) == 3:
                self.options["export_plugins"][plugin].append("default")

        # Check if list options with predefined structure match data types from default
        los = copy.deepcopy(self.list_option_structure)
        for key in los:
            if key in json_file_data:
                temp_data = []
                for i in range(len(json_file_data[key])):
                    for los_key_item in los[key]:
                        data, match = self.compare_data(los_key_item, json_file_data[key][i])
                        if match:
                            temp_data.append(data)
                            break
                if temp_data != []:
                    self.options[key] = temp_data

        # Check if options with fixed key/value pair structure match data types from default
        for key in self.key_value_options:
            if key in json_file_data:
                data, match = self.compare_data(self.default_options[key], json_file_data[key])
                if match:
                    self.options[key] = data

    def show_all(self):
        # self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setFilterRegExp("")

    def selection_change(self, index):
        if self.optCb.currentText() == "All":
            self.show_all()
            return
        self.proxy_model.setFilterRegExp(QtCore.QRegExp(f"^{self.optCb.currentText()}$"))
        self.view.expandAll()

    def add_option_handler(self):
        filter_exp = self.proxy_model.filterRegExp().pattern()
        if filter_exp == "":
            self.statusbar.showMessage("Please select an option to add")
            return

        filter_exp = filter_exp[1:-1]
        parent = QtCore.QModelIndex()
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            if item.text() == filter_exp:
                if isinstance(item.data(), DictType):
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
                    self.view.scrollToBottom()
                elif isinstance(item.data(), ListType):
                    if filter_exp in self.list_option_structure:
                        json_data = self.list_option_structure[filter_exp]
                    else:
                        self.statusbar.showMessage("Sorry, could not recognize config option.")
                        return
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                    # increase row count in view
                    rows = self.json_model.rowCount(index) - 1
                    new_item = self.json_model.itemFromIndex(self.json_model.index(rows, 0, index))
                    new_item.setData(rows, QtCore.Qt.DisplayRole)
                    self.statusbar.showMessage("")
                    self.view.expandAll()
                    self.view.scrollToBottom()
                else:
                    self.statusbar.showMessage(
                        "Option already exists. Please change value to your preference or restore to default.")
                break

    def remove_option_handler(self):
        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0:
            self.statusbar.showMessage("Please select an option to remove")
            return

        non_removable = []
        removable_indexes = {}
        for index in selection:
            if not index.parent().isValid():
                # cannot remove root item
                non_removable.append(index)
                continue

            # find penultimate option key
            while index.parent().parent().isValid():
                index = index.parent()
            root = index.parent()
            # enter only if option not in fixed dictionary options
            if root.data() not in self.fixed_dict_options + self.key_value_options:
                if root in removable_indexes:
                    removable_indexes[root].add(index.row())
                else:
                    removable_indexes[root] = set([index.row()])
            else:
                non_removable.append(index)

        data = self.json_model.serialize()
        removable_data = {}
        for index in removable_indexes:
            index_data = index.data()
            if isinstance(data[index_data], list):
                removable_data[index_data] = [data[index_data][r] for r in removable_indexes[index]]
            else:
                removable_data[index_data] = {}
                for r in removable_indexes[index]:
                    child_index = self.proxy_model.index(r, 0, index)
                    child_data = child_index.data()
                    removable_data[index_data][child_data] = data[index_data][child_data]

        if removable_indexes == {} and non_removable != []:
            self.statusbar.showMessage("Default options are not removable.")
            return

        self.view.selectionModel().clearSelection()
        for index in removable_indexes:
            rows = sorted(list(removable_indexes[index]))
            for count, row in enumerate(rows):
                row = row - count
                self.proxy_model.removeRow(row, parent=index)

            # fix row number in list type options
            source_index = self.proxy_model.mapToSource(index)
            source_item = self.json_model.itemFromIndex(source_index)
            if isinstance(source_item.data(QtCore.Qt.UserRole + 1), ListType):
                for r in range(self.json_model.rowCount(source_index)):
                    child_index = self.json_model.index(r, 0, source_index)
                    item = self.json_model.itemFromIndex(child_index)
                    item.setData(r, QtCore.Qt.DisplayRole)

        # print(json.dumps(self.json_model.serialize(), indent=4))

        # dialog_box = QtWidgets.QMessageBox.question(self, "Invalid options detected", "The following options were invalid\npredefined_map_sections:new_location", QtWidgets.QMessageBox.Ok)
        # if dialog_box == QtWidgets.QMessageBox.Ok:
        #     pass

