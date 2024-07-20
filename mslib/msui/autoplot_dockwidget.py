# -*- coding: utf-8 -*-
"""

    mslib.utils.autoplot_dockingwidget
    ~~~~~~~~~~~~~~~~

    This is a docking widget that allows the user to create the
    json file or edit the json file which can be used by the CLI for
    automatically downloading the plots.

    This file is part of MSS.

    :copyright: Copyright 2024 Preetam Sundar Das
    :copyright: Copyright 2024 by the MSS team, see AUTHORS.
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
import json
from PyQt5.QtWidgets import QWidget, QFileDialog, QTreeWidgetItem
from mslib.msui.qt5.ui_mss_autoplot import Ui_AutoplotDockWidget
from mslib.msui import constants as const


class AutoplotDockWidget(QWidget, Ui_AutoplotDockWidget):

    def __init__(self, parent=None, view=None, config_settings=None):
        super().__init__()
        self.setupUi(self)

        self.view = view
        self.url = None
        self.layer = None
        self.styles = None
        self.level = None
        self.flight = None
        self.sections = None
        self.vertical = None
        self.filename = None
        self.itime = None
        self.stime = None
        self.etime = None
        self.intv = None

        self.refresh_sig(config_settings)

        parent.refresh_signal_send.connect(lambda: self.refresh_sig(config_settings))

        # Add to TreeWidget
        if self.view == "Top View":
            self.addToAutoplotButton.clicked.connect(lambda: self.add_to_treewidget(
                parent, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name,
                parent.cbChangeMapSection.currentText(), None, parent.waypoints_model.name, parent.curritime,
                parent.currvtime, None, None, None, None
            ))
        elif self.view == "Side View":
            self.addToAutoplotButton.clicked.connect(lambda: self.add_to_treewidget(
                parent, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, None,
                parent.currvertical, parent.waypoints_model.name, parent.curritime, parent.currvtime, None, None,
                None, None
            ))
        else:
            self.addToAutoplotButton.clicked.connect(lambda: self.add_to_treewidget(
                parent, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, None, None,
                parent.waypoints_model.name, None, parent.currvtime, None, None, None, None
            ))

        self.addToAutoplotSecsButton.clicked.connect(lambda: self.add_to_treewidget(
            parent, config_settings, self.autoplotSecsTreeWidget, None, None, None, None, None, None,
            parent.currurl, parent.currlayer, str(parent.currstyles).strip(), parent.currlevel
        ))

        # Remove from Tree Widget
        self.RemoveFromAutoplotButton.clicked.connect(
            lambda: self.remove_selected_row(parent, self.autoplotTreeWidget, config_settings))
        self.RemoveFromAutoplotSecsButton.clicked.connect(
            lambda: self.remove_selected_row(parent, self.autoplotSecsTreeWidget, config_settings))

        # Update Tree Widget
        if self.view == "Top View":
            self.UploadAutoplotButton.clicked.connect(lambda: self.update_treewidget(
                parent, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name,
                parent.cbChangeMapSection.currentText(), None, parent.waypoints_model.name, parent.curritime,
                parent.currvtime, None, None, None, None
            ))
        elif self.view == "Side View":
            self.UploadAutoplotButton.clicked.connect(lambda: self.update_treewidget(
                parent, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, None,
                parent.currvertical, parent.waypoints_model.name, None, parent.currvtime, None, None, None, None
            ))
        else:
            self.UploadAutoplotButton.clicked.connect(lambda: self.update_treewidget(
                parent, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, None, None,
                parent.waypoints_model.name, None, parent.currvtime, None, None, None, None
            ))

        self.UploadAutoplotSecsButton.clicked.connect(lambda: self.update_treewidget(
            parent, config_settings, self.autoplotSecsTreeWidget, None, None, None, None, None, None,
            parent.currurl, parent.currlayer, str(parent.currstyles).strip(), parent.currlevel
        ))

        # config buttons
        self.selectConfigButton.clicked.connect(lambda: self.configure_from_path(parent, config_settings))
        self.updateConfigFile.clicked.connect(lambda: self.update_config_file(config_settings))

        # stime/etime
        self.stimeSpinBox.dateTimeChanged.connect(self.updateDateTimeValue)
        self.etimeSpinBox.dateTimeChanged.connect(self.updateDateTimeValue)

        # time interval combobox
        self.timeIntervalComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.timeIntervalComboBox))

    def configure_from_path(self, parent, config_settings):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select .json Config File", const.MSUI_CONFIG_PATH, "JSON Files (*.json)", options=options)

        if fileName is not None:
            with open(fileName, 'r') as file:
                configure = json.load(file)
            autoplot_flights = configure["automated_plotting_flights"]
            autoplot_hsecs = configure["automated_plotting_hsecs"]
            autoplot_vsecs = configure["automated_plotting_vsecs"]
            autoplot_lsecs = configure["automated_plotting_lsecs"]

            config_settings["automated_plotting_flights"] = autoplot_flights
            config_settings["automated_plotting_hsecs"] = autoplot_hsecs
            config_settings["automated_plotting_vsecs"] = autoplot_vsecs
            config_settings["automated_plotting_lsecs"] = autoplot_lsecs

            parent.refresh_signal_emit.emit()

    def add_to_treewidget(self, parent, config_settings, treewidget, flight, sections, vertical, filename, itime,
                          vtime, url, layer, styles, level):
        if treewidget.objectName() == "autoplotTreeWidget":
            item = QTreeWidgetItem([flight, sections, vertical, filename, itime, vtime])
            self.autoplotTreeWidget.addTopLevelItem(item)
            self.autoplotTreeWidget.setCurrentItem(item)
            config_settings["automated_plotting_flights"].append([flight, sections, vertical, filename, itime, vtime])
            parent.refresh_signal_emit.emit()
        if treewidget.objectName() == "autoplotSecsTreeWidget":
            item = QTreeWidgetItem([url, layer, styles, level, self.stime, self.etime, self.intv])
            self.autoplotSecsTreeWidget.addTopLevelItem(item)
            self.autoplotSecsTreeWidget.setCurrentItem(item)

            if self.view == "Top View":
                config_settings["automated_plotting_hsecs"].append([url, layer, styles, level])
            elif self.view == "Side View":
                config_settings["automated_plotting_vsecs"].append([url, layer, styles, level])
            else:
                config_settings["automated_plotting_lsecs"].append([url, layer, styles, level])
        self.resize_treewidgets()

    def update_treewidget(self, parent, config_settings, treewidget, flight, sections, vertical, filename, itime,
                          vtime, url, layer, styles, level):
        if treewidget.objectName() == "autoplotTreeWidget":
            selected_item = self.autoplotTreeWidget.currentItem()
            selected_item.setText(0, flight)
            selected_item.setText(3, filename)
            selected_item.setText(5, vtime)
            if self.view == "Top View":
                selected_item.setText(1, sections)
                selected_item.setText(4, itime)
            elif self.view == "Side View":
                selected_item.setText(2, vertical)

            index = treewidget.indexOfTopLevelItem(selected_item)
            settings_list = config_settings["automated_plotting_flights"][index]
            if self.view == "Top View":
                config_settings["automated_plotting_flights"][index] = [
                    flight, sections, settings_list[2], filename, itime, vtime]
            elif self.view == "Side View":
                config_settings["automated_plotting_flights"][index] = [
                    flight, settings_list[1], vertical, filename, settings_list[4], vtime]
            else:
                config_settings["automated_plotting_flights"][index] = [
                    flight, settings_list[1], settings_list[2], filename, settings_list[4], vtime]
            parent.refresh_signal_emit.emit()

        if treewidget.objectName() == "autoplotSecsTreeWidget":
            selected_item = self.autoplotSecsTreeWidget.currentItem()
            selected_item.setText(0, url)
            selected_item.setText(1, layer)
            selected_item.setText(2, styles)
            selected_item.setText(3, level)
            selected_item.setText(4, self.stime)
            selected_item.setText(5, self.etime)
            selected_item.setText(6, self.intv)
            index = treewidget.indexOfTopLevelItem(selected_item)
            if self.view == "Top View":
                if index != -1:
                    config_settings["automated_plotting_hsecs"][index] = [url, layer, styles, level]
            elif self.view == "Side View":
                if index != -1:
                    config_settings["automated_plotting_vsecs"][index] = [url, layer, styles, level]
            else:
                if index != -1:
                    config_settings["automated_plotting_lsecs"][index] = [url, layer, styles, level]
        self.resize_treewidgets()

    def refresh_sig(self, config_settings):
        autoplot_flights = config_settings["automated_plotting_flights"]
        if self.view == "Top View":
            autoplot_secs = config_settings["automated_plotting_hsecs"]
        elif self.view == "Side View":
            autoplot_secs = config_settings["automated_plotting_vsecs"]
        else:
            autoplot_secs = config_settings["automated_plotting_lsecs"]

        self.autoplotTreeWidget.clear()
        for row in autoplot_flights:
            item = QTreeWidgetItem(row)
            self.autoplotTreeWidget.addTopLevelItem(item)

        self.autoplotSecsTreeWidget.clear()
        for row in autoplot_secs:
            item = QTreeWidgetItem(row)
            self.autoplotSecsTreeWidget.addTopLevelItem(item)

    def remove_selected_row(self, parent, treewidget, config_settings):
        selected_item = treewidget.currentItem()
        if selected_item:
            index = treewidget.indexOfTopLevelItem(selected_item)
            if index != -1:
                treewidget.takeTopLevelItem(index)
                if treewidget.objectName() == "autoplotTreeWidget":
                    config_settings["automated_plotting_flights"].pop(index)
                if treewidget.objectName() == "autoplotSecsTreeWidget":
                    if self.view == "Top View":
                        config_settings["automated_plotting_hsecs"].pop(index)
                    elif self.view == "Side View":
                        config_settings["automated_plotting_vsecs"].pop(index)
                    else:
                        config_settings["automated_plotting_lsecs"].pop(index)
            else:
                parent = selected_item.parent()
                if parent:
                    parent.takeChild(parent.indexOfChild(selected_item))
        parent.refresh_signal_emit.emit()
        self.resize_treewidgets()

    def combo_box_input(self, combo):
        comboBoxName = combo.objectName()
        currentText = combo.currentText()
        if comboBoxName == "timeIntervalComboBox":
            self.intv = currentText

    def updateDateTimeValue(self):
        self.stime = self.stimeSpinBox.dateTime().toString('yyyy/MM/dd HH:mm UTC')
        self.etime = self.etimeSpinBox.dateTime().toString('yyyy/MM/dd HH:mm UTC')
    
    def resize_treewidgets(self):
        for i in range(6):
            self.autoplotTreeWidget.resizeColumnToContents(i)
        for i in range(7):
            self.autoplotSecsTreeWidget.resizeColumnToContents(i)  
        

    def update_config_file(self, config_settings):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            const.MSUI_CONFIG_PATH,
            "JSON Files (*.json);;All Files (*)",
            options=options
        )

        if file_path:
            with open(file_path, 'w') as file:
                json.dump(config_settings, file, indent=4)
