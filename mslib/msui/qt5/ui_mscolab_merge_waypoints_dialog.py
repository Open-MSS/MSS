# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_merge_waypoints_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MergeWaypointsDialog(object):
    def setupUi(self, MergeWaypointsDialog):
        MergeWaypointsDialog.setObjectName("MergeWaypointsDialog")
        MergeWaypointsDialog.resize(995, 618)
        self.gridLayout = QtWidgets.QGridLayout(MergeWaypointsDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 8)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.label_4 = QtWidgets.QLabel(MergeWaypointsDialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(MergeWaypointsDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.localWaypointsTable = QtWidgets.QTableView(MergeWaypointsDialog)
        self.localWaypointsTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.localWaypointsTable.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.localWaypointsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.localWaypointsTable.setObjectName("localWaypointsTable")
        self.verticalLayout.addWidget(self.localWaypointsTable)
        self.overwriteBtn = QtWidgets.QPushButton(MergeWaypointsDialog)
        self.overwriteBtn.setEnabled(True)
        self.overwriteBtn.setAutoDefault(False)
        self.overwriteBtn.setObjectName("overwriteBtn")
        self.verticalLayout.addWidget(self.overwriteBtn)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(MergeWaypointsDialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.serverWaypointsTable = QtWidgets.QTableView(MergeWaypointsDialog)
        self.serverWaypointsTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.serverWaypointsTable.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.serverWaypointsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.serverWaypointsTable.setObjectName("serverWaypointsTable")
        self.verticalLayout_2.addWidget(self.serverWaypointsTable)
        self.keepServerBtn = QtWidgets.QPushButton(MergeWaypointsDialog)
        self.keepServerBtn.setAutoDefault(False)
        self.keepServerBtn.setObjectName("keepServerBtn")
        self.verticalLayout_2.addWidget(self.keepServerBtn)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_3 = QtWidgets.QLabel(MergeWaypointsDialog)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        self.mergedWaypointsTable = QtWidgets.QTableView(MergeWaypointsDialog)
        self.mergedWaypointsTable.setAcceptDrops(True)
        self.mergedWaypointsTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.mergedWaypointsTable.setDragEnabled(True)
        self.mergedWaypointsTable.setDragDropOverwriteMode(False)
        self.mergedWaypointsTable.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.mergedWaypointsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.mergedWaypointsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.mergedWaypointsTable.setObjectName("mergedWaypointsTable")
        self.verticalLayout_3.addWidget(self.mergedWaypointsTable)
        self.saveBtn = QtWidgets.QPushButton(MergeWaypointsDialog)
        self.saveBtn.setObjectName("saveBtn")
        self.verticalLayout_3.addWidget(self.saveBtn)
        self.horizontalLayout_3.addLayout(self.verticalLayout_3)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 6)
        self.horizontalLayout_3.setStretch(2, 1)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.gridLayout.addLayout(self.verticalLayout_4, 0, 0, 1, 1)

        self.retranslateUi(MergeWaypointsDialog)
        QtCore.QMetaObject.connectSlotsByName(MergeWaypointsDialog)

    def retranslateUi(self, MergeWaypointsDialog):
        _translate = QtCore.QCoreApplication.translate
        MergeWaypointsDialog.setWindowTitle(_translate("MergeWaypointsDialog", "Save Waypoints to Server"))
        self.label_4.setText(_translate("MergeWaypointsDialog", "Select which waypoints you want to keep"))
        self.label.setText(_translate("MergeWaypointsDialog", "Your Local File Waypoints"))
        self.overwriteBtn.setToolTip(_translate("MergeWaypointsDialog", "Overwrite server data with local waypoints"))
        self.overwriteBtn.setText(_translate("MergeWaypointsDialog", "Overwrite with local waypoints"))
        self.label_2.setText(_translate("MergeWaypointsDialog", "Waypoints on server"))
        self.keepServerBtn.setToolTip(_translate("MergeWaypointsDialog", "Keep the server waypoints"))
        self.keepServerBtn.setText(_translate("MergeWaypointsDialog", "Keep Server Waypoints"))
        self.label_3.setText(_translate("MergeWaypointsDialog", "New Waypoints"))
        self.saveBtn.setToolTip(_translate("MergeWaypointsDialog", "Save the new merged waypoints to the server"))
        self.saveBtn.setText(_translate("MergeWaypointsDialog", "Save new waypoints on server"))
