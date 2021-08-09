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

from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import ui_configuration_editor_window as ui_conf
from PyQt5 import QtWidgets, QtCore, QtGui
# from mslib.msui import constants
from mslib.msui.constants import MSS_SETTINGS
# from mslib.msui.icons import icons
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default

from mslib.support.qt_json_view import delegate
from mslib.support.qt_json_view.view import JsonView
from mslib.support.qt_json_view.model import JsonModel
from mslib.support.qt_json_view.datatypes import match_type, DataType, TypeRole, ListType


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
            model = index.model()
            parents = [model.index(index.row(), 0, index.parent())]
            while parents[0].parent().isValid():
                parents.insert(0, parents[0].parent())
            root_option = parents[0].data()
            if root_option in fixed_dict_options:
                default_data = default_options[root_option]
                for parent in parents[1:]:
                    parent_data = parent.data()
                    if isinstance(default_data, list):
                        parent_data = int(parent.data())
                    default_data = default_data[parent_data]
                if default_data != index.data():
                    option.font.setWeight(QtGui.QFont.Bold)
            elif root_option in key_value_options:
                if default_options[root_option] != index.data():
                    option.font.setWeight(QtGui.QFont.Bold)
            elif root_option in dict_option_structure or root_option in list_option_structure:
                if isinstance(model, QtCore.QAbstractProxyModel):
                    model = model.sourceModel()
                source_data = model.serialize()
                if source_data[root_option] != default_options[root_option]:
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

    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    restartApplication = QtCore.pyqtSignal(name="restartApplication")

    def __init__(self, parent=None):
        super(ConfigurationEditorWindow, self).__init__(parent)
        self.setupUi(self)

        # Load mss_settings.json (if already exists), change \\ to / so fs can work with it
        self.path = MSS_SETTINGS
        json_file_data = {}
        self.path = self.path.replace("\\", "/")
        dir_name, file_name = fs.path.split(self.path)
        with fs.open_fs(dir_name) as _fs:
            if _fs.exists(file_name):
                file_content = _fs.readtext(file_name)
                json_file_data = json.loads(file_content)
        if json_file_data:
            options = self.merge_data(copy.deepcopy(default_options), json_file_data)
            logging.info("Merged default and user settings")
        else:
            options = copy.deepcopy(default_options)
            logging.info("No user settings found, using default settings")
        self.last_saved = copy.deepcopy(options)
        # print(json.dumps(options, indent=4))

        self.optCb.addItem("All")
        for option in sorted(options.keys(), key=str.lower):
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
        self.json_model = JsonModel(data=options, editable_keys=True, editable_values=True)
        self.json_model.setHorizontalHeaderLabels(['Option', 'Value'])

        # set tooltip and make keys non-editable
        self.set_noneditable_items(QtCore.QModelIndex())

        # Set view model
        self.proxy_model.setSourceModel(self.json_model)
        self.view.setModel(self.proxy_model)

        # Setting proxy model and view attributes
        self.proxy_model.setFilterKeyColumn(0)
        self.view.setAlternatingRowColors(True)
        self.view.setColumnWidth(0, self.view.width() // 2)

        # Connecting signals
        self.addOptBtn.clicked.connect(self.add_option_handler)
        self.removeOptBtn.clicked.connect(self.remove_option_handler)
        self.optCb.currentIndexChanged.connect(self.selection_change)
        self.moveUpTb.clicked.connect(lambda: self.move_option(move=1))
        self.moveDownTb.clicked.connect(lambda: self.move_option(move=-1))
        self.restoreDefaultsBtn.clicked.connect(self.restore_defaults)
        self.importBtn.clicked.connect(self.import_config)
        self.exportBtn.clicked.connect(self.export_config)
        self.saveBtn.clicked.connect(self.save_config)
        self.cancelBtn.clicked.connect(lambda: self.close())
        self.view.selectionModel().selectionChanged.connect(self.tree_selection_changed)

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
        self.restoreDefaultsBtn.setEnabled(False)

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
        add, remove, restore_defaults, move = [False] * 4
        if len(selection) == 1:
            index = selection[0]
            if not index.parent().isValid():
                move = True
            index = self.get_root_index(index)
            if index.data() not in fixed_dict_options + key_value_options:
                add, move = True, True
        if len(selection) >= 1:
            restore_defaults = True
            for index in selection:
                index = self.get_root_index(index)
                if index.data() not in fixed_dict_options + key_value_options and self.proxy_model.rowCount(index) > 0:
                    remove = True
                    break
        self.addOptBtn.setEnabled(add)
        self.removeOptBtn.setEnabled(remove)
        self.restoreDefaultsBtn.setEnabled(restore_defaults)
        self.moveUpTb.setEnabled(move)
        self.moveDownTb.setEnabled(move)

    def move_option(self, move=None):
        if move not in [1, -1]:
            logging.debug("Invalid move value passed to move_option method")
            return
        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0 and len(selection) > 1:
            logging.debug("No/multiple options selected when trying to move")
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

    def merge_data(self, options, json_file_data):
        # Check if dictionary options with fixed key/value pairs match data types from default
        for key in fixed_dict_options:
            if key in json_file_data:
                options[key] = self.compare_data(options[key], json_file_data[key])[0]

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
                    options[key] = temp_data

        # add filepicker default to import plugins if missing
        for plugin in options["import_plugins"]:
            if len(options["import_plugins"][plugin]) == 3:
                options["import_plugins"][plugin].append("default")

        # add filepicker default to export plugins if missing
        for plugin in options["export_plugins"]:
            if len(options["export_plugins"][plugin]) == 3:
                options["export_plugins"][plugin].append("default")

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
                    options[key] = temp_data

        # Check if options with fixed key/value pair structure match data types from default
        for key in key_value_options:
            if key in json_file_data:
                data, match = self.compare_data(options[key], json_file_data[key])
                if match:
                    options[key] = data

        return options

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
                    json_data = dict_option_structure[option]
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                elif option in list_option_structure:
                    json_data = list_option_structure[option]
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                    # increase row count in view
                    rows = self.json_model.rowCount(index) - 1
                    new_item = self.json_model.itemFromIndex(self.json_model.index(rows, 0, index))
                    new_item.setData(rows, QtCore.Qt.DisplayRole)
                self.statusbar.showMessage("")
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
                logging.debug(f"Added new value for {option}")
                break

    def remove_option_handler(self):
        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0:
            logging.debug("zero selections while trying to remove option")
            self.statusbar.showMessage("Please select one/more options to remove")
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

        # dialog_box = QtWidgets.QMessageBox.question(self, 'Remove option',
        #                 'Are you sure about removing the selected options?',
        #                 QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        # if dialog_box == QtWidgets.QMessageBox.No:
        #     return

        if removable_indexes == {} and non_removable != []:
            self.statusbar.showMessage("Default options are not removable.")
            return

        options = "\n".join([index.data() for index in removable_indexes])
        logging.debug(f"Trying to remove the following options\n{options}")

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
                if k == option:
                    data[k] = value
                    break
                if isinstance(v, collections.abc.Mapping):
                    data[k] = update(data.get(k, {}), option, value)
            return data

        selection = self.view.selectionModel().selectedRows()
        if len(selection) == 0:
            logging.debug("no selections while trying to restore defaults")
            self.statusbar.showMessage("Please select one/more options to restore defaults")
            return

        # dialog_box = QtWidgets.QMessageBox.question(self, 'Remove option',
        #                 'Are you sure about restoring default values for the selected options?',
        #                 QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        # if dialog_box == QtWidgets.QMessageBox.No:
        #     return

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

        options = "\n".join([index.data() for index in selected_indexes])
        logging.debug(f"Trying to restore defaults for the following options\n{options}")

        for index in selected_indexes:
            if not index.parent().isValid() and index.data() in key_value_options:
                value_index = self.json_model.index(index.row(), 1, QtCore.QModelIndex())
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
                    key = None
                    value = copy.deepcopy(default_options)
                    for parent in parent_list + [index]:
                        parent_data = parent.data()
                        if isinstance(value, list):
                            break
                        key = parent_data
                        value = value[parent_data]
                    data = copy.deepcopy(model_data[option])
                    json_data = update(data, key, value)
            else:
                json_data = default_options[option]
            if model_data[option] == json_data:
                continue
            # remove all rows
            for row in range(self.proxy_model.rowCount(root_index)):
                self.proxy_model.removeRow(0, parent=root_index)
            # add default values
            source_index = self.proxy_model.mapToSource(root_index)
            source_item = self.json_model.itemFromIndex(source_index)
            type_ = match_type(json_data)
            type_.next(model=self.json_model, data=json_data, parent=source_item)
        self.statusbar.showMessage("Defaults restored for selected options")
        self.view.clearSelection()

    def import_config(self):
        file_path = get_open_filename(self, "Import config", "", ';;'.join(["*.json", "*.*"]))
        if not file_path:
            return

        # load data from selected file
        dir_name, file_name = fs.path.split(file_path)
        with fs.open_fs(dir_name) as _fs:
            if _fs.exists(file_name):
                file_content = _fs.readtext(file_name)
                try:
                    json_file_data = json.loads(file_content)
                except Exception as e:
                    self.statusbar.showMessage("Unexpected error while loading data from file")
                    logging.error(f"Couldn't load json data\n Error:\n{e}")
                    return

        if json_file_data:
            logging.debug("Merging default and JSON data from file")
            json_model_data = self.json_model.serialize()
            options = self.merge_data(copy.deepcopy(json_model_data), json_file_data)
            if options == json_model_data:
                self.statusbar.showMessage("No option with new values found")
                return
            # replace existing data with new ones
            self.json_model.init(options, editable_keys=True, editable_values=True)
            self.view.setColumnWidth(0, self.view.width() // 2)
            self.set_noneditable_items(QtCore.QModelIndex())
            self.statusbar.showMessage("Successfully imported config")
        else:
            self.statusbar.showMessage("No data found in the file")
            logging.debug("No data found in the file, using existing settings")

    def check_modified(self):
        return not self.last_saved == self.json_model.serialize()

    def _save_to_path(self, filename):
        self.last_saved = self.json_model.serialize()
        json_data = copy.deepcopy(self.last_saved)
        save_data = copy.deepcopy(self.last_saved)

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
            if json_data[key] == default_options[key] or json_data[key] == {} or json_data[key] == []:
                del save_data[key]

        dir_name, file_name = fs.path.split(filename)
        with fs.open_fs(dir_name) as _fs:
            _fs.writetext(file_name, json.dumps(save_data, indent=4))

    def save_config(self):
        if self.check_modified():
            logging.debug("saving config file to: %s", self.path)
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
        else:
            self.statusbar.showMessage("No values changed")

    def export_config(self):
        if self.json_model.serialize() == default_options:
            # Todo - notify user about no non-default values
            # return
            pass
        path = get_save_filename(self, "Export config", "mss_settings", "Json files (*.json)")
        if path:
            self._save_to_path(path)

    def closeEvent(self, event):
        if self.check_modified():
            ret = QtWidgets.QMessageBox.question(
                self, self.tr("Mission Support System"),
                self.tr("Save Changes to default mss_settings.json?\n"
                        "You need to restart the gui for changes to take effect."),
                QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if ret == QtWidgets.QMessageBox.Yes:
                self.save_config()
        else:
            self.viewCloses.emit()
            event.accept()
