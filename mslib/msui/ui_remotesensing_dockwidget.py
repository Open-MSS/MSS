# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_remotesensing_dockwidget.ui'
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

class Ui_RemoteSensingDockWidget(object):
    def setupUi(self, RemoteSensingDockWidget):
        RemoteSensingDockWidget.setObjectName(_fromUtf8("RemoteSensingDockWidget"))
        RemoteSensingDockWidget.resize(465, 133)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RemoteSensingDockWidget.sizePolicy().hasHeightForWidth())
        RemoteSensingDockWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(RemoteSensingDockWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lbObsAngle = QtGui.QLabel(RemoteSensingDockWidget)
        self.lbObsAngle.setObjectName(_fromUtf8("lbObsAngle"))
        self.horizontalLayout.addWidget(self.lbObsAngle)
        self.dsbObsAngle = QtGui.QDoubleSpinBox(RemoteSensingDockWidget)
        self.dsbObsAngle.setDecimals(0)
        self.dsbObsAngle.setMinimum(-180.0)
        self.dsbObsAngle.setMaximum(180.0)
        self.dsbObsAngle.setSingleStep(15.0)
        self.dsbObsAngle.setObjectName(_fromUtf8("dsbObsAngle"))
        self.horizontalLayout.addWidget(self.dsbObsAngle)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.cbDrawTangents = QtGui.QCheckBox(RemoteSensingDockWidget)
        self.cbDrawTangents.setMinimumSize(QtCore.QSize(145, 0))
        self.cbDrawTangents.setObjectName(_fromUtf8("cbDrawTangents"))
        self.horizontalLayout_5.addWidget(self.cbDrawTangents)
        self.btTangentsColour = QtGui.QPushButton(RemoteSensingDockWidget)
        self.btTangentsColour.setMinimumSize(QtCore.QSize(135, 0))
        self.btTangentsColour.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.btTangentsColour.setObjectName(_fromUtf8("btTangentsColour"))
        self.horizontalLayout_5.addWidget(self.btTangentsColour)
        self.dsbTangentHeight = QtGui.QDoubleSpinBox(RemoteSensingDockWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dsbTangentHeight.sizePolicy().hasHeightForWidth())
        self.dsbTangentHeight.setSizePolicy(sizePolicy)
        self.dsbTangentHeight.setMinimumSize(QtCore.QSize(0, 0))
        self.dsbTangentHeight.setPrefix(_fromUtf8(""))
        self.dsbTangentHeight.setObjectName(_fromUtf8("dsbTangentHeight"))
        self.horizontalLayout_5.addWidget(self.dsbTangentHeight)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.cbShowSolarAngle = QtGui.QCheckBox(RemoteSensingDockWidget)
        self.cbShowSolarAngle.setMinimumSize(QtCore.QSize(145, 0))
        self.cbShowSolarAngle.setObjectName(_fromUtf8("cbShowSolarAngle"))
        self.horizontalLayout_6.addWidget(self.cbShowSolarAngle)
        self.lbStartTime = QtGui.QLabel(RemoteSensingDockWidget)
        self.lbStartTime.setMinimumSize(QtCore.QSize(0, 0))
        self.lbStartTime.setObjectName(_fromUtf8("lbStartTime"))
        self.horizontalLayout_6.addWidget(self.lbStartTime)
        self.dteStartTime = QtGui.QDateTimeEdit(RemoteSensingDockWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dteStartTime.sizePolicy().hasHeightForWidth())
        self.dteStartTime.setSizePolicy(sizePolicy)
        self.dteStartTime.setObjectName(_fromUtf8("dteStartTime"))
        self.horizontalLayout_6.addWidget(self.dteStartTime)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(RemoteSensingDockWidget)
        QtCore.QMetaObject.connectSlotsByName(RemoteSensingDockWidget)

    def retranslateUi(self, RemoteSensingDockWidget):
        RemoteSensingDockWidget.setWindowTitle(_translate("RemoteSensingDockWidget", "Remote Sensing", None))
        self.lbObsAngle.setText(_translate("RemoteSensingDockWidget", "Viewing direction", None))
        self.cbDrawTangents.setText(_translate("RemoteSensingDockWidget", "draw tangent paths", None))
        self.btTangentsColour.setText(_translate("RemoteSensingDockWidget", "colour", None))
        self.dsbTangentHeight.setSuffix(_translate("RemoteSensingDockWidget", " km", None))
        self.cbShowSolarAngle.setText(_translate("RemoteSensingDockWidget", "show solar angle", None))
        self.lbStartTime.setText(_translate("RemoteSensingDockWidget", "Start time:", None))

