"""

    mslib.msui.qt5.mssautoplot_gui
    ~~~~~~~~~~~~~~~~~~~~~~~

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
from mslib.utils import mssautoplot 
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QFileDialog
from mslib.utils.config import config_loader, read_config_file
from mslib.msui import constants
from datetime import datetime
from mslib.msui.qt5 import ui_wms_multilayers as wms_ui


class Ui_mssautoplot(object):
	def setupUi(self, mssautoplotGUI):
		mssautoplotGUI.setObjectName("mssautoplotGUI")
		mssautoplotGUI.resize(521, 671)
		self.centralwidget = QtWidgets.QWidget(mssautoplotGUI)
		self.centralwidget.setObjectName("centralwidget")
		self.ViewLabel = QtWidgets.QLabel(self.centralwidget)
		self.ViewLabel.setGeometry(QtCore.QRect(40, 30, 67, 17))
		self.ViewLabel.setObjectName("ViewLabel")

		self.TopViewradioButton = QtWidgets.QRadioButton(self.centralwidget)
		self.TopViewradioButton.setGeometry(QtCore.QRect(40, 60, 112, 23))
		self.TopViewradioButton.setObjectName("TopViewradioButton")

		self.SideViewradioButton = QtWidgets.QRadioButton(self.centralwidget)
		self.SideViewradioButton.setGeometry(QtCore.QRect(150, 60, 112, 23))
		self.SideViewradioButton.setObjectName("SideViewradioButton")

		self.ConfigPathLabel = QtWidgets.QLabel(self.centralwidget)
		self.ConfigPathLabel.setGeometry(QtCore.QRect(40, 200, 81, 17))
		self.ConfigPathLabel.setObjectName("ConfigPathLabel")
		self.ConfigPathLabel.hide()

		self.ConfigPathlineEdit = QLineEdit(self.centralwidget)
		self.ConfigPathlineEdit.setGeometry(QtCore.QRect(40, 220, 151, 25))
		self.ConfigPathlineEdit.setObjectName("ConfigPathlineEdit")
		self.ConfigPathlineEdit.hide()

		self.FileNameLabel = QtWidgets.QLabel(self.centralwidget)
		self.FileNameLabel.setGeometry(QtCore.QRect(40, 270, 67, 17))
		self.FileNameLabel.setObjectName("FileNameLabel")
		self.FileNameLabel.hide()

		self.FlightNameLabel = QtWidgets.QLabel(self.centralwidget)
		self.FlightNameLabel.setGeometry(QtCore.QRect(290, 200, 81, 16))
		self.FlightNameLabel.setObjectName("FlightNameLabel")
		self.FlightNameLabel.hide()

		self.ServerUrlLabel = QtWidgets.QLabel(self.centralwidget)
		self.ServerUrlLabel.setGeometry(QtCore.QRect(40, 340, 91, 17))
		self.ServerUrlLabel.setObjectName("ServerUrlLabel")
		self.ServerUrlLabel.hide()

		self.InitTimeLabel = QtWidgets.QLabel(self.centralwidget)
		self.InitTimeLabel.setGeometry(QtCore.QRect(40, 480, 67, 17))
		self.InitTimeLabel.setObjectName("InitTimeLabel")
		self.InitTimeLabel.hide()

		self.MapSectionLabel = QtWidgets.QLabel(self.centralwidget)
		self.MapSectionLabel.setGeometry(QtCore.QRect(290, 270, 91, 17))
		self.MapSectionLabel.setObjectName("MapSectionLabel")
		self.MapSectionLabel.hide()

		self.LevelLabel = QtWidgets.QLabel(self.centralwidget)
		self.LevelLabel.setGeometry(QtCore.QRect(290, 340, 67, 17))
		self.LevelLabel.setObjectName("LevelLabel")
		self.LevelLabel.hide()

		self.ValidTimeLabel = QtWidgets.QLabel(self.centralwidget)
		self.ValidTimeLabel.setGeometry(QtCore.QRect(290, 480, 67, 17))
		self.ValidTimeLabel.setObjectName("ValidTimeLabel")
		self.ValidTimeLabel.hide()

		self.MapSectioncomboBox = QtWidgets.QComboBox(self.centralwidget)
		self.MapSectioncomboBox.setGeometry(QtCore.QRect(290, 290, 201, 25))
		self.MapSectioncomboBox.setObjectName("MapSectioncomboBox")
		self.path = constants.MSS_AUTOPLOT
		read_config_file(self.path)
		self.config = config_loader()
		for item in self.config["predefined_map_sections"].keys():
			self.MapSectioncomboBox.addItem(item)
		self.MapSectioncomboBox.hide()

		self.LevellineEdit = QLineEdit(self.centralwidget)
		self.LevellineEdit.setGeometry(QtCore.QRect(290, 360, 201, 25))
		self.LevellineEdit.setObjectName("LevellineEdit")
		self.LevellineEdit.hide()

		self.RetrieveButton = QtWidgets.QPushButton(self.centralwidget)
		self.RetrieveButton.setGeometry(QtCore.QRect(400, 580, 89, 31))
		font = QtGui.QFont()
		font.setPointSize(11)
		font.setBold(True)
		font.setWeight(75)
		self.RetrieveButton.setFont(font)
		self.RetrieveButton.setObjectName("RetrieveButton")
		self.RetrieveButton.hide()

		self.ConfigPathButton = QtWidgets.QPushButton(self.centralwidget)
		self.ConfigPathButton.setGeometry(QtCore.QRect(190, 220, 51, 25))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.ConfigPathButton.setFont(font)
		self.ConfigPathButton.setObjectName("ConfigPathButton")
		self.ConfigPathButton.hide()

		self.FileNamelineEdit = QLineEdit(self.centralwidget)
		self.FileNamelineEdit.setGeometry(QtCore.QRect(40, 290, 151, 25))
		self.FileNamelineEdit.setObjectName("FileNamelineEdit")
		self.FileNamelineEdit.hide()

		self.FileNameButton = QtWidgets.QPushButton(self.centralwidget)
		self.FileNameButton.setGeometry(QtCore.QRect(190, 290, 51, 25))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.FileNameButton.setFont(font)
		self.FileNameButton.setObjectName("FileNameButton")
		self.FileNameButton.hide()

		self.ServerUrllineEdit = QLineEdit(self.centralwidget)
		self.ServerUrllineEdit.setGeometry(QtCore.QRect(40, 360, 201, 25))
		self.ServerUrllineEdit.setObjectName("ServerUrllineEdit")
		self.ServerUrllineEdit.hide()

		self.FlightNamelineEdit = QLineEdit(self.centralwidget)
		self.FlightNamelineEdit.setGeometry(QtCore.QRect(290, 220, 201, 25))
		self.FlightNamelineEdit.setObjectName("FlightNmaelineEdit")
		self.FlightNamelineEdit.hide()

		self.LayerLabel = QtWidgets.QLabel(self.centralwidget)
		self.LayerLabel.setGeometry(QtCore.QRect(40, 410, 67, 17))
		self.LayerLabel.setObjectName("LayerLabel")
		self.LayerLabel.hide()

		self.StyleLabel = QtWidgets.QLabel(self.centralwidget)
		self.StyleLabel.setGeometry(QtCore.QRect(290, 410, 67, 17))
		self.StyleLabel.setObjectName("StyleLabel")
		self.StyleLabel.hide()

		self.LayerlineEdit = QLineEdit(self.centralwidget)
		self.LayerlineEdit.setGeometry(QtCore.QRect(40, 430, 201, 25))
		self.LayerlineEdit.setObjectName("LayerlineEdit")
		self.LayerlineEdit.hide()

		self.StylelineEdit = QLineEdit(self.centralwidget)
		self.StylelineEdit.setGeometry(QtCore.QRect(290, 430, 201, 25))
		self.StylelineEdit.setObjectName("StylelineEdit")
		self.StylelineEdit.hide()

		self.StartTimedateTimeEdit = QtWidgets.QDateTimeEdit(self.centralwidget)
		self.StartTimedateTimeEdit.setGeometry(QtCore.QRect(40, 500, 201, 26))
		self.StartTimedateTimeEdit.setObjectName("StartTimedateTimeEdit")
		self.StartTimedateTimeEdit.hide()

		self.EndTimedateTimeEdit = QtWidgets.QDateTimeEdit(self.centralwidget)
		self.EndTimedateTimeEdit.setGeometry(QtCore.QRect(290, 500, 201, 26))
		self.EndTimedateTimeEdit.setObjectName("EndTimedateTimeEdit")
		self.EndTimedateTimeEdit.hide()

		self.IntervalspinBox = QtWidgets.QSpinBox(self.centralwidget)
		self.IntervalspinBox.setGeometry(QtCore.QRect(40, 570, 201, 26))
		self.IntervalspinBox.setObjectName("IntervalspinBox")
		self.IntervalspinBox.hide()

		self.IntervalLabel = QtWidgets.QLabel(self.centralwidget)
		self.IntervalLabel.setGeometry(QtCore.QRect(40, 550, 121, 17))
		self.IntervalLabel.setObjectName("IntervalLabel")
		self.IntervalLabel.hide()

		self.NoOfPlotsLabel = QtWidgets.QLabel(self.centralwidget)
		self.NoOfPlotsLabel.setGeometry(QtCore.QRect(40, 110, 91, 17))
		self.NoOfPlotsLabel.setObjectName("NoOfPlotsLabel")

		self.SinglePlotradioButton = QtWidgets.QRadioButton(self.centralwidget)
		self.SinglePlotradioButton.setGeometry(QtCore.QRect(40, 140, 112, 23))
		self.SinglePlotradioButton.setObjectName("SinglePlotradioButton")

		self.MultiplePlotsradioButton = QtWidgets.QRadioButton(self.centralwidget)
		self.MultiplePlotsradioButton.setGeometry(QtCore.QRect(150, 140, 121, 23))
		self.MultiplePlotsradioButton.setObjectName("MultiplePlotsradioButton")

		self.VerticalLabel = QtWidgets.QLabel(self.centralwidget)
		self.VerticalLabel.setGeometry(QtCore.QRect(290, 340, 67, 17))
		self.VerticalLabel.setObjectName("VerticalLabel")
		self.VerticalLabel.hide()

		self.VerticalDropDown = QtWidgets.QComboBox(self.centralwidget)
		self.VerticalDropDown.setGeometry(QtCore.QRect(290, 360, 201, 25))
		self.VerticalDropDown.setObjectName("VerticalDropDown")
		item = "Pressure"
		self.VerticalDropDown.addItem(item)
		self.VerticalDropDown.hide()

		mssautoplotGUI.setCentralWidget(self.centralwidget)
		self.menubar = QtWidgets.QMenuBar(mssautoplotGUI)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 521, 22))
		self.menubar.setObjectName("menubar")
		mssautoplotGUI.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(mssautoplotGUI)
		self.statusbar.setObjectName("statusbar")
		mssautoplotGUI.setStatusBar(self.statusbar)
		self.config_path = ""
		self.flightpath = ""

		self.retranslateUi(mssautoplotGUI)
		QtCore.QMetaObject.connectSlotsByName(mssautoplotGUI)

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
		flight_name = str(self.FlightNamelineEdit.text())
		server_url = str(self.ServerUrllineEdit.text())
		layer = str(self.LayerlineEdit.text())
		section = str(self.MapSectioncomboBox.currentText())
		level = str(self.LevellineEdit.text())
		style = str(self.StylelineEdit.text())
		init = self.StartTimedateTimeEdit.dateTime()
		valid = self.EndTimedateTimeEdit.dateTime()
		initpy = init.toPyDateTime()
		validpy = valid.toPyDateTime()
		inittime = datetime.strftime(initpy, '%Y-%m-%dT%H:%M:%S')
		validtime = datetime.strftime(validpy, '%Y-%m-%dT%H:%M:%S')
		if self.no_of_plots == "multiple":
			if interval == 0:
				raise Exception("Interval cannot be zero, please specify another number")
			starttime = inittime
			endtime = validtime
			interval = self.IntervalspinBox.text()
			interval = int(interval)
			mssautoplot.autoplot(cpath=self.config_path, view=self.view, ftrack=self.flightpath, itime="", vtime="", stime=starttime, etime=endtime, intv=interval)
		else:
			if inittime == "2000-01-01T00:00:00":
			 	inittime = ""
			mssautoplot.autoplot(cpath=self.config_path, view=self.view, ftrack=self.flightpath, itime=inittime, vtime=validtime, stime="", etime="", intv=0)
		

	def configFileBrowser(self):
		file_browser = FileBrowserDialog()
		self.config_edit.setText(file_browser.file)
		self.config_path = file_browser.path

	def fileBrowser(self):
		file_browser = FileBrowserDialog()
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

	def retranslateUi(self, mssautoplotGUI):
		_translate = QtCore.QCoreApplication.translate
		mssautoplotGUI.setWindowTitle(_translate("mssautoplotGUI", "mssautoplotGUI GUI"))
		self.ViewLabel.setText(_translate("mssautoplotGUI", "View"))
		self.TopViewradioButton.setText(_translate("mssautoplotGUI", "Top view"))
		self.SideViewradioButton.setText(_translate("mssautoplotGUI", "Side view"))
		self.ConfigPathLabel.setText(_translate("mssautoplotGUI", "Config Path"))
		self.FileNameLabel.setText(_translate("mssautoplotGUI", "Filename"))
		self.FlightNameLabel.setText(_translate("mssautoplotGUI", "Flight name"))
		self.ServerUrlLabel.setText(_translate("mssautoplotGUI", "Server URL"))
		self.InitTimeLabel.setText(_translate("mssautoplotGUI", "Init time"))
		self.MapSectionLabel.setText(_translate("mssautoplotGUI", "Map-section"))
		self.LevelLabel.setText(_translate("mssautoplotGUI", "Level"))
		self.ValidTimeLabel.setText(_translate("mssautoplotGUI", "Valid time"))
		self.RetrieveButton.setText(_translate("mssautoplotGUI", "Retrieve"))
		self.ConfigPathButton.setText(_translate("mssautoplotGUI", "Browse"))
		self.FileNameButton.setText(_translate("mssautoplotGUI", "Browse"))
		self.LayerLabel.setText(_translate("mssautoplotGUI", "Layer"))
		self.StyleLabel.setText(_translate("mssautoplotGUI", "Style"))
		self.StartTimedateTimeEdit.setDisplayFormat(_translate("mssautoplotGUI", "dd/MM/yy hh:mm UTC"))
		self.EndTimedateTimeEdit.setDisplayFormat(_translate("mssautoplotGUI", "dd/MM/yy hh:mm UTC"))
		self.IntervalLabel.setText(_translate("mssautoplotGUI", "Interval (In hours)"))
		self.NoOfPlotsLabel.setText(_translate("mssautoplotGUI", "No. of Plots"))
		self.SinglePlotradioButton.setText(_translate("mssautoplotGUI", "Single Plot"))
		self.MultiplePlotsradioButton.setText(_translate("mssautoplotGUI", "Multiple Plots"))
		self.VerticalLabel.setText(_translate("mssautoplotGUI", "Vertical"))
		

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
		self.path, _ = QFileDialog.getOpenFileName(self,"mssautoplotGUI- File browser", "","All Files (*);;Python Files (*.py)", options=options)
		if self.path:
			self.file = os.path.split(self.path)[1]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mssautoplotGUI = QtWidgets.QMainWindow()
    ui = Ui_mssautoplot()
    ui.setupUi(mssautoplotGUI)
    mssautoplotGUI.show()
    sys.exit(app.exec_())
