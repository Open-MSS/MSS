# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_tableview_window.ui'
#
# Created by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_TableViewWindow(object):
    def setupUi(self, TableViewWindow):
        TableViewWindow.setObjectName(_fromUtf8("TableViewWindow"))
        TableViewWindow.resize(1254, 472)
        TableViewWindow.setMinimumSize(QtCore.QSize(0, 0))
        TableViewWindow.setWindowTitle(QtGui.QApplication.translate("TableViewWindow", "Table View - DLR/IPA Mission Support", None, QtGui.QApplication.UnicodeUTF8))
        self.centralwidget = QtGui.QWidget(TableViewWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tableWayPoints = QtGui.QTableView(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.tableWayPoints.setFont(font)
        self.tableWayPoints.setAlternatingRowColors(True)
        self.tableWayPoints.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableWayPoints.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableWayPoints.setObjectName(_fromUtf8("tableWayPoints"))
        self.verticalLayout.addWidget(self.tableWayPoints)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btViewPerformance = QtGui.QPushButton(self.centralwidget)
        self.btViewPerformance.setEnabled(True)
        self.btViewPerformance.setText(QtGui.QApplication.translate("TableViewWindow", "view performance", None, QtGui.QApplication.UnicodeUTF8))
        self.btViewPerformance.setCheckable(True)
        self.btViewPerformance.setChecked(False)
        self.btViewPerformance.setObjectName(_fromUtf8("btViewPerformance"))
        self.horizontalLayout.addWidget(self.btViewPerformance)
        self.lblRemainingRange = QtGui.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblRemainingRange.setFont(font)
        self.lblRemainingRange.setText(QtGui.QApplication.translate("TableViewWindow", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lblRemainingRange.setObjectName(_fromUtf8("lblRemainingRange"))
        self.horizontalLayout.addWidget(self.lblRemainingRange)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setText(QtGui.QApplication.translate("TableViewWindow", "Waypoints:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.btAddWayPointToFlightTrack = QtGui.QPushButton(self.centralwidget)
        self.btAddWayPointToFlightTrack.setText(QtGui.QApplication.translate("TableViewWindow", "insert", None, QtGui.QApplication.UnicodeUTF8))
        self.btAddWayPointToFlightTrack.setObjectName(_fromUtf8("btAddWayPointToFlightTrack"))
        self.horizontalLayout.addWidget(self.btAddWayPointToFlightTrack)
        self.btDeleteWayPoint = QtGui.QPushButton(self.centralwidget)
        self.btDeleteWayPoint.setText(QtGui.QApplication.translate("TableViewWindow", "delete selected", None, QtGui.QApplication.UnicodeUTF8))
        self.btDeleteWayPoint.setObjectName(_fromUtf8("btDeleteWayPoint"))
        self.horizontalLayout.addWidget(self.btDeleteWayPoint)
        self.verticalLayout.addLayout(self.horizontalLayout)
        TableViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TableViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1254, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menu_File = QtGui.QMenu(self.menubar)
        self.menu_File.setTitle(QtGui.QApplication.translate("TableViewWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_File.setObjectName(_fromUtf8("menu_File"))
        self.menu_Controls = QtGui.QMenu(self.menubar)
        self.menu_Controls.setTitle(QtGui.QApplication.translate("TableViewWindow", "&Service Controls", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Controls.setObjectName(_fromUtf8("menu_Controls"))
        TableViewWindow.setMenuBar(self.menubar)
        self.actionClose = QtGui.QAction(TableViewWindow)
        self.actionClose.setText(QtGui.QApplication.translate("TableViewWindow", "E&xit Module", None, QtGui.QApplication.UnicodeUTF8))
        self.actionClose.setShortcut(QtGui.QApplication.translate("TableViewWindow", "Ctrl+X", None, QtGui.QApplication.UnicodeUTF8))
        self.actionClose.setObjectName(_fromUtf8("actionClose"))
        self.actionFlightPerformance_old = QtGui.QAction(TableViewWindow)
        self.actionFlightPerformance_old.setText(QtGui.QApplication.translate("TableViewWindow", "Flight Performance (first version, depracated)", None, QtGui.QApplication.UnicodeUTF8))
        self.actionFlightPerformance_old.setObjectName(_fromUtf8("actionFlightPerformance_old"))
        self.actionFlightPerformance = QtGui.QAction(TableViewWindow)
        self.actionFlightPerformance.setText(QtGui.QApplication.translate("TableViewWindow", "Flight &Performance", None, QtGui.QApplication.UnicodeUTF8))
        self.actionFlightPerformance.setObjectName(_fromUtf8("actionFlightPerformance"))
        self.menu_File.addAction(self.actionClose)
        self.menu_Controls.addAction(self.actionFlightPerformance)
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Controls.menuAction())

        self.retranslateUi(TableViewWindow)
        QtCore.QObject.connect(self.actionClose, QtCore.SIGNAL(_fromUtf8("activated()")), TableViewWindow.close)
        QtCore.QMetaObject.connectSlotsByName(TableViewWindow)

    def retranslateUi(self, TableViewWindow):
        pass

