# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mssautoplot_gui.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!



from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLineEdit


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
		self.ConfigPathlineEdit = QLineEdit(self.centralwidget)
		self.ConfigPathlineEdit.setGeometry(QtCore.QRect(40, 220, 151, 25))
		self.ConfigPathlineEdit.setObjectName("ConfigPathlineEdit")
		self.FileNameLabel = QtWidgets.QLabel(self.centralwidget)
		self.FileNameLabel.setGeometry(QtCore.QRect(40, 270, 67, 17))
		self.FileNameLabel.setObjectName("FileNameLabel")
		self.FlightNameLabel = QtWidgets.QLabel(self.centralwidget)
		self.FlightNameLabel.setGeometry(QtCore.QRect(290, 200, 81, 16))
		self.FlightNameLabel.setObjectName("FlightNameLabel")
		self.ServerUrlLabel = QtWidgets.QLabel(self.centralwidget)
		self.ServerUrlLabel.setGeometry(QtCore.QRect(40, 340, 91, 17))
		self.ServerUrlLabel.setObjectName("ServerUrlLabel")
		self.InitTimeLabel = QtWidgets.QLabel(self.centralwidget)
		self.InitTimeLabel.setGeometry(QtCore.QRect(40, 480, 67, 17))
		self.InitTimeLabel.setObjectName("InitTimeLabel")
		self.MapSectionLabel = QtWidgets.QLabel(self.centralwidget)
		self.MapSectionLabel.setGeometry(QtCore.QRect(290, 270, 91, 17))
		self.MapSectionLabel.setObjectName("MapSectionLabel")
		self.LevelLabel = QtWidgets.QLabel(self.centralwidget)
		self.LevelLabel.setGeometry(QtCore.QRect(290, 340, 67, 17))
		self.LevelLabel.setObjectName("LevelLabel")
		self.ValidTimeLabel = QtWidgets.QLabel(self.centralwidget)
		self.ValidTimeLabel.setGeometry(QtCore.QRect(290, 480, 67, 17))
		self.ValidTimeLabel.setObjectName("ValidTimeLabel")
		self.MapSectioncomboBox = QtWidgets.QComboBox(self.centralwidget)
		self.MapSectioncomboBox.setGeometry(QtCore.QRect(290, 290, 201, 25))
		self.MapSectioncomboBox.setObjectName("MapSectioncomboBox")
		self.LevellineEdit = QLineEdit(self.centralwidget)
		self.LevellineEdit.setGeometry(QtCore.QRect(290, 360, 201, 25))
		self.LevellineEdit.setObjectName("LevellineEdit")
		self.RetrieveButton = QtWidgets.QPushButton(self.centralwidget)
		self.RetrieveButton.setGeometry(QtCore.QRect(400, 580, 89, 31))
		self.ConfigPathButton = QtWidgets.QPushButton(self.centralwidget)
		self.ConfigPathButton.setGeometry(QtCore.QRect(190, 220, 51, 25))
		self.FileNamelineEdit = QLineEdit(self.centralwidget)
		self.FileNamelineEdit.setGeometry(QtCore.QRect(40, 290, 151, 25))
		self.FileNamelineEdit.setObjectName("FileNamelineEdit")
		self.FileNameButton = QtWidgets.QPushButton(self.centralwidget)
		self.FileNameButton.setGeometry(QtCore.QRect(190, 290, 51, 25))
		self.ServerUrllineEdit = QLineEdit(self.centralwidget)
		self.ServerUrllineEdit.setGeometry(QtCore.QRect(40, 360, 201, 25))
		self.ServerUrllineEdit.setObjectName("ServerUrllineEdit")
		self.FlightNamelineEdit = QLineEdit(self.centralwidget)
		self.FlightNamelineEdit.setGeometry(QtCore.QRect(290, 220, 201, 25))
		self.FlightNamelineEdit.setObjectName("FlightNmaelineEdit")
		self.LayerLabel = QtWidgets.QLabel(self.centralwidget)
		self.LayerLabel.setGeometry(QtCore.QRect(40, 410, 67, 17))
		self.LayerLabel.setObjectName("LayerLabel")
		self.StyleLabel = QtWidgets.QLabel(self.centralwidget)
		self.StyleLabel.setGeometry(QtCore.QRect(290, 410, 67, 17))
		self.StyleLabel.setObjectName("StyleLabel")
		self.LayerlineEdit = QLineEdit(self.centralwidget)
		self.LayerlineEdit.setGeometry(QtCore.QRect(40, 430, 201, 25))
		self.LayerlineEdit.setObjectName("LayerlineEdit")
		self.StylelineEdit = QLineEdit(self.centralwidget)
		self.StylelineEdit.setGeometry(QtCore.QRect(290, 430, 201, 25))
		self.StylelineEdit.setObjectName("StylelineEdit")
		self.StartTimedateTimeEdit = QtWidgets.QDateTimeEdit(self.centralwidget)
		self.StartTimedateTimeEdit.setGeometry(QtCore.QRect(40, 500, 201, 26))
		self.StartTimedateTimeEdit.setObjectName("StartTimedateTimeEdit")
		self.EndTimedateTimeEdit = QtWidgets.QDateTimeEdit(self.centralwidget)
		self.EndTimedateTimeEdit.setGeometry(QtCore.QRect(290, 500, 201, 26))
		self.EndTimedateTimeEdit.setObjectName("EndTimedateTimeEdit")
		self.IntervalspinBox = QtWidgets.QSpinBox(self.centralwidget)
		self.IntervalspinBox.setGeometry(QtCore.QRect(40, 570, 201, 26))
		self.IntervalspinBox.setObjectName("IntervalspinBox")
		self.IntervalLabel = QtWidgets.QLabel(self.centralwidget)
		self.IntervalLabel.setGeometry(QtCore.QRect(40, 550, 121, 17))
		self.IntervalLabel.setObjectName("IntervalLabel")
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
		self.VerticalDropDown = QtWidgets.QComboBox(self.centralwidget)
		self.VerticalDropDown.setGeometry(QtCore.QRect(290, 360, 201, 25))
		self.VerticalDropDown.setObjectName("VerticalDropDown")
		item = "Pressure"
		self.VerticalDropDown.addItem(item)
		mssautoplotGUI.setCentralWidget(self.centralwidget)
		self.menubar = QtWidgets.QMenuBar(mssautoplotGUI)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 521, 22))
		self.menubar.setObjectName("menubar")
		mssautoplotGUI.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(mssautoplotGUI)
		self.statusbar.setObjectName("statusbar")
		mssautoplotGUI.setStatusBar(self.statusbar)
		self.retranslateUi(mssautoplotGUI)
		QtCore.QMetaObject.connectSlotsByName(mssautoplotGUI)

	

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
 