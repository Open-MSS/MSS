# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_kmloverlay_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_KMLOverlayDockWidget(object):
    def setupUi(self, KMLOverlayDockWidget):
        KMLOverlayDockWidget.setObjectName("KMLOverlayDockWidget")
        KMLOverlayDockWidget.resize(545, 234)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(KMLOverlayDockWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget = QtWidgets.QListWidget(KMLOverlayDockWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.listWidget.setObjectName("listWidget")
        self.horizontalLayout.addWidget(self.listWidget)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cbOverlay = QtWidgets.QCheckBox(KMLOverlayDockWidget)
        self.cbOverlay.setObjectName("cbOverlay")
        self.verticalLayout.addWidget(self.cbOverlay)
        self.btSelectFile = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.btSelectFile.setObjectName("btSelectFile")
        self.verticalLayout.addWidget(self.btSelectFile)
        self.btLoadFile = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.btLoadFile.setObjectName("btLoadFile")
        self.verticalLayout.addWidget(self.btLoadFile)
        self.pushButton_remove = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.pushButton_remove.setObjectName("pushButton_remove")
        self.verticalLayout.addWidget(self.pushButton_remove)
        self.pushButton_remove_all = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.pushButton_remove_all.setObjectName("pushButton_remove_all")
        self.verticalLayout.addWidget(self.pushButton_remove_all)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.cbManualStyle = QtWidgets.QCheckBox(KMLOverlayDockWidget)
        self.cbManualStyle.setObjectName("cbManualStyle")
        self.horizontalLayout_2.addWidget(self.cbManualStyle)
        self.pbSelectColour = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.pbSelectColour.setObjectName("pbSelectColour")
        self.horizontalLayout_2.addWidget(self.pbSelectColour)
        self.label_2 = QtWidgets.QLabel(KMLOverlayDockWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.dsbLineWidth = QtWidgets.QDoubleSpinBox(KMLOverlayDockWidget)
        self.dsbLineWidth.setObjectName("dsbLineWidth")
        self.horizontalLayout_2.addWidget(self.dsbLineWidth)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.pushButton_merge = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.pushButton_merge.setObjectName("pushButton_merge")
        self.verticalLayout_2.addWidget(self.pushButton_merge)

        self.retranslateUi(KMLOverlayDockWidget)
        QtCore.QMetaObject.connectSlotsByName(KMLOverlayDockWidget)

    def retranslateUi(self, KMLOverlayDockWidget):
        _translate = QtCore.QCoreApplication.translate
        KMLOverlayDockWidget.setWindowTitle(_translate("KMLOverlayDockWidget", "KML Overlay"))
        self.cbOverlay.setText(_translate("KMLOverlayDockWidget", "KML Overlay"))
        self.btSelectFile.setText(_translate("KMLOverlayDockWidget", "Add KML File"))
        self.btLoadFile.setText(_translate("KMLOverlayDockWidget", "Load"))
        self.pushButton_remove.setText(_translate("KMLOverlayDockWidget", "Remove"))
        self.pushButton_remove_all.setText(_translate("KMLOverlayDockWidget", "Remove All"))
        self.cbManualStyle.setText(_translate("KMLOverlayDockWidget", "Manual Style"))
        self.pbSelectColour.setText(_translate("KMLOverlayDockWidget", "Colour"))
        self.label_2.setText(_translate("KMLOverlayDockWidget", "line width"))
        self.pushButton_merge.setText(_translate("KMLOverlayDockWidget", "Merge and Export KML File"))

