# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_tableview_window.ui'
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


class Ui_TableViewWindow(object):
    def setupUi(self, TableViewWindow):
        TableViewWindow.setObjectName(_fromUtf8("TableViewWindow"))
        TableViewWindow.resize(1254, 472)
        TableViewWindow.setMinimumSize(QtCore.QSize(0, 0))
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
        self.btViewPerformance.setCheckable(True)
        self.btViewPerformance.setChecked(False)
        self.btViewPerformance.setObjectName(_fromUtf8("btViewPerformance"))
        self.horizontalLayout.addWidget(self.btViewPerformance)
        self.lblRemainingRange = QtGui.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblRemainingRange.setFont(font)
        self.lblRemainingRange.setObjectName(_fromUtf8("lblRemainingRange"))
        self.horizontalLayout.addWidget(self.lblRemainingRange)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.btAddWayPointToFlightTrack = QtGui.QPushButton(self.centralwidget)
        self.btAddWayPointToFlightTrack.setObjectName(_fromUtf8("btAddWayPointToFlightTrack"))
        self.horizontalLayout.addWidget(self.btAddWayPointToFlightTrack)
        self.btDeleteWayPoint = QtGui.QPushButton(self.centralwidget)
        self.btDeleteWayPoint.setObjectName(_fromUtf8("btDeleteWayPoint"))
        self.horizontalLayout.addWidget(self.btDeleteWayPoint)
        self.btInvertDirection = QtGui.QPushButton(self.centralwidget)
        self.btInvertDirection.setMinimumSize(QtCore.QSize(100, 0))
        self.btInvertDirection.setObjectName(_fromUtf8("btInvertDirection"))
        self.horizontalLayout.addWidget(self.btInvertDirection)
        self.verticalLayout.addLayout(self.horizontalLayout)
        TableViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TableViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1254, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menu_File = QtGui.QMenu(self.menubar)
        self.menu_File.setObjectName(_fromUtf8("menu_File"))
        self.menu_Controls = QtGui.QMenu(self.menubar)
        self.menu_Controls.setObjectName(_fromUtf8("menu_Controls"))
        TableViewWindow.setMenuBar(self.menubar)
        self.actionClose = QtGui.QAction(TableViewWindow)
        self.actionClose.setObjectName(_fromUtf8("actionClose"))
        self.actionFlightPerformance_old = QtGui.QAction(TableViewWindow)
        self.actionFlightPerformance_old.setObjectName(_fromUtf8("actionFlightPerformance_old"))
        self.actionFlightPerformance = QtGui.QAction(TableViewWindow)
        self.actionFlightPerformance.setObjectName(_fromUtf8("actionFlightPerformance"))
        self.menu_File.addAction(self.actionClose)
        self.menu_Controls.addAction(self.actionFlightPerformance)
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Controls.menuAction())

        self.retranslateUi(TableViewWindow)
        QtCore.QObject.connect(self.actionClose, QtCore.SIGNAL(_fromUtf8("activated()")), TableViewWindow.close)
        QtCore.QMetaObject.connectSlotsByName(TableViewWindow)

    def retranslateUi(self, TableViewWindow):
        TableViewWindow.setWindowTitle(_translate("TableViewWindow", "Table View - DLR/IPA Mission Support", None))
        self.btViewPerformance.setText(_translate("TableViewWindow", "view performance", None))
        self.lblRemainingRange.setText(_translate("TableViewWindow", "TextLabel", None))
        self.label.setText(_translate("TableViewWindow", "Waypoints:", None))
        self.btAddWayPointToFlightTrack.setText(_translate("TableViewWindow", "insert", None))
        self.btDeleteWayPoint.setText(_translate("TableViewWindow", "delete selected", None))
        self.btInvertDirection.setText(_translate("TableViewWindow", "reverse", None))
        self.menu_File.setTitle(_translate("TableViewWindow", "&File", None))
        self.menu_Controls.setTitle(_translate("TableViewWindow", "&Service Controls", None))
        self.actionClose.setText(_translate("TableViewWindow", "E&xit Module", None))
        self.actionClose.setShortcut(_translate("TableViewWindow", "Ctrl+X", None))
        self.actionFlightPerformance_old.setText(
            _translate("TableViewWindow", "Flight Performance (first version, depracated)", None))
        self.actionFlightPerformance.setText(_translate("TableViewWindow", "Flight &Performance", None))
