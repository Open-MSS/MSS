# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_tableview_window.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TableViewWindow(object):
    def setupUi(self, TableViewWindow):
        TableViewWindow.setObjectName("TableViewWindow")
        TableViewWindow.resize(1254, 472)
        TableViewWindow.setMinimumSize(QtCore.QSize(0, 0))
        self.centralwidget = QtWidgets.QWidget(TableViewWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWayPoints = QtWidgets.QTableView(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.tableWayPoints.setFont(font)
        self.tableWayPoints.setAlternatingRowColors(True)
        self.tableWayPoints.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableWayPoints.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWayPoints.setObjectName("tableWayPoints")
        self.verticalLayout.addWidget(self.tableWayPoints)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btViewPerformance = QtWidgets.QPushButton(self.centralwidget)
        self.btViewPerformance.setEnabled(True)
        self.btViewPerformance.setCheckable(True)
        self.btViewPerformance.setChecked(False)
        self.btViewPerformance.setObjectName("btViewPerformance")
        self.horizontalLayout.addWidget(self.btViewPerformance)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cbTools = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbTools.sizePolicy().hasHeightForWidth())
        self.cbTools.setSizePolicy(sizePolicy)
        self.cbTools.setBaseSize(QtCore.QSize(0, 0))
        self.cbTools.setObjectName("cbTools")
        self.cbTools.addItem("")
        self.horizontalLayout.addWidget(self.cbTools)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.btAddWayPointToFlightTrack = QtWidgets.QPushButton(self.centralwidget)
        self.btAddWayPointToFlightTrack.setObjectName("btAddWayPointToFlightTrack")
        self.horizontalLayout.addWidget(self.btAddWayPointToFlightTrack)
        self.btDeleteWayPoint = QtWidgets.QPushButton(self.centralwidget)
        self.btDeleteWayPoint.setObjectName("btDeleteWayPoint")
        self.horizontalLayout.addWidget(self.btDeleteWayPoint)
        self.btInvertDirection = QtWidgets.QPushButton(self.centralwidget)
        self.btInvertDirection.setMinimumSize(QtCore.QSize(100, 0))
        self.btInvertDirection.setObjectName("btInvertDirection")
        self.horizontalLayout.addWidget(self.btInvertDirection)
        self.verticalLayout.addLayout(self.horizontalLayout)
        TableViewWindow.setCentralWidget(self.centralwidget)
        self.actionClose = QtWidgets.QAction(TableViewWindow)
        self.actionClose.setObjectName("actionClose")
        self.actionFlightPerformance_old = QtWidgets.QAction(TableViewWindow)
        self.actionFlightPerformance_old.setObjectName("actionFlightPerformance_old")
        self.actionFlightPerformance = QtWidgets.QAction(TableViewWindow)
        self.actionFlightPerformance.setObjectName("actionFlightPerformance")

        self.retranslateUi(TableViewWindow)
        self.actionClose.triggered.connect(TableViewWindow.close)
        QtCore.QMetaObject.connectSlotsByName(TableViewWindow)

    def retranslateUi(self, TableViewWindow):
        _translate = QtCore.QCoreApplication.translate
        TableViewWindow.setWindowTitle(_translate("TableViewWindow", "Table View - Mission Support System"))
        self.btViewPerformance.setText(_translate("TableViewWindow", "performance settings"))
        self.cbTools.setItemText(0, _translate("TableViewWindow", "(select to open control)"))
        self.label.setText(_translate("TableViewWindow", "Waypoints:"))
        self.btAddWayPointToFlightTrack.setText(_translate("TableViewWindow", "insert"))
        self.btDeleteWayPoint.setText(_translate("TableViewWindow", "delete selected"))
        self.btInvertDirection.setText(_translate("TableViewWindow", "reverse"))
        self.actionClose.setText(_translate("TableViewWindow", "E&xit Module"))
        self.actionClose.setShortcut(_translate("TableViewWindow", "Ctrl+X"))
        self.actionFlightPerformance_old.setText(_translate("TableViewWindow", "Flight Performance (first version, depracated)"))
        self.actionFlightPerformance.setText(_translate("TableViewWindow", "Flight &Performance"))

