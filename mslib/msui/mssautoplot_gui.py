"""

    mslib.msui.mssautoplot_gui
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A GUI for the mssautoplot CLI tool to create for instance a number of the same plots
    for several flights or several forecast steps

    This file is part of MSS.

    :copyright: Copyright 2022 Sreelakshmi Jayarajan
    :copyright: Copyright 2022 by the MSS team, see AUTHORS.
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
from PyQt5 import QtCore, QtGui, QtWidgets
from mslib.msui.qt5 import ui_mssautoplot_gui as ui
from mslib.utils import mssautoplot
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from mslib.utils.config import config_loader, read_config_file
from mslib.msui import constants
from datetime import datetime


class Mssautoplot_gui(ui.Ui_mssautoplot):
    def __init__(self, dock_widget):
        super().setupUi(dock_widget)
        self.dock_widget = dock_widget
        self.ConfigPathLabel.hide()
        self.ConfigPathlineEdit.hide()
        self.ConfigPathButton.hide()
        self.FileNameLabel.hide()
        self.FlightNameLabel.hide()
        self.ServerUrlLabel.hide()
        self.InitTimeLabel.hide()
        self.MapSectionLabel.hide()
        self.LevelLabel.hide()
        self.ValidTimeLabel.hide()
        self.path = constants.MSS_AUTOPLOT
        read_config_file(self.path)
        self.config = config_loader()
        for item in self.config["predefined_map_sections"].keys():
            self.MapSectioncomboBox.addItem(item)
        self.MapSectioncomboBox.hide()
        self.LevellineEdit.hide()
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.RetrieveButton.setFont(font)
        self.RetrieveButton.setObjectName("RetrieveButton")
        self.RetrieveButton.hide()
        self.FileNamelineEdit.hide()
        self.FileNameButton.setObjectName("FileNameButton")
        self.FileNameButton.hide()
        self.ServerUrllineEdit.hide()
        self.FlightNamelineEdit.hide()
        self.LayerLabel.hide()
        self.StyleLabel.hide()
        self.LayerlineEdit.hide()
        self.StylelineEdit.hide()
        self.StartTimedateTimeEdit.hide()
        self.EndTimedateTimeEdit.hide()
        self.IntervalspinBox.hide()
        self.IntervalLabel.hide()
        self.VerticalLabel.hide()
        self.VerticalDropDown.hide()
        self.config_path = ""
        self.flightpath = ""
        self.ConfigPathButton.clicked.connect(self.configFileBrowser)
        # self.retrieve.clicked.connect(self.openMultilayeringDialog)
        self.RetrieveButton.clicked.connect(self.retrieveImage)
        self.FileNameButton.clicked.connect(self.fileBrowser)
        self.SideViewradioButton.toggled.connect(self.passToggledside)
        self.TopViewradioButton.toggled.connect(self.passToggledtop)
        self.SinglePlotradioButton.toggled.connect(self.passToggledSinglePlot)
        self.MultiplePlotsradioButton.toggled.connect(self.passToggledMultiplePlots)

    def retrieveImage(self):
        if self.config_path == "":
            self.config_path = self.path
        init = self.StartTimedateTimeEdit.dateTime()
        valid = self.EndTimedateTimeEdit.dateTime()
        initpy = init.toPyDateTime()
        validpy = valid.toPyDateTime()
        inittime = datetime.strftime(initpy, '%Y-%m-%dT%H:%M:%S')
        validtime = datetime.strftime(validpy, '%Y-%m-%dT%H:%M:%S')
        if self.no_of_plots == "multiple":
            interval = self.IntervalspinBox.text()
            interval = int(interval)
            if interval == 0:
                raise Exception("Interval cannot be zero, please specify another number")
            starttime = inittime
            endtime = validtime
            print("calling")
            mssautoplot.autoplot(cpath=self.config_path, view=self.view, ftrack=self.flightpath,
                                 itime="", vtime="", stime=starttime, etime=endtime, intv=interval)
        else:
            if inittime == "2000-01-01T00:00:00":
                inittime = ""
            mssautoplot.autoplot(cpath=self.config_path, view=self.view, ftrack=self.flightpath,
                                 itime=inittime, vtime=validtime, stime="", etime="", intv=0)

    def configFileBrowser(self):
        file_browser = self.FileBrowserDialog()
        self.ConfigPathlineEdit.setText(file_browser.file)
        self.config_path = file_browser.path

    def fileBrowser(self):
        file_browser = self.FileBrowserDialog()
        self.FileNamelineEdit.setText(file_browser.file)
        self.flightpath = file_browser.path

    def passToggledtop(self):
        if not self.SideViewradioButton.isChecked():
            self.view = "top"
            self.TopViewradioButton.show()
            self.SideViewradioButton.show()
            self.ConfigPathLabel.show()
            self.ConfigPathlineEdit.show()
            self.FileNameLabel.show()
            self.FlightNameLabel.show()
            self.ServerUrlLabel.show()
            self.VerticalLabel.hide()
            self.VerticalDropDown.hide()
            self.MapSectionLabel.show()
            self.LevelLabel.show()
            self.MapSectioncomboBox.show()
            self.LevellineEdit.show()
            self.RetrieveButton.show()
            self.ConfigPathButton.show()
            self.FileNamelineEdit.show()
            self.FileNameButton.show()
            self.ServerUrllineEdit.show()
            self.FlightNamelineEdit.show()
            self.LayerLabel.show()
            self.StyleLabel.show()
            self.LayerlineEdit.show()
            self.StylelineEdit.show()
            self.NoOfPlotsLabel.show()
            self.SinglePlotradioButton.show()
            self.MultiplePlotsradioButton.show()

    def passToggledside(self):
        if not self.TopViewradioButton.isChecked():
            self.view = "side"
            self.TopViewradioButton.show()
            self.SideViewradioButton.show()
            self.ConfigPathLabel.show()
            self.ConfigPathlineEdit.show()
            self.FileNameLabel.show()
            self.FlightNameLabel.show()
            self.ServerUrlLabel.show()
            self.LevelLabel.hide()
            self.LevellineEdit.hide()
            self.VerticalLabel.show()
            self.VerticalDropDown.show()
            self.MapSectionLabel.show()
            self.MapSectioncomboBox.show()
            self.LevellineEdit.show()
            self.RetrieveButton.show()
            self.ConfigPathButton.show()
            self.FileNamelineEdit.show()
            self.FileNameButton.show()
            self.ServerUrllineEdit.show()
            self.FlightNamelineEdit.show()
            self.LayerLabel.show()
            self.StyleLabel.show()
            self.LayerlineEdit.show()
            self.StylelineEdit.show()
            self.NoOfPlotsLabel.show()
            self.SinglePlotradioButton.show()
            self.MultiplePlotsradioButton.show()

    def passToggledSinglePlot(self):
        _translate = QtCore.QCoreApplication.translate
        self.no_of_plots = "one"
        self.InitTimeLabel.show()
        self.ValidTimeLabel.show()
        self.InitTimeLabel.setText(_translate("mssautoplotGUI", "Init time"))
        self.ValidTimeLabel.setText(_translate("mssautoplotGUI", "Valid time"))
        self.StartTimedateTimeEdit.show()
        self.EndTimedateTimeEdit.show()
        self.IntervalLabel.hide()
        self.IntervalspinBox.hide()

    def passToggledMultiplePlots(self):
        _translate = QtCore.QCoreApplication.translate
        self.no_of_plots = "multiple"
        self.InitTimeLabel.show()
        self.ValidTimeLabel.show()
        self.InitTimeLabel.setText(_translate("mssautoplotGUI", "Start time"))
        self.ValidTimeLabel.setText(_translate("mssautoplotGUI", "End time"))
        self.StartTimedateTimeEdit.show()
        self.EndTimedateTimeEdit.show()
        self.IntervalLabel.show()
        self.IntervalspinBox.show()

    class FileBrowserDialog(QWidget):
        def __init__(self):
            super().__init__()
            self.title = 'mssautoplotGUI- MSS'
            self.left = 10
            self.top = 10
            self.width = 640
            self.height = 480
            self.initUI()

        def initUI(self):
            self.setWindowTitle(self.title)
            self.setGeometry(self.left, self.top, self.width, self.height)
            self.openFileNameDialog()
            self.show()

        def openFileNameDialog(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.path, _ = QFileDialog.getOpenFileName(self, "mssautoplotGUI- File browser", "",
                                                       "All Files (*);;Python Files (*.py)", options=options)
            if self.path:
                self.file = os.path.split(self.path)[1]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mssautoplotGUI = QtWidgets.QMainWindow()
    ui = Mssautoplot_gui(mssautoplotGUI)
    mssautoplotGUI.show()
    sys.exit(app.exec_())
