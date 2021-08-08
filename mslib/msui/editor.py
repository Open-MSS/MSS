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
import collections.abc
import copy
import fs
import logging
import json

# from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import ui_configuration_editor_window as ui_conf
from PyQt5 import QtWidgets, QtCore, QtGui
from mslib.msui import constants
from mslib.msui.constants import MSS_SETTINGS
# from mslib.msui.icons import icons
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default

from mslib.support.qt_json_view import delegate
from mslib.support.qt_json_view.view import JsonView
from mslib.support.qt_json_view.model import JsonModel
from mslib.support.qt_json_view.datatypes import match_type, DataType, TypeRole, ListType, DictType


# system default options as dictionary
default_options = dict(mss_default.__dict__)
for key in ["__module__", "__doc__", "__dict__", "__weakref__", "config_descriptions"]:
    del default_options[key]

# Dictionary options with fixed key/value pairs
fixed_dict_options = ["layout", "wms_prefetch", "topview", "sideview", "linearview"]

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
        "http://www.your-mscolab-server.de": ["yourusername", "yourpassword"],
    },
    "WMS_login": {
        "http://www.your-wms-server.de": ["yourusername", "yourpassword"],
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


class JsonDelegate(delegate.JsonDelegate):

    def paint(self, painter, option, index):
        """Use method from the data type or fall back to the default."""
        if index.column() == 0:
            return super(JsonDelegate, self).paint(painter, option, index)

        if index.data() is not None:
            proxy_model = index.model()
            parents = [proxy_model.index(index.row(), 0, index.parent())]
            while parents[0].parent().isValid():
                parents.insert(0, parents[0].parent())
            if parents[0].data() in fixed_dict_options:
                default_data = default_options[parents[0].data()]
                for parent in parents[1:]:
                    parent_data = parent.data()
                    if isinstance(default_data, list):
                        parent_data = int(parent.data())
                    default_data = default_data[parent_data]
                if default_data != index.data():
                    option.font.setWeight(QtGui.QFont.Bold)
            elif parents[0].data() in key_value_options:
                if default_options[parents[0].data()] != index.data():
                    option.font.setWeight(QtGui.QFont.Bold)

        type_ = index.data(TypeRole)
        if isinstance(type_, DataType):
            try:
                super(JsonDelegate, self).paint(painter, option, index)
                return type_.paint(painter, option, index)
            except NotImplementedError:
                pass
        return super(JsonDelegate, self).paint(painter, option, index)


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
    name = "MSSEditor"
    identifier = None

    # restartApplication = QtCore.pyqtSignal(name="restartApplication")

    def __init__(self, parent=None):
        super(ConfigurationEditorWindow, self).__init__(parent)
        self.setupUi(self)

        self.options = copy.deepcopy(default_options)

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

        # Create view and place in widget
        self.view = JsonView()
        self.view.setItemDelegate(JsonDelegate())
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

        # Buttonbox signals
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setText("Save and Restart")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Open).setText("Import")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Save).clicked.connect(self.save_and_restart)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Open).clicked.connect(self.import_config)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancel_handler)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)

        # Option signals
        self.addOptBtn.clicked.connect(self.add_option_handler)
        self.removeOptBtn.clicked.connect(self.remove_option_handler)
        self.optCb.currentIndexChanged.connect(self.selection_change)
        self.moveUpTb.clicked.connect(lambda: self.move_option(move=1))
        self.moveDownTb.clicked.connect(lambda: self.move_option(move=-1))

        self.moveUpTb.hide()
        self.moveDownTb.hide()
        self.moveUpTb.setAutoRaise(True)
        self.moveUpTb.setArrowType(QtCore.Qt.UpArrow)
        self.moveUpTb.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.moveDownTb.setAutoRaise(True)
        self.moveDownTb.setArrowType(QtCore.Qt.DownArrow)
        self.moveDownTb.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.moveUpTb.setEnabled(False)
        self.moveDownTb.setEnabled(False)
        self.addOptBtn.setEnabled(False)
        self.removeOptBtn.setEnabled(False)
        self.view.selectionModel().selectionChanged.connect(self.tree_selection_changed)

    def get_root_index(self, index, parents=False):
        parent_list = []
        while index.parent().isValid():
            index = index.parent()
            parent_list.append(index)
        parent_list.reverse()
        if parents:
            return index, parent_list
        return index

    def set_noneditable_items(self, parent):
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            item.setEditable(False)
            if item.text() in fixed_dict_options:
                self.set_noneditable_items(index)
            if item.text() in mss_default.config_descriptions:
                item.setData(mss_default.config_descriptions[item.text()], QtCore.Qt.ToolTipRole)

    def tree_selection_changed(self, selected, deselected):
        selection = self.view.selectionModel().selectedRows()
        # if no selection
        add, remove, move = [False] * 3
        if len(selection) == 1:
            index = selection[0]
            if not index.parent().isValid():
                move = True
            index = self.get_root_index(index)
            if index.data() not in fixed_dict_options + key_value_options:
                add, move = True, True
        if len(selection) >= 1:
            for index in selection:
                index = self.get_root_index(index)
                if index.data() not in fixed_dict_options + key_value_options and self.proxy_model.rowCount(index) > 0:
                    remove = True
                    break
        self.addOptBtn.setEnabled(add)
        self.removeOptBtn.setEnabled(remove)
        self.moveUpTb.setEnabled(move)
        self.moveDownTb.setEnabled(move)

    def move_option(self, move=None):
        if move not in [1, -1]:
            logging.error("Invalid move value passed to move_option method")
            return
        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0:
            logging.debug("No options selected when trying to move")
            self.statusbar.showMessage("Please select an option to move")
            return
        elif len(selection) > 1:
            logging.debug("Multiple options selected when trying to move")
            self.statusbar.showMessage("Please select a single option to move")
            return

        index = selection[0]
        if not index.parent().isValid():
            if index.data() not in fixed_dict_options + key_value_options:
                self.proxy_model.moveRow(index.parent(), index.row(), index.parent(), index.row() + move)

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
        for key in fixed_dict_options:
            if key in json_file_data:
                self.options[key] = self.compare_data(self.options[key], json_file_data[key])[0]

        # Check if dictionary options with predefined structure match data types from default
        dos = copy.deepcopy(dict_option_structure)
        # adding plugin structure : ["extension", "module", "function"] to recognize
        # user plugins that don't have optional filepicker option set
        dos["import_plugins"]["plugin-name-a"] = dos["import_plugins"]["plugin-name"][:3]
        dos["export_plugins"]["plugin-name-a"] = dos["export_plugins"]["plugin-name"][:3]
        for key in dos:
            if key in json_file_data:
                temp_data = {}
                for option_key in json_file_data[key]:
                    for dos_key_key in dos[key]:
                        # if isinstance(match_type(option_key), type(match_type(dos_key_key))):
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
        los = copy.deepcopy(list_option_structure)
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
        for key in key_value_options:
            if key in json_file_data:
                data, match = self.compare_data(default_options[key], json_file_data[key])
                if match:
                    self.options[key] = data
        logging.info("Merged default and user settings")

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
        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0 or len(selection) > 1:
            logging.debug("zero or multiple selections while trying to add new value")
            self.statusbar.showMessage("Please select one option to add new value")
            return

        selected_index = self.get_root_index(selection[0])
        option = selected_index.data()
        parent = QtCore.QModelIndex()
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            if index.data() == option:
                if option in fixed_dict_options + key_value_options:
                    self.statusbar.showMessage(
                        "Option already exists. Please change value to your preference or restore to default.")
                    return
                elif option in dict_option_structure:
                    self.statusbar.showMessage("")
                    json_data = dict_option_structure[option]
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                elif option in list_option_structure:
                    self.statusbar.showMessage("")
                    json_data = list_option_structure[option]
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                    # increase row count in view
                    rows = self.json_model.rowCount(index) - 1
                    new_item = self.json_model.itemFromIndex(self.json_model.index(rows, 0, index))
                    new_item.setData(rows, QtCore.Qt.DisplayRole)
                # expand root item
                proxy_index = self.proxy_model.mapFromSource(index)
                self.view.expand(proxy_index)
                # scroll to, expand and select new item
                rows = self.json_model.rowCount(index) - 1
                new_index = self.json_model.index(rows, 0, index)
                proxy_index = self.proxy_model.mapFromSource(new_index)
                self.view.expand(proxy_index)
                self.view.scrollTo(proxy_index)
                self.view.selectionModel().select(
                    proxy_index, QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows)
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
                if index.data() not in fixed_dict_options + key_value_options:
                    removable_indexes[index] = set(range(self.proxy_model.rowCount(index)))
                else:
                    # cannot remove root item
                    non_removable.append(index)
            else:
                # find penultimate option key
                while index.parent().parent().isValid():
                    index = index.parent()
                root = index.parent()
                # enter only if root option not in fixed dictionary / key value options
                if root.data() not in fixed_dict_options + key_value_options:
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

        # self.error_dialog = QtWidgets.QErrorMessage()
        # self.error_dialog.showMessage('Path can\'t be empty')
        # dialog_box = QtWidgets.QMessageBox.question(self, "Invalid options detected",
        # "The following options were invalid\npredefined_map_sections:new_location", QtWidgets.QMessageBox.Ok)
        # if dialog_box == QtWidgets.QMessageBox.Ok:
        #     pass

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

    def restore_defaults(self):
        def update(data, option, value):
            for k, v in data.items():
                if k == option[0]:
                    if option[1] is None:
                        data[k] = value
                    else:
                        data[k][option[1]] = value
                    break
                if isinstance(v, collections.abc.Mapping):
                    data[k] = update(data.get(k, {}), option, value)
            return data

        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0:
            logging.debug("zero selections while trying to restore defaults")
            self.statusbar.showMessage("Please select one/more options to restore defaults")
            return

        model_data = self.json_model.serialize()
        selected_indexes = set()
        for index in selection:
            root_index, parent_list = self.get_root_index(index, parents=True)
            added = False
            data = model_data
            for parent in parent_list + [index]:
                data = data[parent.data()]
                if isinstance(data, list):
                    added = True
                    selected_indexes.add(parent)
                    break
            if not added:
                selected_indexes.add(index)

        for index in selected_indexes:
            parent = QtCore.QModelIndex()
            if not index.parent().isValid() and index.data() in key_value_options:
                value_index = self.json_model.index(index.row(), 1, parent)
                value_item = self.json_model.itemFromIndex(value_index)
                value_item.setData(default_options[index.data()], QtCore.Qt.DisplayRole)
                continue

            root_index, parent_list = self.get_root_index(index, parents=True)
            option = root_index.data()
            model_data = self.json_model.serialize()
            if option in fixed_dict_options:
                if index == root_index:
                    json_data = default_options[option]
                else:
                    list_index = None
                    key = None
                    value = copy.deepcopy(default_options)
                    for parent in parent_list + [index]:
                        parent_data = parent.data()
                        if isinstance(value, list):
                            break
                            # parent_data = int(parent.data())
                            # list_index = parent_data
                        key = parent_data
                        value = value[parent_data]
                    json_data = update(model_data[option], (key, list_index), value)
                    # key = index.data() if list_index is None else index.parent().data()
                    # key = index.parent().data() if index.parent().parent().isValid() else index.data()
                    # if index.parent().isValid():
                    #     key = index.data() if list_index is None else index.parent().data()
                    #     json_data = update(model_data[option], (key, list_index), value)
                    # else:
                    #     key = index.data()
                    #     json_data = update(model_data, (key, list_index), value)[option]
            else:
                json_data = default_options[option]
            # print(json_data)
            # if json_data == default_options[option]:
            #     continue
            # remove all rows
            for row in range(self.proxy_model.rowCount(root_index)):
                self.proxy_model.removeRow(0, parent=root_index)
            # add default values
            source_index = self.proxy_model.mapToSource(root_index)
            source_item = self.json_model.itemFromIndex(source_index)
            type_ = match_type(json_data)
            type_.next(model=self.json_model, data=json_data, parent=source_item)
        self.view.clearSelection()

    def save_and_restart(self):
        json_data = self.json_model.serialize()
        save_data = copy.deepcopy(json_data)

        # saving only diff from default
        for key in fixed_dict_options:
            if isinstance(json_data[key], dict):
                for key_key in json_data[key]:
                    if json_data[key][key_key] == default_options[key][key_key]:
                        del save_data[key][key_key]
            else:
                if json_data[key] == default_options[key]:
                    del save_data[key]
            if save_data[key] == {}:
                del save_data[key]

        for key in key_value_options + list(dict_option_structure) + list(list_option_structure):
            if json_data[key] == default_options[key]:
                del save_data[key]

#         print(json.dumps(save_data, indent=4))

        dir_name, file_name = fs.path.split(self.path)
        with fs.open_fs(dir_name) as _fs:
            _fs.writetext(file_name, json.dumps(save_data, indent=4))

    def import_config(self):
        pass

    def cancel_handler(self):
        pass
