# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_satellite_dockwidget.ui'
#
# Created: Fri Aug 20 17:48:34 2010
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_SatelliteDockWidget(object):
    def setupUi(self, SatelliteDockWidget):
        SatelliteDockWidget.setObjectName("SatelliteDockWidget")
        SatelliteDockWidget.resize(649, 104)
        self.verticalLayout = QtGui.QVBoxLayout(SatelliteDockWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtGui.QLabel(SatelliteDockWidget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.leFile = QtGui.QLineEdit(SatelliteDockWidget)
        self.leFile.setObjectName("leFile")
        self.horizontalLayout_5.addWidget(self.leFile)
        self.btSelectFile = QtGui.QToolButton(SatelliteDockWidget)
        self.btSelectFile.setObjectName("btSelectFile")
        self.horizontalLayout_5.addWidget(self.btSelectFile)
        self.btLoadFile = QtGui.QToolButton(SatelliteDockWidget)
        self.btLoadFile.setObjectName("btLoadFile")
        self.horizontalLayout_5.addWidget(self.btLoadFile)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_6 = QtGui.QLabel(SatelliteDockWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_7.addWidget(self.label_6)
        self.cbSatelliteOverpasses = QtGui.QComboBox(SatelliteDockWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbSatelliteOverpasses.sizePolicy().hasHeightForWidth())
        self.cbSatelliteOverpasses.setSizePolicy(sizePolicy)
        self.cbSatelliteOverpasses.setObjectName("cbSatelliteOverpasses")
        self.horizontalLayout_7.addWidget(self.cbSatelliteOverpasses)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(SatelliteDockWidget)
        QtCore.QMetaObject.connectSlotsByName(SatelliteDockWidget)

    def retranslateUi(self, SatelliteDockWidget):
        SatelliteDockWidget.setWindowTitle(QtGui.QApplication.translate("SatelliteDockWidget", "Satellite Tracks", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("SatelliteDockWidget", "File with predicted satellite track:", None, QtGui.QApplication.UnicodeUTF8))
        self.btSelectFile.setText(QtGui.QApplication.translate("SatelliteDockWidget", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.btLoadFile.setText(QtGui.QApplication.translate("SatelliteDockWidget", "load", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("SatelliteDockWidget", "Predicted satellite overpasses:", None, QtGui.QApplication.UnicodeUTF8))

