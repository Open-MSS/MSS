# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_performance_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PerformanceDockWidget(object):
    def setupUi(self, PerformanceDockWidget):
        PerformanceDockWidget.setObjectName("PerformanceDockWidget")
        PerformanceDockWidget.resize(767, 123)
        self.gridLayout = QtWidgets.QGridLayout(PerformanceDockWidget)
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.gridLayout.setVerticalSpacing(1)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, 8, -1, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(PerformanceDockWidget)
        self.label_2.setIndent(5)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lbAircraftName = QtWidgets.QLabel(PerformanceDockWidget)
        self.lbAircraftName.setIndent(3)
        self.lbAircraftName.setObjectName("lbAircraftName")
        self.horizontalLayout_2.addWidget(self.lbAircraftName, 0, QtCore.Qt.AlignHCenter)
        self.pbLoadPerformance = QtWidgets.QPushButton(PerformanceDockWidget)
        self.pbLoadPerformance.setObjectName("pbLoadPerformance")
        self.horizontalLayout_2.addWidget(self.pbLoadPerformance, 0, QtCore.Qt.AlignRight)
        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 1, 1, 1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(PerformanceDockWidget)
        self.label_4.setIndent(1)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.dsbFuel = QtWidgets.QDoubleSpinBox(PerformanceDockWidget)
        self.dsbFuel.setDecimals(0)
        self.dsbFuel.setMaximum(9999999.0)
        self.dsbFuel.setSingleStep(1000.0)
        self.dsbFuel.setObjectName("dsbFuel")
        self.horizontalLayout_4.addWidget(self.dsbFuel)
        self.gridLayout.addLayout(self.horizontalLayout_4, 3, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(PerformanceDockWidget)
        self.label_3.setIndent(1)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.dteTakeoffTime = QtWidgets.QDateTimeEdit(PerformanceDockWidget)
        self.dteTakeoffTime.setObjectName("dteTakeoffTime")
        self.horizontalLayout_3.addWidget(self.dteTakeoffTime)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(-1, 4, -1, -1)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(PerformanceDockWidget)
        self.label_5.setIndent(1)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.dsbTakeoffWeight = QtWidgets.QDoubleSpinBox(PerformanceDockWidget)
        self.dsbTakeoffWeight.setDecimals(0)
        self.dsbTakeoffWeight.setMaximum(9999999.0)
        self.dsbTakeoffWeight.setSingleStep(1000.0)
        self.dsbTakeoffWeight.setObjectName("dsbTakeoffWeight")
        self.horizontalLayout_5.addWidget(self.dsbTakeoffWeight)
        self.gridLayout.addLayout(self.horizontalLayout_5, 1, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cbShowPerformance = QtWidgets.QCheckBox(PerformanceDockWidget)
        self.cbShowPerformance.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.cbShowPerformance.setTristate(False)
        self.cbShowPerformance.setObjectName("cbShowPerformance")
        self.horizontalLayout.addWidget(self.cbShowPerformance)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 1, 1, 1)

        self.retranslateUi(PerformanceDockWidget)
        QtCore.QMetaObject.connectSlotsByName(PerformanceDockWidget)

    def retranslateUi(self, PerformanceDockWidget):
        _translate = QtCore.QCoreApplication.translate
        PerformanceDockWidget.setWindowTitle(_translate("PerformanceDockWidget", "PerformanceDockWidget"))
        self.label_2.setText(_translate("PerformanceDockWidget", "Aircraft:"))
        self.lbAircraftName.setText(_translate("PerformanceDockWidget", "DUMMY"))
        self.pbLoadPerformance.setText(_translate("PerformanceDockWidget", "Select"))
        self.label_4.setText(_translate("PerformanceDockWidget", "Fuel (lb)"))
        self.label_3.setText(_translate("PerformanceDockWidget", "Take off time"))
        self.label_5.setText(_translate("PerformanceDockWidget", "Take off weight (lb)"))
        self.cbShowPerformance.setText(_translate("PerformanceDockWidget", "Show Performance"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    PerformanceDockWidget = QtWidgets.QDialog()
    ui = Ui_PerformanceDockWidget()
    ui.setupUi(PerformanceDockWidget)
    PerformanceDockWidget.show()
    sys.exit(app.exec_())

