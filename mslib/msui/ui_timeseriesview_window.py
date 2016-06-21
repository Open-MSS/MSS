# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_timeseriesview_window.ui'
#
# Created: Wed Sep  1 12:22:02 2010
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

from mpl_qtwidget import MplTimeSeriesViewWidget


class Ui_TimeSeriesViewWindow(object):
    def setupUi(self, TimeSeriesViewWindow):
        TimeSeriesViewWindow.setObjectName("TimeSeriesViewWindow")
        TimeSeriesViewWindow.resize(648, 738)
        self.centralwidget = QtGui.QWidget(TimeSeriesViewWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mpl = MplTimeSeriesViewWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setCursor(QtCore.Qt.CrossCursor)
        self.mpl.setObjectName("mpl")
        self.horizontalLayout.addWidget(self.mpl)
        TimeSeriesViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TimeSeriesViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 648, 26))
        self.menubar.setObjectName("menubar")
        TimeSeriesViewWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(TimeSeriesViewWindow)
        self.statusbar.setObjectName("statusbar")
        TimeSeriesViewWindow.setStatusBar(self.statusbar)

        self.retranslateUi(TimeSeriesViewWindow)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesViewWindow)

    def retranslateUi(self, TimeSeriesViewWindow):
        TimeSeriesViewWindow.setWindowTitle(
            QtGui.QApplication.translate("TimeSeriesViewWindow", "Time Series View - DLR/IPA Mission Support", None,
                                         QtGui.QApplication.UnicodeUTF8))
