# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_remotesensing_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_RemoteSensingDockWidget(object):
    def setupUi(self, RemoteSensingDockWidget):
        RemoteSensingDockWidget.setObjectName("RemoteSensingDockWidget")
        RemoteSensingDockWidget.resize(465, 133)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RemoteSensingDockWidget.sizePolicy().hasHeightForWidth())
        RemoteSensingDockWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(RemoteSensingDockWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lbObsAngle = QtWidgets.QLabel(RemoteSensingDockWidget)
        self.lbObsAngle.setObjectName("lbObsAngle")
        self.horizontalLayout.addWidget(self.lbObsAngle)
        self.dsbObsAngle = QtWidgets.QDoubleSpinBox(RemoteSensingDockWidget)
        self.dsbObsAngle.setDecimals(0)
        self.dsbObsAngle.setMinimum(-180.0)
        self.dsbObsAngle.setMaximum(180.0)
        self.dsbObsAngle.setSingleStep(15.0)
        self.dsbObsAngle.setObjectName("dsbObsAngle")
        self.horizontalLayout.addWidget(self.dsbObsAngle)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.cbDrawTangents = QtWidgets.QCheckBox(RemoteSensingDockWidget)
        self.cbDrawTangents.setMinimumSize(QtCore.QSize(145, 0))
        self.cbDrawTangents.setObjectName("cbDrawTangents")
        self.horizontalLayout_5.addWidget(self.cbDrawTangents)
        self.btTangentsColour = QtWidgets.QPushButton(RemoteSensingDockWidget)
        self.btTangentsColour.setMinimumSize(QtCore.QSize(135, 0))
        self.btTangentsColour.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.btTangentsColour.setObjectName("btTangentsColour")
        self.horizontalLayout_5.addWidget(self.btTangentsColour)
        self.dsbTangentHeight = QtWidgets.QDoubleSpinBox(RemoteSensingDockWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dsbTangentHeight.sizePolicy().hasHeightForWidth())
        self.dsbTangentHeight.setSizePolicy(sizePolicy)
        self.dsbTangentHeight.setMinimumSize(QtCore.QSize(0, 0))
        self.dsbTangentHeight.setPrefix("")
        self.dsbTangentHeight.setObjectName("dsbTangentHeight")
        self.horizontalLayout_5.addWidget(self.dsbTangentHeight)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.cbShowSolarAngle = QtWidgets.QCheckBox(RemoteSensingDockWidget)
        self.cbShowSolarAngle.setMinimumSize(QtCore.QSize(145, 0))
        self.cbShowSolarAngle.setObjectName("cbShowSolarAngle")
        self.horizontalLayout_6.addWidget(self.cbShowSolarAngle)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(RemoteSensingDockWidget)
        QtCore.QMetaObject.connectSlotsByName(RemoteSensingDockWidget)

    def retranslateUi(self, RemoteSensingDockWidget):
        _translate = QtCore.QCoreApplication.translate
        RemoteSensingDockWidget.setWindowTitle(_translate("RemoteSensingDockWidget", "Remote Sensing"))
        self.lbObsAngle.setText(_translate("RemoteSensingDockWidget", "Viewing direction"))
        self.cbDrawTangents.setText(_translate("RemoteSensingDockWidget", "draw tangent points"))
        self.btTangentsColour.setText(_translate("RemoteSensingDockWidget", "colour"))
        self.dsbTangentHeight.setSuffix(_translate("RemoteSensingDockWidget", " km"))
        self.cbShowSolarAngle.setText(_translate("RemoteSensingDockWidget", "show solar angle"))

