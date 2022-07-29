# -*- coding: utf-8 -*-
"""

    mslib.multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~

    Control Widget to configure multiple flightpath on topview.

    This file is part of MSS.

    :copyright: Copyright 2017 Main Contributor
    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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
from PyQt5 import QtWidgets, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mpl_qtwidget import MplTopViewCanvas
from mslib.utils.qt import get_open_filenames
from mslib.utils.config import load_settings_qsettings, save_settings_qsettings


class MultipleFlightpath(MplTopViewCanvas):
    """
    Represent a Multiple FLightpath
    """

    def __init__(self):
        super().__init__()


class MultipleFlightpathControlWidget(QtWidgets.QWidget, ui.Ui_MultipleViewWidget):
    """
    This class provides the interface for plotting Multiple Flighttracks
    on the TopView canvas.
    """

    def __init__(self, parent=None, view=None):
        super(MultipleFlightpathControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view  # canvas
        self.dict_files = {}

        # Connect Signals and Slots
        self.bt_addFile.clicked.connect(self.get_file)

        self.settings_tag = "multipledock"
        settings = load_settings_qsettings(
            self.settings_tag, {"filename": "", "saved_files": {}})

        self.directory_location = settings["filename"]
        if parent is not None:
            parent.viewCloses.connect(self.save_settings)
        # Restore previously stored sessions
        if settings["saved_files"] is not None:
            delete_files = []
            self.dict_files = settings["saved_files"]
            for fn in self.dict_files:
                if os.path.isfile(fn) is True:
                    self.create_list_item(fn)
                else:
                    delete_files.append(fn)  # add non-existent files to list
                    logging.info("'%s' does not exist in the directory anymore.", fn)
            for fn in delete_files:
                del self.dict_files[fn]  # remove non-existent files from dictionary

    def get_file(self):
        """
        Slot that open opens a file dialog to choose FTML file.
        """
        filenames = get_open_filenames(
            self, "Open FTML File", os.path.dirname(str(self.directory_location)), "FTML Files(*.ftml)")
        if not filenames:
            return
        self.select_file(filenames)

    def save_settings(self):
        """
        Save Flighttrack settings after closing of view.
        """
        for entry in self.dict_files.values():
            entry["track"] = None
        settings = {
            "filename": str(self.directory_location),
            "saved_files": self.dict_files
        }
        save_settings_qsettings(self.settings_tag, settings)

    def select_file(self, filenames):
        """
        Initializes selected file.
        """
        for filename in filenames:
            if filename is None:
                return
            text = filename
            if text not in self.dict_files:
                self.dict_files[text] = {}

                self.directory_location = text
                self.create_list_item(text)
            else:
                logging.info("%s file already added", text)
        self.labelStatus.setText("Status: Files added successfully.")

    def create_list_item(self, text):
        """
        Add Flighttracks to list widget.
        """
        item = QtWidgets.QListWidgetItem(text)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.list_flighttrack.addItem(item)

