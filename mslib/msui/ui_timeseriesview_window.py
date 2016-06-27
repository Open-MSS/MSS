# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_timeseriesview_window.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_TimeSeriesViewWindow(object):
    def setupUi(self, TimeSeriesViewWindow):
        TimeSeriesViewWindow.setObjectName(_fromUtf8("TimeSeriesViewWindow"))
        TimeSeriesViewWindow.resize(648, 738)
        self.centralwidget = QtGui.QWidget(TimeSeriesViewWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.mpl = MplTimeSeriesViewWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.mpl.setObjectName(_fromUtf8("mpl"))
        self.horizontalLayout.addWidget(self.mpl)
        TimeSeriesViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TimeSeriesViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 648, 26))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        TimeSeriesViewWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(TimeSeriesViewWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        TimeSeriesViewWindow.setStatusBar(self.statusbar)

        self.retranslateUi(TimeSeriesViewWindow)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesViewWindow)

    def retranslateUi(self, TimeSeriesViewWindow):
        TimeSeriesViewWindow.setWindowTitle(_translate("TimeSeriesViewWindow", "Time Series View - Mission Support System", None))

from mpl_qtwidget import MplTimeSeriesViewWidget
