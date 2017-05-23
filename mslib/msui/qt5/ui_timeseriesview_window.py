# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_timeseriesview_window.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from builtins import object
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TimeSeriesViewWindow(object):
    def setupUi(self, TimeSeriesViewWindow):
        TimeSeriesViewWindow.setObjectName("TimeSeriesViewWindow")
        TimeSeriesViewWindow.resize(648, 738)
        self.centralwidget = QtWidgets.QWidget(TimeSeriesViewWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mpl = MplTimeSeriesViewWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.mpl.setObjectName("mpl")
        self.horizontalLayout.addWidget(self.mpl)
        TimeSeriesViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(TimeSeriesViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 648, 26))
        self.menubar.setObjectName("menubar")
        TimeSeriesViewWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(TimeSeriesViewWindow)
        self.statusbar.setObjectName("statusbar")
        TimeSeriesViewWindow.setStatusBar(self.statusbar)

        self.retranslateUi(TimeSeriesViewWindow)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesViewWindow)

    def retranslateUi(self, TimeSeriesViewWindow):
        _translate = QtCore.QCoreApplication.translate
        TimeSeriesViewWindow.setWindowTitle(_translate("TimeSeriesViewWindow", "Time Series View - Mission Support System"))

from mslib.msui.mpl_qtwidget import MplTimeSeriesViewWidget
