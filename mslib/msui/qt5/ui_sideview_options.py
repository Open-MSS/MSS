# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_sideview_options.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SideViewOptionsDialog(object):
    def setupUi(self, SideViewOptionsDialog):
        SideViewOptionsDialog.setObjectName("SideViewOptionsDialog")
        SideViewOptionsDialog.resize(538, 650)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(SideViewOptionsDialog)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.groupBox = QtWidgets.QGroupBox(SideViewOptionsDialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_6.setContentsMargins(-1, -1, -1, 7)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.sbPbot = QtWidgets.QDoubleSpinBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sbPbot.sizePolicy().hasHeightForWidth())
        self.sbPbot.setSizePolicy(sizePolicy)
        self.sbPbot.setPrefix("")
        self.sbPbot.setMinimum(0.0)
        self.sbPbot.setMaximum(2132.0)
        self.sbPbot.setProperty("value", 1050.0)
        self.sbPbot.setObjectName("sbPbot")
        self.horizontalLayout.addWidget(self.sbPbot)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.sbPtop = QtWidgets.QDoubleSpinBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sbPtop.sizePolicy().hasHeightForWidth())
        self.sbPtop.setSizePolicy(sizePolicy)
        self.sbPtop.setMinimum(0.0)
        self.sbPtop.setMaximum(2132.0)
        self.sbPtop.setProperty("value", 200.0)
        self.sbPtop.setObjectName("sbPtop")
        self.horizontalLayout.addWidget(self.sbPtop)
        self.verticalLayout_6.addLayout(self.horizontalLayout)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.cbVerticalAxis = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbVerticalAxis.sizePolicy().hasHeightForWidth())
        self.cbVerticalAxis.setSizePolicy(sizePolicy)
        self.cbVerticalAxis.setObjectName("cbVerticalAxis")
        self.cbVerticalAxis.addItem("")
        self.cbVerticalAxis.addItem("")
        self.cbVerticalAxis.addItem("")
        self.gridLayout.addWidget(self.cbVerticalAxis, 0, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.cbVerticalAxis2 = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbVerticalAxis2.sizePolicy().hasHeightForWidth())
        self.cbVerticalAxis2.setSizePolicy(sizePolicy)
        self.cbVerticalAxis2.setObjectName("cbVerticalAxis2")
        self.cbVerticalAxis2.addItem("")
        self.cbVerticalAxis2.addItem("")
        self.cbVerticalAxis2.addItem("")
        self.cbVerticalAxis2.addItem("")
        self.gridLayout.addWidget(self.cbVerticalAxis2, 1, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 1)
        self.verticalLayout_6.addLayout(self.gridLayout)
        self.verticalLayout_4.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(SideViewOptionsDialog)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.cbDrawFlightLevels = QtWidgets.QCheckBox(self.groupBox_2)
        self.cbDrawFlightLevels.setObjectName("cbDrawFlightLevels")
        self.verticalLayout_2.addWidget(self.cbDrawFlightLevels)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tableWidget = QtWidgets.QTableWidget(self.groupBox_2)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        self.horizontalLayout_3.addWidget(self.tableWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.btAdd = QtWidgets.QPushButton(self.groupBox_2)
        self.btAdd.setObjectName("btAdd")
        self.verticalLayout.addWidget(self.btAdd)
        self.btDelete = QtWidgets.QPushButton(self.groupBox_2)
        self.btDelete.setObjectName("btDelete")
        self.verticalLayout.addWidget(self.btDelete)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.verticalLayout_4.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(SideViewOptionsDialog)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.cbDrawFlightTrack = QtWidgets.QCheckBox(self.groupBox_3)
        self.cbDrawFlightTrack.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbDrawFlightTrack.sizePolicy().hasHeightForWidth())
        self.cbDrawFlightTrack.setSizePolicy(sizePolicy)
        self.cbDrawFlightTrack.setMinimumSize(QtCore.QSize(140, 0))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(20, 19, 18))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(20, 19, 18))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(20, 19, 18))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(20, 19, 18))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(173, 173, 173))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.cbDrawFlightTrack.setPalette(palette)
        self.cbDrawFlightTrack.setChecked(True)
        self.cbDrawFlightTrack.setObjectName("cbDrawFlightTrack")
        self.horizontalLayout_4.addWidget(self.cbDrawFlightTrack)
        self.btVerticesColour = QtWidgets.QPushButton(self.groupBox_3)
        self.btVerticesColour.setMinimumSize(QtCore.QSize(140, 0))
        self.btVerticesColour.setObjectName("btVerticesColour")
        self.horizontalLayout_4.addWidget(self.btVerticesColour)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.cbDrawMarker = QtWidgets.QCheckBox(self.groupBox_3)
        self.cbDrawMarker.setMinimumSize(QtCore.QSize(140, 0))
        self.cbDrawMarker.setObjectName("cbDrawMarker")
        self.horizontalLayout_8.addWidget(self.cbDrawMarker)
        self.btWaypointsColour = QtWidgets.QPushButton(self.groupBox_3)
        self.btWaypointsColour.setMinimumSize(QtCore.QSize(140, 0))
        self.btWaypointsColour.setObjectName("btWaypointsColour")
        self.horizontalLayout_8.addWidget(self.btWaypointsColour)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem2)
        self.verticalLayout_3.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.cbFillFlightTrack = QtWidgets.QCheckBox(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbFillFlightTrack.sizePolicy().hasHeightForWidth())
        self.cbFillFlightTrack.setSizePolicy(sizePolicy)
        self.cbFillFlightTrack.setMinimumSize(QtCore.QSize(140, 0))
        self.cbFillFlightTrack.setObjectName("cbFillFlightTrack")
        self.horizontalLayout_5.addWidget(self.cbFillFlightTrack)
        self.btFillColour = QtWidgets.QPushButton(self.groupBox_3)
        self.btFillColour.setMinimumSize(QtCore.QSize(140, 0))
        self.btFillColour.setObjectName("btFillColour")
        self.horizontalLayout_5.addWidget(self.btFillColour)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem3)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.cbLabelFlightTrack = QtWidgets.QCheckBox(self.groupBox_3)
        self.cbLabelFlightTrack.setObjectName("cbLabelFlightTrack")
        self.horizontalLayout_6.addWidget(self.cbLabelFlightTrack)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.cbVerticalLines = QtWidgets.QCheckBox(self.groupBox_3)
        self.cbVerticalLines.setObjectName("cbVerticalLines")
        self.horizontalLayout_7.addWidget(self.cbVerticalLines)
        self.verticalLayout_3.addLayout(self.horizontalLayout_7)
        self.verticalLayout_4.addWidget(self.groupBox_3)
        self.groupBox_4 = QtWidgets.QGroupBox(SideViewOptionsDialog)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.cbDrawCeiling = QtWidgets.QCheckBox(self.groupBox_4)
        self.cbDrawCeiling.setObjectName("cbDrawCeiling")
        self.horizontalLayout_2.addWidget(self.cbDrawCeiling)
        self.btCeilingColour = QtWidgets.QPushButton(self.groupBox_4)
        self.btCeilingColour.setMinimumSize(QtCore.QSize(140, 0))
        self.btCeilingColour.setObjectName("btCeilingColour")
        self.horizontalLayout_2.addWidget(self.btCeilingColour)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label = QtWidgets.QLabel(self.groupBox_4)
        self.label.setObjectName("label")
        self.gridLayout_4.addWidget(self.label, 2, 0, 1, 1)
        self.cbtitlesize = QtWidgets.QComboBox(self.groupBox_4)
        self.cbtitlesize.setObjectName("cbtitlesize")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.cbtitlesize.addItem("")
        self.gridLayout_4.addWidget(self.cbtitlesize, 2, 1, 1, 1)
        self.cbaxessize = QtWidgets.QComboBox(self.groupBox_4)
        self.cbaxessize.setObjectName("cbaxessize")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.cbaxessize.addItem("")
        self.gridLayout_4.addWidget(self.cbaxessize, 2, 3, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.groupBox_4)
        self.label_7.setObjectName("label_7")
        self.gridLayout_4.addWidget(self.label_7, 2, 2, 1, 1)
        self.verticalLayout_5.addLayout(self.gridLayout_4)
        self.verticalLayout_4.addWidget(self.groupBox_4)
        self.buttonBox = QtWidgets.QDialogButtonBox(SideViewOptionsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_4.addWidget(self.buttonBox)

        self.retranslateUi(SideViewOptionsDialog)
        self.buttonBox.accepted.connect(SideViewOptionsDialog.accept)
        self.buttonBox.rejected.connect(SideViewOptionsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SideViewOptionsDialog)
        SideViewOptionsDialog.setTabOrder(self.sbPbot, self.sbPtop)
        SideViewOptionsDialog.setTabOrder(self.sbPtop, self.cbVerticalAxis)
        SideViewOptionsDialog.setTabOrder(self.cbVerticalAxis, self.cbVerticalAxis2)
        SideViewOptionsDialog.setTabOrder(self.cbVerticalAxis2, self.cbDrawFlightLevels)
        SideViewOptionsDialog.setTabOrder(self.cbDrawFlightLevels, self.tableWidget)
        SideViewOptionsDialog.setTabOrder(self.tableWidget, self.btAdd)
        SideViewOptionsDialog.setTabOrder(self.btAdd, self.btDelete)
        SideViewOptionsDialog.setTabOrder(self.btDelete, self.cbDrawFlightTrack)
        SideViewOptionsDialog.setTabOrder(self.cbDrawFlightTrack, self.btVerticesColour)
        SideViewOptionsDialog.setTabOrder(self.btVerticesColour, self.cbFillFlightTrack)
        SideViewOptionsDialog.setTabOrder(self.cbFillFlightTrack, self.btFillColour)
        SideViewOptionsDialog.setTabOrder(self.btFillColour, self.cbLabelFlightTrack)
        SideViewOptionsDialog.setTabOrder(self.cbLabelFlightTrack, self.cbDrawCeiling)
        SideViewOptionsDialog.setTabOrder(self.cbDrawCeiling, self.btCeilingColour)

    def retranslateUi(self, SideViewOptionsDialog):
        _translate = QtCore.QCoreApplication.translate
        SideViewOptionsDialog.setWindowTitle(_translate("SideViewOptionsDialog", "Side View Options"))
        self.groupBox.setTitle(_translate("SideViewOptionsDialog", "Vertical Extent"))
        self.label_2.setText(_translate("SideViewOptionsDialog", "Vertical extent:"))
        self.sbPbot.setSuffix(_translate("SideViewOptionsDialog", " hpa"))
        self.label_3.setText(_translate("SideViewOptionsDialog", "to"))
        self.sbPtop.setSuffix(_translate("SideViewOptionsDialog", " hpa"))
        self.cbVerticalAxis.setItemText(0, _translate("SideViewOptionsDialog", "pressure"))
        self.cbVerticalAxis.setItemText(1, _translate("SideViewOptionsDialog", "pressure altitude"))
        self.cbVerticalAxis.setItemText(2, _translate("SideViewOptionsDialog", "flight level"))
        self.label_5.setText(_translate("SideViewOptionsDialog", "Secondary axis units: "))
        self.cbVerticalAxis2.setItemText(0, _translate("SideViewOptionsDialog", "no secondary axis"))
        self.cbVerticalAxis2.setItemText(1, _translate("SideViewOptionsDialog", "pressure"))
        self.cbVerticalAxis2.setItemText(2, _translate("SideViewOptionsDialog", "pressure altitude"))
        self.cbVerticalAxis2.setItemText(3, _translate("SideViewOptionsDialog", "flight level"))
        self.label_4.setText(_translate("SideViewOptionsDialog", "Vertical axis units:       "))
        self.groupBox_2.setTitle(_translate("SideViewOptionsDialog", "Flight Levels"))
        self.cbDrawFlightLevels.setText(_translate("SideViewOptionsDialog", "draw the following flight levels:"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("SideViewOptionsDialog", "flight levels"))
        self.btAdd.setText(_translate("SideViewOptionsDialog", "add"))
        self.btDelete.setText(_translate("SideViewOptionsDialog", "delete selected"))
        self.groupBox_3.setTitle(_translate("SideViewOptionsDialog", "Flight Track Colours"))
        self.cbDrawFlightTrack.setText(_translate("SideViewOptionsDialog", "draw flight track"))
        self.btVerticesColour.setText(_translate("SideViewOptionsDialog", "colour of flight path"))
        self.cbDrawMarker.setToolTip(_translate("SideViewOptionsDialog", "Draw a circle marker on every waypoint along the flight track"))
        self.cbDrawMarker.setText(_translate("SideViewOptionsDialog", "draw marker"))
        self.btWaypointsColour.setText(_translate("SideViewOptionsDialog", "colour of waypoints"))
        self.cbFillFlightTrack.setText(_translate("SideViewOptionsDialog", "fill flight track"))
        self.btFillColour.setText(_translate("SideViewOptionsDialog", "colour"))
        self.cbLabelFlightTrack.setText(_translate("SideViewOptionsDialog", "label flight track"))
        self.cbVerticalLines.setToolTip(_translate("SideViewOptionsDialog", "Draw a vertical line to visualise each point in the flight path"))
        self.cbVerticalLines.setText(_translate("SideViewOptionsDialog", "draw vertical lines"))
        self.groupBox_4.setTitle(_translate("SideViewOptionsDialog", "Performance"))
        self.cbDrawCeiling.setText(_translate("SideViewOptionsDialog", "draw ceiling altitude"))
        self.btCeilingColour.setText(_translate("SideViewOptionsDialog", "colour"))
        self.label.setText(_translate("SideViewOptionsDialog", " Plot Title Size               "))
        self.cbtitlesize.setItemText(0, _translate("SideViewOptionsDialog", "default"))
        self.cbtitlesize.setItemText(1, _translate("SideViewOptionsDialog", "4"))
        self.cbtitlesize.setItemText(2, _translate("SideViewOptionsDialog", "6"))
        self.cbtitlesize.setItemText(3, _translate("SideViewOptionsDialog", "8"))
        self.cbtitlesize.setItemText(4, _translate("SideViewOptionsDialog", "10"))
        self.cbtitlesize.setItemText(5, _translate("SideViewOptionsDialog", "12"))
        self.cbtitlesize.setItemText(6, _translate("SideViewOptionsDialog", "14"))
        self.cbtitlesize.setItemText(7, _translate("SideViewOptionsDialog", "16"))
        self.cbtitlesize.setItemText(8, _translate("SideViewOptionsDialog", "18"))
        self.cbtitlesize.setItemText(9, _translate("SideViewOptionsDialog", "20"))
        self.cbtitlesize.setItemText(10, _translate("SideViewOptionsDialog", "22"))
        self.cbtitlesize.setItemText(11, _translate("SideViewOptionsDialog", "24"))
        self.cbtitlesize.setItemText(12, _translate("SideViewOptionsDialog", "26"))
        self.cbtitlesize.setItemText(13, _translate("SideViewOptionsDialog", "28"))
        self.cbtitlesize.setItemText(14, _translate("SideViewOptionsDialog", "30"))
        self.cbtitlesize.setItemText(15, _translate("SideViewOptionsDialog", "32"))
        self.cbaxessize.setItemText(0, _translate("SideViewOptionsDialog", "default"))
        self.cbaxessize.setItemText(1, _translate("SideViewOptionsDialog", "4"))
        self.cbaxessize.setItemText(2, _translate("SideViewOptionsDialog", "6"))
        self.cbaxessize.setItemText(3, _translate("SideViewOptionsDialog", "8"))
        self.cbaxessize.setItemText(4, _translate("SideViewOptionsDialog", "10"))
        self.cbaxessize.setItemText(5, _translate("SideViewOptionsDialog", "12"))
        self.cbaxessize.setItemText(6, _translate("SideViewOptionsDialog", "14"))
        self.cbaxessize.setItemText(7, _translate("SideViewOptionsDialog", "16"))
        self.cbaxessize.setItemText(8, _translate("SideViewOptionsDialog", "18"))
        self.cbaxessize.setItemText(9, _translate("SideViewOptionsDialog", "20"))
        self.cbaxessize.setItemText(10, _translate("SideViewOptionsDialog", "22"))
        self.cbaxessize.setItemText(11, _translate("SideViewOptionsDialog", "24"))
        self.cbaxessize.setItemText(12, _translate("SideViewOptionsDialog", "26"))
        self.cbaxessize.setItemText(13, _translate("SideViewOptionsDialog", "28"))
        self.cbaxessize.setItemText(14, _translate("SideViewOptionsDialog", "30"))
        self.cbaxessize.setItemText(15, _translate("SideViewOptionsDialog", "32"))
        self.label_7.setText(_translate("SideViewOptionsDialog", "         Axes Label Size  "))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SideViewOptionsDialog = QtWidgets.QDialog()
    ui = Ui_SideViewOptionsDialog()
    ui.setupUi(SideViewOptionsDialog)
    SideViewOptionsDialog.show()
    sys.exit(app.exec_())
