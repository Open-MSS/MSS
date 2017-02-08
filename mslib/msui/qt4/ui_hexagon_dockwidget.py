# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'msui/ui_hexagon_dockwidget.ui'
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

class Ui_HexagonDockWidget(object):
    def setupUi(self, HexagonDockWidget):
        HexagonDockWidget.setObjectName(_fromUtf8("HexagonDockWidget"))
        HexagonDockWidget.resize(638, 114)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(HexagonDockWidget.sizePolicy().hasHeightForWidth())
        HexagonDockWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(HexagonDockWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label = QtGui.QLabel(HexagonDockWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_5.addWidget(self.label)
        self.dsbHexagonLatitude = QtGui.QDoubleSpinBox(HexagonDockWidget)
        self.dsbHexagonLatitude.setMinimumSize(QtCore.QSize(0, 0))
        self.dsbHexagonLatitude.setPrefix(_fromUtf8(""))
        self.dsbHexagonLatitude.setMinimum(-90.0)
        self.dsbHexagonLatitude.setMaximum(90.0)
        self.dsbHexagonLatitude.setObjectName(_fromUtf8("dsbHexagonLatitude"))
        self.horizontalLayout_5.addWidget(self.dsbHexagonLatitude)
        self.label_2 = QtGui.QLabel(HexagonDockWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_5.addWidget(self.label_2)
        self.dsbHexagonLongitude = QtGui.QDoubleSpinBox(HexagonDockWidget)
        self.dsbHexagonLongitude.setMinimum(-180.0)
        self.dsbHexagonLongitude.setMaximum(360.0)
        self.dsbHexagonLongitude.setObjectName(_fromUtf8("dsbHexagonLongitude"))
        self.horizontalLayout_5.addWidget(self.dsbHexagonLongitude)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_3 = QtGui.QLabel(HexagonDockWidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_2.addWidget(self.label_3)
        self.dsbHexgaonRadius = QtGui.QDoubleSpinBox(HexagonDockWidget)
        self.dsbHexgaonRadius.setMinimum(10.0)
        self.dsbHexgaonRadius.setMaximum(9999.99)
        self.dsbHexgaonRadius.setSingleStep(10.0)
        self.dsbHexgaonRadius.setProperty("value", 200.0)
        self.dsbHexgaonRadius.setObjectName(_fromUtf8("dsbHexgaonRadius"))
        self.horizontalLayout_2.addWidget(self.dsbHexgaonRadius)
        self.label_4 = QtGui.QLabel(HexagonDockWidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.horizontalLayout_2.addWidget(self.label_4)
        self.dsbHexagonAngle = QtGui.QDoubleSpinBox(HexagonDockWidget)
        self.dsbHexagonAngle.setMinimum(-360.0)
        self.dsbHexagonAngle.setMaximum(360.0)
        self.dsbHexagonAngle.setObjectName(_fromUtf8("dsbHexagonAngle"))
        self.horizontalLayout_2.addWidget(self.dsbHexagonAngle)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.pbAddHexagon = QtGui.QPushButton(HexagonDockWidget)
        self.pbAddHexagon.setObjectName(_fromUtf8("pbAddHexagon"))
        self.horizontalLayout_6.addWidget(self.pbAddHexagon)
        self.pbRemoveHexagon = QtGui.QPushButton(HexagonDockWidget)
        self.pbRemoveHexagon.setObjectName(_fromUtf8("pbRemoveHexagon"))
        self.horizontalLayout_6.addWidget(self.pbRemoveHexagon)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.retranslateUi(HexagonDockWidget)
        QtCore.QMetaObject.connectSlotsByName(HexagonDockWidget)

    def retranslateUi(self, HexagonDockWidget):
        HexagonDockWidget.setWindowTitle(_translate("HexagonDockWidget", "Remote Sensing", None))
        self.label.setText(_translate("HexagonDockWidget", "Center latitude", None))
        self.dsbHexagonLatitude.setSuffix(_translate("HexagonDockWidget", " °N", None))
        self.label_2.setText(_translate("HexagonDockWidget", "Center longitude", None))
        self.dsbHexagonLongitude.setSuffix(_translate("HexagonDockWidget", " °E", None))
        self.label_3.setText(_translate("HexagonDockWidget", "Radius", None))
        self.dsbHexgaonRadius.setSuffix(_translate("HexagonDockWidget", " km", None))
        self.label_4.setText(_translate("HexagonDockWidget", "Angle of first point", None))
        self.dsbHexagonAngle.setSuffix(_translate("HexagonDockWidget", " °", None))
        self.pbAddHexagon.setText(_translate("HexagonDockWidget", "Add Hexagon", None))
        self.pbRemoveHexagon.setText(_translate("HexagonDockWidget", "Remove Hexagon", None))

