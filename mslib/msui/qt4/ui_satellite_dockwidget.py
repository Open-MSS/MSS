# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_satellite_dockwidget.ui'
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

class Ui_SatelliteDockWidget(object):
    def setupUi(self, SatelliteDockWidget):
        SatelliteDockWidget.setObjectName(_fromUtf8("SatelliteDockWidget"))
        SatelliteDockWidget.resize(649, 107)
        self.verticalLayout = QtGui.QVBoxLayout(SatelliteDockWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label_5 = QtGui.QLabel(SatelliteDockWidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.horizontalLayout_5.addWidget(self.label_5)
        self.leFile = QtGui.QLineEdit(SatelliteDockWidget)
        self.leFile.setObjectName(_fromUtf8("leFile"))
        self.horizontalLayout_5.addWidget(self.leFile)
        self.btSelectFile = QtGui.QToolButton(SatelliteDockWidget)
        self.btSelectFile.setObjectName(_fromUtf8("btSelectFile"))
        self.horizontalLayout_5.addWidget(self.btSelectFile)
        self.btLoadFile = QtGui.QToolButton(SatelliteDockWidget)
        self.btLoadFile.setObjectName(_fromUtf8("btLoadFile"))
        self.horizontalLayout_5.addWidget(self.btLoadFile)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.label_6 = QtGui.QLabel(SatelliteDockWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.horizontalLayout_7.addWidget(self.label_6)
        self.cbSatelliteOverpasses = QtGui.QComboBox(SatelliteDockWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbSatelliteOverpasses.sizePolicy().hasHeightForWidth())
        self.cbSatelliteOverpasses.setSizePolicy(sizePolicy)
        self.cbSatelliteOverpasses.setObjectName(_fromUtf8("cbSatelliteOverpasses"))
        self.horizontalLayout_7.addWidget(self.cbSatelliteOverpasses)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.label = QtGui.QLabel(SatelliteDockWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(SatelliteDockWidget)
        QtCore.QMetaObject.connectSlotsByName(SatelliteDockWidget)

    def retranslateUi(self, SatelliteDockWidget):
        SatelliteDockWidget.setWindowTitle(_translate("SatelliteDockWidget", "Satellite Tracks", None))
        self.label_5.setText(_translate("SatelliteDockWidget", "File with predicted satellite track:", None))
        self.btSelectFile.setToolTip(_translate("SatelliteDockWidget", "Opens a file dialog for selecting a satellite overpass file.", None))
        self.btSelectFile.setText(_translate("SatelliteDockWidget", "...", None))
        self.btLoadFile.setToolTip(_translate("SatelliteDockWidget", "Load the specified file for visualisation.", None))
        self.btLoadFile.setText(_translate("SatelliteDockWidget", "load", None))
        self.label_6.setText(_translate("SatelliteDockWidget", "Predicted satellite overpasses:", None))
        self.cbSatelliteOverpasses.setToolTip(_translate("SatelliteDockWidget", "Select/unselect a satellite overpass from all available overpasses.", None))
        self.label.setText(_translate("SatelliteDockWidget", "Use http://www-air.larc.nasa.gov/tools/predict.htm to generate prediction files.", None))

