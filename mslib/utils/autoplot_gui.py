# -*- coding: utf-8 -*-
"""

    mslib.utils.autoplot_gui
    ~~~~~~~~~~~~~~~~

    Python Scripts file for the GUI to download plots automatically.

    This file is part of MSS.

    :copyright: Copyright 2024 Preetam Sundar Das
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


import sys
import os
import requests
import json
import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QListWidgetItem,
                             QVBoxLayout,QComboBox, QPushButton, QLabel, QTreeWidgetItem)
from PyQt5 import QtCore
from mslib.msui.qt5.ui_mss_autoplot import Uploadui
from mslib.utils import config as conf
from mslib.utils.auth import save_password_to_keyring, get_auth_from_url_and_name, del_password_from_keyring
from mslib.msui import wms_control as wc


class SimpleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Simple GUI')
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.viewl = QLabel('Select View', self)
        layout.addWidget(self.viewl)

        self.viewCb = QComboBox(self)
        self.viewCb.addItem('Top View')
        self.viewCb.addItem('Side View')
        self.viewCb.addItem('Linear View')
        layout.addWidget(self.viewCb)

        self.openB = QPushButton('Open GUI', self)
        self.openB.clicked.connect(self.openautoplot)
        layout.addWidget(self.openB)

        self.setLayout(layout)

    def openautoplot(self):
        print("Opening MSSAUTOPLOT GUI...")
        if self.viewl.text()== "Side View":
            self.viewtype="side"
            widget = wc.VSecWMSControlWidget(
                default_WMS=conf.config_loader(dataset="default_WMS"),
                wms_cache=conf.config_loader(dataset="wms_cache"))
        elif self.viewl.text()== "Linear View":
            self.viewtype="linear"
            widget = wc.LSecWMSControlWidget(
                default_WMS=conf.config_loader(dataset="default_WMS"),
                wms_cache=conf.config_loader(dataset="wms_cache"))
        else:
            self.viewtype="top"
            widget = wc.HSecWMSControlWidget(
                default_WMS=conf.config_loader(dataset="default_WMS"),
                wms_cache=conf.config_loader(dataset="wms_cache"))
            
            
        widget.signal_disable_cbs.connect(self.disable_cbs)
        widget.signal_enable_cbs.connect(self.enable_cbs)

    @QtCore.pyqtSlot()
    def disable_cbs(self):
        self.wms_connected = True

    @QtCore.pyqtSlot()
    def enable_cbs(self):
        self.wms_connected = False



class Upload(QWidget, Uploadui):
    def __init__(self,viewtype):
        super().__init__()
        self.setupUi(self)
        self.cpath = None
        self.view = "top"
        self.itime = None
        self.vertical = None
        self.sections = None
        self.flight = None
        self.filename = None
        self.operations = None
        self.vtime = None
        self.intv = None
        self.stime = None
        self.etime = None

        self.url = None
        self.layer = None
        self.styles = None
        self.level = None

        self.num_interpolation_points = None
        self.num_labels = None
        self.resolution = None
        
        self.add_to_treewidget(self.autoplotTreeWidget)
        self.add_to_treewidget(self.autoplotsecsTreeWidget)
        
        self.ViewSelectedLabel.setText(viewtype)
        

        # cpath
        self.cpathButton.clicked.connect(self.open_file_dialog)

        # all QcomboBox
        # self.viewComboBox.currentIndexChanged.connect(
        #     lambda: self.combo_box_input(self.viewComboBox))
        self.itimeComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.itimeComboBox))
        self.verticalComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.verticalComboBox))
        self.sectionsComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.sectionsComboBox))

        self.stylesComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.stylesComboBox))
        self.levelComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.levelComboBox))

        self.stimeComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.stimeComboBox))
        self.etimeComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.etimeComboBox))
        self.vtimeComboBox.lineEdit().returnPressed.connect(
            lambda: self.combo_box_input(self.vtimeComboBox))
        self.intvComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.intvComboBox))

        # all pushButton
        self.flightAddButton.clicked.connect(self.add_flight)
        self.autoplotAddButton.clicked.connect(lambda: self.add_to_treewidget(self.autoplotTreeWidget))
        self.autoplotRemoveButton.clicked.connect(lambda: self.remove_selected_row(self.autoplotTreeWidget))
        self.autoplotsecsAddButton.clicked.connect(lambda: self.add_to_treewidget(self.autoplotsecsTreeWidget))
        self.autoplotsecsRemoveButton.clicked.connect(
            lambda: self.remove_selected_row(self.autoplotsecsTreeWidget))
        self.storePlotsButton.clicked.connect(self.store_plots)
        
    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select .json Config File", "", "JSON Files (*.json)", options=options)
        if fileName:
            self.cpath = fileName
            self.configure_from_path(self.cpath)
            self.cpathOutputLabel.setText(self.cpath)

    def configure_from_path(self, path):
        conf.read_config_file(path)
        configure = conf.config_loader()
        if self.view == "linear":
            sec = "automated_plotting_lsecs"
        elif self.view == "side":
            sec = "automated_plotting_vsecs"
        else:
            sec = "automated_plotting_hsecs"

        self.flight = configure["automated_plotting_flights"][0][0]
        self.filename = configure["automated_plotting_flights"][0][3]
        self.sections = configure["automated_plotting_flights"][0][1]
        self.vertical = configure["automated_plotting_flights"][0][2]
        self.itime = configure["automated_plotting_flights"][0][4]

        self.url = configure[sec][0][0]
        self.layer = configure[sec][0][1]
        self.styles = configure[sec][0][2]
        self.level = configure[sec][0][3]

    def mscolab_login_window(self):
        self.mscolab.open_connect_window()
        print(self.mscolab.mscolab_server_url, self.mscolab.token)
        val = self.mscolab.request_wps_from_server()
        print(val)

    # def store_plots(self):
    #     args = [
    #         "--cpath", self.cpath,
    #         "--view", self.view,
    #         "--ftrack", self.filename,
    #         "--itime", self.itime,
    #         "--vtime", self.vtime,
    #         "--intv", self.intv,
    #         "--stime", self.stime,
    #         "--etime", self.etime
    #     ]
    #     with click.Context(autopl):
    #         autopl.main(args=args, prog_name="autoplot_gui")
    
    def store_plots(self):
        data = []

        def get_item_data(item):
            row_data = [item.text(i) for i in range(item.columnCount())]
            children_data = []
            for i in range(item.childCount()):
                children_data.append(get_item_data(item.child(i)))
            return [row_data] + children_data

        def collect_data(item, level=0):
            while item:
                row_data = [item.text(i) for i in range(self.autoplotTreeWidget.columnCount())]
                if len(data) <= level:
                    data.append([])
                data[level].append(row_data)
                if item.childCount() > 0:
                    collect_data(item.child(0), level + 1)
                item = item.nextSibling()

        for i in range(self.autoplotTreeWidget.topLevelItemCount()):
            collect_data(self.autoplotTreeWidget.topLevelItem(i))

        with open("tree_data.json", "w") as file:
            json.dump(data, file, indent=4)

        print("Data saved to tree_data.json")
    
    
    # def store_plots(self):
    #     automnated_plotting_flights=[]
    #     automnated_plotting_flights_secs=[]       
        
        
    #     config = {
    #         'View':self.view,
    #         'automnated_plotting_flights':automnated_plotting_flights,
    #         'automnated_plotting_flights_secs':automnated_plotting_flights_secs,
    #         'Sections': self.sections
    #     }

    #     with open('config.json', 'w') as config_file:
    #         json.dump(config, config_file, indent=4)

    #     print("Configuration stored in config.json")

    def add_to_treewidget(self, treewidget):
        if treewidget.objectName() == "autoplotTreeWidget":
            item = QTreeWidgetItem(self.autoplotTreeWidget, ['', '', '', '', ''])
            self.autoplotTreeWidget.setCurrentItem(item)
        if treewidget.objectName() == "autoplotsecsTreeWidget":
            item = QTreeWidgetItem(self.autoplotsecsTreeWidget, ['', '', '', ''])
            self.autoplotsecsTreeWidget.setCurrentItem(item)

    def remove_selected_row(self, treewidget):
        selected_item = treewidget.currentItem()
        if selected_item:
            index = treewidget.indexOfTopLevelItem(selected_item)
            if index != -1:
                treewidget.takeTopLevelItem(index)
            else:
                parent = selected_item.parent()
                if parent:
                    parent.takeChild(parent.indexOfChild(selected_item))

    def update_selected_row(self, treewidget, column, value):
        selected_item = treewidget.currentItem()
        if selected_item:
            selected_item.setText(column, value)

    def combo_box_input(self, combo):
        comboBoxName = combo.objectName()
        currentText = combo.currentText()
        if comboBoxName == "viewComboBox":
            self.view = currentText
            if currentText == "Top View":
                self.view = "top"
            if currentText == "Side View":
                self.view = "side"
            if currentText == "Linear View":
                self.view = "linear"

        if comboBoxName == "itimeComboBox":
            self.itime = currentText
            # self.update_selected_row(self.autoplotTreeWidget, 4, comboBoxName.currentText())
        if comboBoxName == "verticalComboBox":
            self.vertical = currentText
            self.update_selected_row(self.autoplotTreeWidget, 2, currentText)
        if comboBoxName == "sectionsComboBox":
            self.sections = currentText
            self.update_selected_row(self.autoplotTreeWidget, 1, currentText)
        if comboBoxName == "stylesComboBox":
            self.styles = currentText
            self.update_selected_row(self.autoplotsecsTreeWidget, 2, currentText)
        if comboBoxName == "levelComboBox":
            self.level = currentText
            self.update_selected_row(self.autoplotsecsTreeWidget, 3, currentText)
        if comboBoxName == "resolutionComboBox":
            self.resolution = currentText
        if comboBoxName == "stimeComboBox":
            self.stime = currentText
        if comboBoxName == "etimeComboBox":
            self.etime = currentText
        if comboBoxName == "vtimeComboBox":
            self.vtime = currentText
        if comboBoxName == "intvComboBox":
            self.intv = currentText

    def on_spin_box_value_changed(self, value, spinName):
        spinBoxName = spinName.objectName()
        if spinBoxName == "numinterSpinBox":
            self.num_interpolation_points = value
        if spinBoxName == "numlabelsSpinBox":
            self.num_labels = value

    def add_flight(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select .ftml flights File", "", "ftml Files (*.ftml)", options=options)
        path = fileName
        if path:
            self.flight = path
            self.filename = os.path.basename(self.flight)
            self.update_selected_row(self.autoplotTreeWidget, 0, self.flight)
            self.update_selected_row(self.autoplotTreeWidget, 3, self.filename)

    def remove_flight(self):
        selected = self.autoplotTreeWidget.currentItem()
        if selected:
            self.update_selected_row(self.autoplotTreeWidget, 0, "")
            self.update_selected_row(self.autoplotTreeWidget, 1, "")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    sys.exit(app.exec_())
