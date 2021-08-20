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
from mslib.msui.constants import MSS_SETTINGS
from mslib.msui.icons import icons
from mslib.utils import show_popup
from mslib.utils.config import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils.config import config_loader, dict_raise_on_duplicates_empty, merge_data


from mslib.support.qt_json_view import delegate
from mslib.support.qt_json_view.view import JsonView
from mslib.support.qt_json_view.model import JsonModel
from mslib.support.qt_json_view.datatypes import match_type, DataType, TypeRole, ListType


InvalidityRole = TypeRole + 1
DummyRole = TypeRole + 2
default_options = config_loader(default=True)


def get_root_index(index, parents=False):
    parent_list = []
    while index.parent().isValid():
        index = index.parent()
        parent_list.append(index)
    parent_list.reverse()
    if parents:
        return index, parent_list
    return index


class JsonDelegate(delegate.JsonDelegate):

    def paint(self, painter, option, index):
        """Use method from the data type or fall back to the default."""
        if index.column() == 0:
            source_model = index.model()
            if isinstance(source_model, QtCore.QAbstractProxyModel):
                source_model = source_model.sourceModel()
            data = source_model.serialize()

            # bold the key which has non-default value
            root_index, parents = get_root_index(index, parents=True)
            parents.append(index)
            key = root_index.data()
            if key in mss_default.list_option_structure or key \
                in mss_default.dict_option_structure or key \
                in mss_default.key_value_options:
                if root_index == index and data[key] != default_options[key]:
                    option.font.setWeight(QtGui.QFont.Bold)
            elif key in mss_default.fixed_dict_options:
                model_data = data[key]
                default_data = default_options[key]
                for parent in parents[1:]:
                    parent_data = parent.data()
                    if isinstance(default_data, list):
                        parent_data = int(parent.data())
                    model_data = model_data[parent_data]
                    default_data = default_data[parent_data]
                if model_data != default_data:
                    option.font.setWeight(QtGui.QFont.Bold)

            return super(JsonDelegate, self).paint(painter, option, index)

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
    """MSUI configuration editor class. Provides user interface elements for editing mss_settings.json
    """

    restartApplication = QtCore.pyqtSignal(name="restartApplication")

    def __init__(self, parent=None):
        super(ConfigurationEditorWindow, self).__init__(parent)
        self.setupUi(self)

        self.restart_on_save = True

        options = config_loader()
        self.path = MSS_SETTINGS
        self.last_saved = copy.deepcopy(options)

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

        # Set view model
        self.proxy_model.setSourceModel(self.json_model)
        self.view.setModel(self.proxy_model)

        # Setting proxy model and view attributes
        self.proxy_model.setFilterKeyColumn(0)

        # Add actions to toolbar
        self.import_file_action = QtWidgets.QAction(
            QtGui.QIcon(icons("config_editor", "Folder-new.svg")), "Import config", self)
        self.import_file_action.setStatusTip("Import an external configuration file")
        self.toolBar.addAction(self.import_file_action)

        self.save_file_action = QtWidgets.QAction(
            QtGui.QIcon(icons("config_editor", "Document-save.svg")), "Save config", self)
        self.save_file_action.setStatusTip("Save current configuration")
        self.toolBar.addAction(self.save_file_action)

        self.export_file_action = QtWidgets.QAction(
            QtGui.QIcon(icons("config_editor", "Document-save-as.svg")), "Export config", self)
        self.export_file_action.setStatusTip("Export current configuration")
        self.toolBar.addAction(self.export_file_action)

        # Button signals
        self.optCb.currentIndexChanged.connect(self.selection_change)
        self.addOptBtn.clicked.connect(self.add_option_handler)
        self.removeOptBtn.clicked.connect(self.remove_option_handler)
        self.restoreDefaultsBtn.clicked.connect(self.restore_defaults)
        self.moveUpTb.clicked.connect(lambda: self.move_option(move=1))
        self.moveDownTb.clicked.connect(lambda: self.move_option(move=-1))

        # File action signals
        self.import_file_action.triggered.connect(self.import_config)
        self.save_file_action.triggered.connect(self.save_config)
        self.export_file_action.triggered.connect(self.export_config)

        # View/Model signals
        self.view.selectionModel().selectionChanged.connect(self.tree_selection_changed)
        self.json_model.dataChanged.connect(self.update_view)

        # set behaviour of widgets
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

        # set tooltip and make keys non-editable
        self.set_noneditable_items(QtCore.QModelIndex())

        # json view attributes
        self.view.setAlternatingRowColors(True)
        self.view.setColumnWidth(0, self.view.width() // 2)

        # Add invalidity roles and update status of keys
        self.update_view()

    def set_noneditable_items(self, parent):
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            item.setEditable(False)
            if item.text() in mss_default.fixed_dict_options:
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
            root_index = get_root_index(index)
            if root_index.data() not in mss_default.fixed_dict_options + mss_default.key_value_options:
                add, move = True, True

            # display error message if key has invalid values
            if not index.parent().isValid():
                root_index = get_root_index(index)
                source_index = self.proxy_model.mapToSource(root_index)
                item = self.json_model.itemFromIndex(source_index)
                if any(item.data(InvalidityRole)):
                    invalidity = item.data(InvalidityRole)
                    errors = {"empty": invalidity[0], "duplicate": invalidity[1], "invalid": invalidity[2]}
                    msg = ", ".join([key for key in errors if errors[key]])
                    msg += " values found"
                    self.statusbar.showMessage(msg)
                elif item.data(DummyRole):
                    self.statusbar.showMessage("Dummy values found")
                else:
                    self.statusbar.showMessage("")
        if len(selection) >= 1:
            restore_defaults = True
            for index in selection:
                index = get_root_index(index)
                if index.data() not in mss_default.fixed_dict_options + mss_default.key_value_options \
                    and self.proxy_model.rowCount(index) > 0:
                    remove = True
                    break

        self.addOptBtn.setEnabled(add)
        self.removeOptBtn.setEnabled(remove)
        self.restoreDefaultsBtn.setEnabled(restore_defaults)
        self.moveUpTb.setEnabled(move)
        self.moveDownTb.setEnabled(move)

    def update_view(self):
        source_model = self.json_model
        data = source_model.serialize()
        parent = QtCore.QModelIndex()
        for r in range(source_model.rowCount(parent)):
            root_index = source_model.index(r, 0, parent)
            root_item = source_model.itemFromIndex(root_index)

            empty, duplicate, invalid, dummy = [False] * 4
            color = QtCore.Qt.transparent
            key = root_index.data()
            if key in mss_default.dict_option_structure:
                child_keys = set()
                rows = source_model.rowCount(root_index)
                for row in range(rows):
                    child_key_data = source_model.index(row, 0, root_index).data()
                    child_keys.add(child_key_data)
                    if child_key_data == "":
                        empty = True

                # check for dummy values
                default = mss_default.dict_option_structure[key]
                values_dict = data[key]
                for value in values_dict:
                    if value in default:
                        if default[value] == values_dict[value]:
                            dummy = True
                            color = QtCore.Qt.gray
                            break

                # condition for checking duplicate and empty keys
                if len(child_keys) != rows or empty:
                    duplicate = True
                    color = QtCore.Qt.red
            elif key in mss_default.list_option_structure:
                values_list = data[key]
                # check if any dummy values
                if any([value == mss_default.list_option_structure[key][0] for value in values_list]):
                    dummy = True
                    color = QtCore.Qt.gray
                # check if any empty values
                if any([value == "" for value in values_list]):
                    empty = True
                    color = QtCore.Qt.red
                # check if any duplicate values
                if len(set(values_list)) != len(values_list):
                    duplicate = True
                    color = QtCore.Qt.red
            elif key == 'filepicker_default':
                if data[key] not in ['default', 'qt', 'fs']:
                    invalid = True
                    color = QtCore.Qt.red

            # set invalidityroles and dummyrole for key
            root_item.setData([empty, duplicate, invalid], InvalidityRole)
            root_item.setData(dummy, DummyRole)
            # set color for column 1
            item = source_model.itemFromIndex(root_index)
            item.setBackground(color)
            # set color for column 2
            source_index = source_model.index(r, 1, parent)
            item = source_model.itemFromIndex(source_index)
            item.setBackground(color)

    def show_all(self):
        # By default FilterKeyColumn of the proxy model is set to 0
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

        selected_index = get_root_index(selection[0])
        option = selected_index.data()
        parent = QtCore.QModelIndex()
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            if index.data() == option:
                if option in mss_default.fixed_dict_options + mss_default.key_value_options:
                    self.statusbar.showMessage(
                        "Option already exists. Please change value to your preference or restore to default.")
                    return
                elif option in mss_default.dict_option_structure:
                    json_data = mss_default.dict_option_structure[option]
                    type_ = match_type(json_data)
                    type_.next(model=self.json_model, data=json_data, parent=item)
                elif option in mss_default.list_option_structure:
                    json_data = mss_default.list_option_structure[option]
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
                self.update_view()
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
                if index.data() not in mss_default.fixed_dict_options + mss_default.key_value_options:
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
                if root.data() not in mss_default.fixed_dict_options + mss_default.key_value_options:
                    if root in removable_indexes:
                        removable_indexes[root].add(index.row())
                    else:
                        removable_indexes[root] = set([index.row()])
                else:
                    non_removable.append(index)

        if removable_indexes == {} and non_removable != []:
            self.statusbar.showMessage("Default options are not removable.")
            return

        # ToDo add confirmation dialog here

        options = "\n".join([index.data() for index in removable_indexes])
        logging.debug(f"Attempting to remove the following options\n{options}")

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

        self.statusbar.showMessage("Successfully removed values selected options")
        self.update_view()

    def restore_defaults(self):
        # function to update dict at a depth
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

        # get list of distinct indexes to restore
        model_data = self.json_model.serialize()
        selected_indexes = set()
        for index in selection:
            root_index, parent_list = get_root_index(index, parents=True)
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

        # ToDo add confirmation dialog here

        options = "\n".join([index.data() for index in selected_indexes])
        logging.debug(f"Attempting to restore defaults for the following options\n{options}")

        for index in selected_indexes:
            # check if root option and present in mss_default.key_value_options
            if not index.parent().isValid() and index.data() in mss_default.key_value_options:
                value_index = self.json_model.index(index.row(), 1, QtCore.QModelIndex())
                value_item = self.json_model.itemFromIndex(value_index)
                value_item.setData(default_options[index.data()], QtCore.Qt.DisplayRole)
                continue

            root_index, parent_list = get_root_index(index, parents=True)
            option = root_index.data()
            model_data = self.json_model.serialize()
            if option in mss_default.fixed_dict_options:
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
        self.update_view()

    def import_config(self):
        file_path = get_open_filename(self, "Import config", "", ";;".join(["JSON Files (*.json)", "All Files (*.*)"]))
        if not file_path:
            return

        # load data from selected file
        dir_name, file_name = fs.path.split(file_path)
        with fs.open_fs(dir_name) as _fs:
            if _fs.exists(file_name):
                file_content = _fs.readtext(file_name)
                try:
                    json_file_data = json.loads(file_content, object_pairs_hook=dict_raise_on_duplicates_empty)
                except json.JSONDecodeError as e:
                    show_popup(self, "Error while loading file", e)
                    logging.error(f"Error while loading json file {e}")
                    return
                except ValueError as e:
                    show_popup(self, "Invalid keys detected", e)
                    logging.error(f"Error while loading json file {e}")
                    return

        if json_file_data:
            json_model_data = self.json_model.serialize()
            options = merge_data(copy.deepcopy(json_model_data), json_file_data)
            if options == json_model_data:
                self.statusbar.showMessage("No option with new values found")
                return
            # replace existing data with new data
            self.json_model.init(options, editable_keys=True, editable_values=True)
            self.view.setColumnWidth(0, self.view.width() // 2)
            self.set_noneditable_items(QtCore.QModelIndex())
            self.update_view()
            self.statusbar.showMessage("Successfully imported config")
            logging.debug("Imported new config data from file")
        else:
            self.statusbar.showMessage("No data found in the file")
            logging.debug("No data found in the file, using existing settings")

    def _save_to_path(self, filename):
        self.last_saved = self.json_model.serialize()
        json_data = copy.deepcopy(self.last_saved)
        save_data = copy.deepcopy(self.last_saved)

        for key in json_data:
            if json_data[key] == default_options[key] or json_data[key] == {} or json_data[key] == []:
                del save_data[key]

        dir_name, file_name = fs.path.split(filename)
        with fs.open_fs(dir_name) as _fs:
            _fs.writetext(file_name, json.dumps(save_data, indent=4))

    def validate_data(self):
        invalid, dummy = False, False
        parent = QtCore.QModelIndex()
        for r in range(self.json_model.rowCount(parent)):
            index = self.json_model.index(r, 0, parent)
            item = self.json_model.itemFromIndex(index)
            invalid |= any(item.data(InvalidityRole))
            dummy |= item.data(DummyRole)

        return invalid, dummy

    def check_modified(self):
        return not self.last_saved == self.json_model.serialize()

    def save_config(self):
        invalid, dummy = self.validate_data()
        if invalid:
            show_popup(
                self,
                "Invalid values detected",
                "Please correct the invalid values (keys colored in red) to be able to save.")
            self.statusbar.showMessage("Please correct the values and try saving again")
            return False
        if dummy and self.check_modified():
            ret = QtWidgets.QMessageBox.warning(
                self, self.tr("Dummy values detected"),
                self.tr("Dummy values detected (keys colored in gray.)\n"
                        "Since they are dummy values you might face issues later on while working."
                        "\n\nDo you still want to continue to save?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.No:
                self.statusbar.showMessage("Please correct the values and try saving")
                return False

        if self.check_modified():
            logging.debug("saving config file to: %s", self.path)
            self._save_to_path(self.path)
            if self.restart_on_save:
                ret = QtWidgets.QMessageBox.warning(
                    self, self.tr("Mission Support System"),
                    self.tr("Do you want to restart the application?\n"
                            "(This is necessary to apply changes)"),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No)
                if ret == QtWidgets.QMessageBox.Yes:
                    self.restartApplication.emit()
                    self.restart_on_save = False
                    self.close()
            self.restart_on_save = True
        else:
            self.statusbar.showMessage("No values changed")
        return True

    def export_config(self):
        invalid, dummy = self.validate_data()
        if invalid:
            show_popup(
                self,
                "Invalid values detected",
                "Please correct the invalid values (keys colored in red) to be able to save.")
            self.statusbar.showMessage("Please correct the values and try exporting")
            return False

        if self.json_model.serialize() == default_options:
            msg = """Since the current configuration matches the default configuration, \
only an empty json file would be exported.\nDo you still want to continue?"""
            ret = QtWidgets.QMessageBox.warning(
                self, self.tr("Mission Support System"), self.tr(msg),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.No:
                return

        path = get_save_filename(self, "Export configuration", "mss_settings", "JSON files (*.json)")
        if path:
            self._save_to_path(path)

    def closeEvent(self, event):
        msg = ""
        invalid, dummy = self.validate_data()
        if invalid:
            msg = self.tr("Invalid keys/values found in config.\nDo you want to rectify and save changes?")
        elif dummy and not self.check_modified:
            msg = self.tr("Dummy keys/values found in config.\nDo you want to rectify and save changes?")
        elif self.check_modified():
            msg = self.tr(
                "Save Changes to default mss_settings.json?\nYou need to restart the gui for changes to take effect.")
        if msg != "":
            ret = QtWidgets.QMessageBox.warning(
                self, self.tr("Mission Support System"), self.tr(msg),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                if not self.save_config():
                    event.ignore()
                    return
        elif self.restart_on_save:
            ret = QtWidgets.QMessageBox.warning(
                self, self.tr("Mission Support System"),
                self.tr("Do you want to close the config editor?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.No:
                event.ignore()
                return

        event.accept()
