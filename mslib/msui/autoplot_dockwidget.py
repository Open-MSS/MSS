# -*- coding: utf-8 -*-
"""

    mslib.utils.autoplot_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

import os
import json
import logging
from datetime import datetime

import click
from PyQt5.QtWidgets import QWidget, QFileDialog, QTreeWidgetItem, QMessageBox
from PyQt5 import QtCore

from mslib.utils.mssautoplot import main as cli_tool
from mslib.msui.qt5.ui_mss_autoplot import Ui_AutoplotDockWidget
from mslib.msui import constants as const


class AutoplotDockWidget(QWidget, Ui_AutoplotDockWidget):

    treewidget_item_selected = QtCore.pyqtSignal(str, str, str, str)
    autoplot_treewidget_item_selected = QtCore.pyqtSignal(str, str)
    update_op_flight_treewidget = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None, parent2=None, view=None, config_settings=None):
        super().__init__()
        self.setupUi(self)

        self.UploadAutoplotButton.setVisible(False)
        self.UploadAutoplotSecsButton.setVisible(False)
        self.cpath = ""
        self.view = view
        self.url = ""
        self.layer = ""
        self.styles = ""
        self.level = ""
        self.flight = ""
        self.sections = ""
        self.vertical = ""
        self.filename = ""
        self.itime = ""
        self.vtime = ""
        self.stime = ""
        self.etime = ""
        self.intv = ""

        self.refresh_sig(config_settings)

        parent.refresh_signal_send.connect(lambda: self.refresh_sig(config_settings))

        parent.vtime_vals.connect(lambda vtime_vals: self.update_stime_etime(vtime_vals))

        self.autoplotSecsTreeWidget.itemSelectionChanged.connect(self.autoplotSecsTreeWidget_selected_row)
        self.autoplotTreeWidget.itemSelectionChanged.connect(self.autoplotTreeWidget_selected_row)

        # Add to TreeWidget
        if self.view == "Top View":
            self.addToAutoplotButton.clicked.connect(lambda: self.add_to_treewidget(
                parent, parent2, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name,
                parent.cbChangeMapSection.currentText(), self.vertical, parent.waypoints_model.name, parent.curritime,
                parent.currvtime, "", "", "", ""
            ))
        elif self.view == "Side View":
            self.addToAutoplotButton.clicked.connect(lambda: self.add_to_treewidget(
                parent, parent2, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, "",
                parent.currvertical, parent.waypoints_model.name, parent.curritime, parent.currvtime, "", "",
                "", ""
            ))
        else:
            self.addToAutoplotButton.clicked.connect(lambda: self.add_to_treewidget(
                parent, parent2, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, "", "",
                parent.waypoints_model.name, "", parent.currvtime, "", "", "", ""
            ))

        self.addToAutoplotSecsButton.clicked.connect(lambda: self.add_to_treewidget(
            parent, parent2, config_settings, self.autoplotSecsTreeWidget, "", "", "", "", "", "",
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
                parent, parent2, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name,
                parent.cbChangeMapSection.currentText(), "", parent.waypoints_model.name, parent.curritime,
                parent.currvtime, "", "", "", ""
            ))
        elif self.view == "Side View":
            self.UploadAutoplotButton.clicked.connect(lambda: self.update_treewidget(
                parent, parent2, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, "",
                parent.currvertical, parent.waypoints_model.name, "", parent.currvtime, "", "", "", ""
            ))
        else:
            self.UploadAutoplotButton.clicked.connect(lambda: self.update_treewidget(
                parent, parent2, config_settings, self.autoplotTreeWidget, parent.waypoints_model.name, "", "",
                parent.waypoints_model.name, "", parent.currvtime, "", "", "", ""
            ))

        self.UploadAutoplotSecsButton.clicked.connect(lambda: self.update_treewidget(
            parent, parent2, config_settings, self.autoplotSecsTreeWidget, "", "", "", "", "", "",
            parent.currurl, parent.currlayer, str(parent.currstyles).strip(), parent.currlevel
        ))

        # config buttons
        self.selectConfigButton.clicked.connect(lambda: self.configure_from_path(parent, config_settings))
        self.updateConfigFile.clicked.connect(lambda: self.update_config_file(config_settings))
        self.updateConfigFile.setDefault(True)

        # time interval combobox
        self.timeIntervalComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.timeIntervalComboBox))
        # stime/etime
        self.stimeComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.stimeComboBox))
        self.etimeComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.etimeComboBox))

        self.autoplotTreeWidget.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.autoplotSecsTreeWidget.itemSelectionChanged.connect(self.on_item_selection_changed_secs)
        self.downloadPushButton.clicked.connect(lambda: self.download_plots_cli(config_settings))

    def download_plots_cli(self, config_settings):
        if self.stime > self.etime:
            QMessageBox.information(
                self,
                "WARNING",
                "Start time should be before end time"
            )
            return
        if self.autoplotSecsTreeWidget.topLevelItemCount() == 0:
            QMessageBox.information(
                self,
                "WARNING",
                "Cannot download empty treewidget"
            )
            return
        view = "top"
        intv = 0
        if self.intv != "":
            index = self.intv.find(' ')
            intv = int(self.intv[:index])

        if self.view == "Top View":
            view = "top"
        elif self.view == "Side View":
            view = "side"
        else:
            view = "linear"

        # Create the configuration path
        config_path = os.path.join(const.MSUI_CONFIG_PATH, "mssautoplot.json")

        # Save the config settings to the file
        if config_path:
            with open(config_path, 'w') as file:
                json.dump(config_settings, file, indent=4)

        args = {
            'cpath': config_path,
            'view': view,
            'ftrack': "",
            'itime': self.itime,
            'vtime': self.vtime,
            'intv': intv,
            'stime': self.stime[:-1],
            'etime': self.etime[:-1]
        }

        # Invoke the main method using click from the mssautoplot
        try:
            ctx = click.Context(cli_tool)
            ctx.obj = self
            ctx.invoke(cli_tool, **args)
        except SystemExit as ex:
            logging.error("Can't find given data: %s", ex)
            QMessageBox.information(
                self,
                "Error",
                ex.args[0]
            )
            ctx.obj = None
            return

    def autoplotSecsTreeWidget_selected_row(self):
        selected_items = self.autoplotSecsTreeWidget.selectedItems()
        if selected_items:
            url = selected_items[0].text(0)
            layer = selected_items[0].text(1)
            styles = selected_items[0].text(2)
            level = selected_items[0].text(3)

            self.treewidget_item_selected.emit(url, layer, styles, level)

    def autoplotTreeWidget_selected_row(self):
        if self.autoplotSecsTreeWidget.topLevelItemCount() == 0:
            QMessageBox.information(
                self,
                "WARNING",
                "Select right tree widget row first."
            )
            return
        selected_items = self.autoplotTreeWidget.selectedItems()
        if selected_items:
            flight = selected_items[0].text(0)
            filename = selected_items[0].text(3)
            section = selected_items[0].text(1)
            vtime = selected_items[0].text(5)
            if flight != "" and flight == filename:
                self.update_op_flight_treewidget.emit("operation", flight)
            elif flight != "":
                self.update_op_flight_treewidget.emit("flight", flight)
            self.autoplot_treewidget_item_selected.emit(section, vtime)

    def update_stime_etime(self, vtime_data):
        self.stimeComboBox.clear()
        self.etimeComboBox.clear()
        self.stimeComboBox.addItem("")
        self.etimeComboBox.addItem("")
        self.stimeComboBox.addItems(vtime_data)
        self.etimeComboBox.addItems(vtime_data)

    def on_item_selection_changed(self):
        selected_item = self.autoplotTreeWidget.selectedItems()
        if selected_item:
            self.UploadAutoplotButton.setVisible(True)
        else:
            self.UploadAutoplotButton.setVisible(False)

    def on_item_selection_changed_secs(self):
        selected_item = self.autoplotSecsTreeWidget.selectedItems()
        if selected_item:
            self.UploadAutoplotSecsButton.setVisible(True)
        else:
            self.UploadAutoplotSecsButton.setVisible(False)

    def configure_from_path(self, parent, config_settings):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select .json Config File", const.MSUI_CONFIG_PATH, "JSON Files (*.json)", options=options)

        if fileName != "":
            self.cpath = fileName
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
            self.resize_treewidgets()

    def add_to_treewidget(self, parent, parent2, config_settings, treewidget, flight, sections, vertical, filename,
                          itime, vtime, url, layer, styles, level):
        if treewidget.objectName() == "autoplotTreeWidget":
            if self.autoplotSecsTreeWidget.topLevelItemCount() == 0:
                QMessageBox.information(
                    self,
                    "WARNING",
                    "Add right tree widget row first."
                )
                return
            if flight.startswith("new flight track"):
                filename = ""
                flight = ""
            else:
                if filename != parent2.mscolab.active_operation_name:
                    filename += ".ftml"
            item = QTreeWidgetItem([flight, sections, vertical, filename, itime, vtime])
            self.autoplotTreeWidget.addTopLevelItem(item)
            self.autoplotTreeWidget.setCurrentItem(item)
            config_settings["automated_plotting_flights"].append([flight, sections, vertical, filename, itime, vtime])
            parent.refresh_signal_emit.emit()
        if treewidget.objectName() == "autoplotSecsTreeWidget":
            if url == "":
                QMessageBox.information(
                    self,
                    "WARNING",
                    "Please select the URL, layer, styles and level (row information first)"
                )
                return
            item = QTreeWidgetItem([url, layer, styles, level, self.stime, self.etime, self.intv])
            self.autoplotSecsTreeWidget.addTopLevelItem(item)
            self.autoplotSecsTreeWidget.setCurrentItem(item)

            if self.view == "Top View":
                config_settings["automated_plotting_hsecs"].append([url, layer, styles, level])
            elif self.view == "Side View":
                config_settings["automated_plotting_vsecs"].append([url, layer, styles, level])
            else:
                config_settings["automated_plotting_lsecs"].append([url, layer, styles, level])
            self.autoplotSecsTreeWidget.clearSelection()
        self.resize_treewidgets()

    def update_treewidget(self, parent, parent2, config_settings, treewidget, flight, sections, vertical, filename,
                          itime, vtime, url, layer, styles, level):
        if flight.startswith("new flight track"):
            filename = ""
            flight = ""
        else:
            if filename != parent2.mscolab.active_operation_name:
                filename += ".ftml"
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
            if url == "":
                QMessageBox.information(
                    self,
                    "WARNING",
                    "Please select the URL, layer, styles and level (row information first)"
                )
                return
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
            self.autoplotSecsTreeWidget.clearSelection()
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
        self.autoplotSecsTreeWidget.clearSelection()
        self.autoplotTreeWidget.clearSelection()

    def remove_selected_row(self, parent, treewidget, config_settings):
        if treewidget.topLevelItemCount() == 0:
            QMessageBox.information(
                self,
                "WARNING",
                "Cannot remove from empty treewidget"
            )
            return
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
        self.stime = ""
        self.etime = ""

    def combo_box_input(self, combo):
        comboBoxName = combo.objectName()
        currentText = combo.currentText()
        if comboBoxName == "timeIntervalComboBox":
            if currentText == "":
                return
            if self.stimeComboBox.count() == 0:
                QMessageBox.information(
                    self,
                    "WARNING",
                    "Please select a layer first."
                )
                self.timeIntervalComboBox.setCurrentIndex(0)
                return
            datetime1_str = self.stimeComboBox.itemText(1)
            datetime2_str = self.stimeComboBox.itemText(2)

            datetime1 = datetime.strptime(datetime1_str, "%Y-%m-%dT%H:%M:%SZ")
            datetime2 = datetime.strptime(datetime2_str, "%Y-%m-%dT%H:%M:%SZ")
            time_difference = int((datetime2 - datetime1).total_seconds())
            time_diff = 1
            num = int(currentText.split()[0])
            if currentText.endswith("mins"):
                time_diff = time_diff * 60 * num
            elif currentText.endswith("hour"):
                time_diff = time_diff * 3600 * num
            elif currentText.endswith("hours"):
                time_diff = time_diff * 3600 * num
            elif currentText.endswith("days"):
                time_diff = time_diff * 86400 * num

            if time_diff % time_difference != 0:
                QMessageBox.information(
                    self,
                    "WARNING",
                    "Please select valid time interval."
                )
                self.timeIntervalComboBox.setCurrentIndex(0)
                return

            self.intv = currentText
        elif comboBoxName == "stimeComboBox":
            self.stime = currentText
        elif comboBoxName == "etimeComboBox":
            self.etime = currentText

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

            QMessageBox.information(
                self,
                "SUCCESS",
                "Configuration successfully saved."
            )
