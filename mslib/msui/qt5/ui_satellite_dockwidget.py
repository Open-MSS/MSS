# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_satellite_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SatelliteDockWidget(object):
    def setupUi(self, SatelliteDockWidget):
        SatelliteDockWidget.setObjectName("SatelliteDockWidget")
        SatelliteDockWidget.resize(649, 107)
        self.verticalLayout = QtWidgets.QVBoxLayout(SatelliteDockWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(SatelliteDockWidget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.leFile = QtWidgets.QLineEdit(SatelliteDockWidget)
        self.leFile.setObjectName("leFile")
        self.horizontalLayout_5.addWidget(self.leFile)
        self.btSelectFile = QtWidgets.QToolButton(SatelliteDockWidget)
        self.btSelectFile.setObjectName("btSelectFile")
        self.horizontalLayout_5.addWidget(self.btSelectFile)
        self.btLoadFile = QtWidgets.QToolButton(SatelliteDockWidget)
        self.btLoadFile.setObjectName("btLoadFile")
        self.horizontalLayout_5.addWidget(self.btLoadFile)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_6 = QtWidgets.QLabel(SatelliteDockWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_7.addWidget(self.label_6)
        self.cbSatelliteOverpasses = QtWidgets.QComboBox(SatelliteDockWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbSatelliteOverpasses.sizePolicy().hasHeightForWidth())
        self.cbSatelliteOverpasses.setSizePolicy(sizePolicy)
        self.cbSatelliteOverpasses.setObjectName("cbSatelliteOverpasses")
        self.horizontalLayout_7.addWidget(self.cbSatelliteOverpasses)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.label = QtWidgets.QLabel(SatelliteDockWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(SatelliteDockWidget)
        QtCore.QMetaObject.connectSlotsByName(SatelliteDockWidget)

    def retranslateUi(self, SatelliteDockWidget):
        _translate = QtCore.QCoreApplication.translate
        SatelliteDockWidget.setWindowTitle(_translate("SatelliteDockWidget", "Satellite Tracks"))
        self.label_5.setText(_translate("SatelliteDockWidget", "File with predicted satellite track:"))
        self.btSelectFile.setToolTip(_translate("SatelliteDockWidget", "Opens a file dialog for selecting a satellite overpass file."))
        self.btSelectFile.setText(_translate("SatelliteDockWidget", "..."))
        self.btLoadFile.setToolTip(_translate("SatelliteDockWidget", "Load the specified file for visualisation."))
        self.btLoadFile.setText(_translate("SatelliteDockWidget", "load"))
        self.label_6.setText(_translate("SatelliteDockWidget", "Predicted satellite overpasses:"))
        self.cbSatelliteOverpasses.setToolTip(_translate("SatelliteDockWidget", "Select/unselect a satellite overpass from all available overpasses."))
        self.label.setText(_translate("SatelliteDockWidget", "Use https://cloudsgate2.larc.nasa.gov/cgi-bin/predict/predict.cgi to generate prediction files."))

