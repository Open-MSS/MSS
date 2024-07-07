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
import click
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QListWidgetItem,
                             QVBoxLayout, QPushButton, QLabel, QTreeWidgetItem)
from mslib.msui.qt5.ui_mss_autoplot import Uploadui
from mslib.msui.qt5.ui_wms_login import Loginwms
from mslib.utils import config as conf
from mslib.utils.mssautoplot import main as autopl
from mslib.msui.mscolab import MSColab_ConnectDialog, MSUIMscolab
from mslib.utils.auth import save_password_to_keyring, get_auth_from_url_and_name, del_password_from_keyring
from mslib.mscolab.conf import mscolab_settings
from mslib.msui import msui
from mslib.msui import mscolab
from mslib.msui.multilayers import Layer, Multilayers
from mslib.msui.wms_control import WMSControlWidget, HSecWMSControlWidget


class Layers(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.setWindowTitle('Layers Window')
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel('Select Layers Under development', self)
        layout.addWidget(self.label)

        self.closeButton = QPushButton('Close', self)
        self.closeButton.clicked.connect(self.close)
        layout.addWidget(self.closeButton)

        self.setLayout(layout)


class WmsLoginInfo(QWidget, Loginwms):
    def __init__(self, link):
        super().__init__()
        self.setupUi(self)
        self.savePushButton.clicked.connect(lambda: self.funct(link))

    def funct(self, link):
        wms = link
        usern = self.userNameLineEdit.text()
        passw = self.passwordLineEdit.text()
        save_password_to_keyring(service_name=wms, username=usern, password=passw)
        self.close()


class Upload(QWidget, Uploadui):
    def __init__(self):
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

        self.main_window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.mscolab = mscolab.MSUIMscolab(parent=self.main_window, data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.wmscon = WMSControlWidget()
        self.multilayers = Multilayers(self)
        self.widget = HSecWMSControlWidget(
            default_WMS=conf.config_loader(dataset="default_WMS"),
            wms_cache=conf.config_loader(dataset="wms_cache"))

        self.layersButton.clicked.connect(lambda: (self.multilayers.hide(), self.multilayers.show()))
        self.multilayers.btGetCapabilities.clicked.connect(self.wmscon.get_capabilities)

        # cpath
        self.cpathButton.clicked.connect(self.open_file_dialog)

        # all QcomboBox
        self.viewComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.viewComboBox))
        self.itimeComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.itimeComboBox))
        self.verticalComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.verticalComboBox))
        self.sectionsComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.sectionsComboBox))

        self.stylesComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.stylesComboBox))
        self.levelComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.levelComboBox))

        self.stimeComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.stimeComboBox))
        self.etimeComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.etimeComboBox))
        self.vtimeComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.vtimeComboBox))
        self.intvComboBox.currentIndexChanged.connect(
            lambda: self.combo_box_input(self.intvComboBox))

        # all pushButton
        self.flightAddButton.clicked.connect(self.add_flight)
        self.flightRemoveButton.clicked.connect(self.remove_flight)
        self.autoplotAddButton.clicked.connect(lambda: self.add_to_treewidget(self.autoplotTreeWidget))
        self.autoplotRemoveButton.clicked.connect(lambda: self.remove_from_treewidget(self.autoplotTreeWidget))
        self.urlAddButton.clicked.connect(self.add_url)
        self.urlRemoveButton.clicked.connect(self.remove_url)
        self.autoplotsecsAddButton.clicked.connect(lambda: self.add_to_treewidget(self.autoplotsecsTreeWidget))
        self.autoplotsecsRemoveButton.clicked.connect(
            lambda: self.remove_from_treewidget(self.autoplotsecsTreeWidget))
        # self.layersButton.clicked.connect(self.layers_window)
        self.storePlotsButton.clicked.connect(self.store_plots)
        self.mscolabLoginButton.clicked.connect(self.mscolab_login_window)

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

    def store_plots(self):
        args = [
            "--cpath", self.cpath,
            "--view", self.view,
            "--ftrack", self.filename,
            "--itime", self.itime,
            "--vtime", self.vtime,
            "--intv", self.intv,
            "--stime", self.stime,
            "--etime", self.etime
        ]
        with click.Context(autopl):
            autopl.main(args=args, prog_name="autoplot_gui")

    def add_to_treewidget(self, treewidget):
        if (treewidget.objectName() == "autoplotTreeWidget"):
            QTreeWidgetItem(self.autoplotTreeWidget, ['', '', '', '', ''])
        if (treewidget.objectName() == "autoplotsecsTreeWidget"):
            QTreeWidgetItem(self.autoplotsecsTreeWidget, ['', '', '', ''])

    def remove_from_treewidget(self, treewidget):
        selected_item = treewidget.currentItem()
        treewidget.takeTopelevationItem(self.tree.indexOfTopelevationItem(selected_item))

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
        text = self.flightLineEdit.text()
        if text:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Select .ftml flights File", "", "ftml Files (*.ftml)", options=options)
            path = fileName
            if path:
                self.flight = path
                self.filename = text
                self.update_selected_row(self.autoplotTreeWidget, 0, self.flight)
                self.update_selected_row(self.autoplotTreeWidget, 3, self.filename)
            self.flightLineEdit.clear()

    def remove_flight(self):
        selected = self.autoplotTreeWidget.currentItem()
        if selected:
            self.update_selected_row(self.autoplotTreeWidget, 0, "")
            self.update_selected_row(self.autoplotTreeWidget, 1, "")

    def add_url(self):
        link = self.urlLineEdit.text()
        if link:
            response = requests.get(link)
            if response.status_code == 401:
                self.check_url_in_keyring(link)
            else:
                self.update_selected_row(self.autoplotsecsTreeWidget, 0, link)

    def check_url_in_keyring(self, link):
        conf.read_config_file(self.cpath)
        configure = conf.config_loader()
        username, password = get_auth_from_url_and_name(link, configure["MSS_auth"])
        print(username, password)
        if username:
            check = self.check_website_access(link, username, password)
            if check == True:
                self.update_selected_row(self.autoplotsecsTreeWidget, 0, link)
            else:
                del_password_from_keyring(link, username)
                self.connect_dialog = WmsLoginInfo(link)
                self.connect_dialog.show()

        else:
            self.connect_dialog = WmsLoginInfo(link)
            self.connect_dialog.show()

    def check_website_access(self, link, username, password):
        try:
            response = requests.get(link, auth=requests.auth.HTTPBasicAuth(username, password))

            if response.status_code == 200:
                print("Authentication successful!")
                return True
            else:
                print(f"Failed to authenticate. Status code: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")

    def remove_url(self):
        selected = self.autoplotsecsTreeWidget.currentItem()
        if selected:
            self.update_selected_row(self.autoplotsecsTreeWidget, 0, "")

    def layers_window(self):
        self.layerobj = Layers()
        self.layerobj.show()


def main():
    app = QApplication(sys.argv)
    window = Upload()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
