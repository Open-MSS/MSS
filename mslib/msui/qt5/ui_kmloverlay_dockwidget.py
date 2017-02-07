# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_kmloverlay_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_KMLOverlayDockWidget(object):
    def setupUi(self, KMLOverlayDockWidget):
        KMLOverlayDockWidget.setObjectName("KMLOverlayDockWidget")
        KMLOverlayDockWidget.resize(649, 120)
        self.verticalLayout = QtWidgets.QVBoxLayout(KMLOverlayDockWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.cbOverlay = QtWidgets.QCheckBox(KMLOverlayDockWidget)
        self.cbOverlay.setObjectName("cbOverlay")
        self.horizontalLayout_5.addWidget(self.cbOverlay)
        self.leFile = QtWidgets.QLineEdit(KMLOverlayDockWidget)
        self.leFile.setObjectName("leFile")
        self.horizontalLayout_5.addWidget(self.leFile)
        self.btSelectFile = QtWidgets.QToolButton(KMLOverlayDockWidget)
        self.btSelectFile.setObjectName("btSelectFile")
        self.horizontalLayout_5.addWidget(self.btSelectFile)
        self.btLoadFile = QtWidgets.QToolButton(KMLOverlayDockWidget)
        self.btLoadFile.setObjectName("btLoadFile")
        self.horizontalLayout_5.addWidget(self.btLoadFile)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.pbSelectColour = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.pbSelectColour.setObjectName("pbSelectColour")
        self.horizontalLayout_7.addWidget(self.pbSelectColour)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.label = QtWidgets.QLabel(KMLOverlayDockWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        self.retranslateUi(KMLOverlayDockWidget)
        QtCore.QMetaObject.connectSlotsByName(KMLOverlayDockWidget)

    def retranslateUi(self, KMLOverlayDockWidget):
        _translate = QtCore.QCoreApplication.translate
        KMLOverlayDockWidget.setWindowTitle(_translate("KMLOverlayDockWidget", "KML Overlay"))
        self.cbOverlay.setText(_translate("KMLOverlayDockWidget", "KML Overlay"))
        self.btSelectFile.setText(_translate("KMLOverlayDockWidget", "..."))
        self.btLoadFile.setText(_translate("KMLOverlayDockWidget", "load"))
        self.pbSelectColour.setText(_translate("KMLOverlayDockWidget", "Colour"))
        self.label.setText(_translate("KMLOverlayDockWidget", "!Experimental Feature! Not all KML files and contained features will work."))

