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
        self.btSelectFile = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.btSelectFile.setObjectName("btSelectFile")
        self.verticalLayout.addWidget(self.btSelectFile)
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
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.pushButton_merge = QtWidgets.QPushButton(KMLOverlayDockWidget)
        self.pushButton_merge.setObjectName("pushButton_merge")
        self.verticalLayout_2.addWidget(self.pushButton_merge)

        self.retranslateUi(KMLOverlayDockWidget)
        QtCore.QMetaObject.connectSlotsByName(KMLOverlayDockWidget)

    def retranslateUi(self, KMLOverlayDockWidget):
        _translate = QtCore.QCoreApplication.translate
        KMLOverlayDockWidget.setWindowTitle(_translate("KMLOverlayDockWidget", "KML Overlay"))
        self.listWidget.setToolTip(_translate("KMLOverlayDockWidget", "KML Files; double click specific file to customize"))
        self.btSelectFile.setToolTip(_translate("KMLOverlayDockWidget", "Add multiple KML Files"))
        self.btSelectFile.setText(_translate("KMLOverlayDockWidget", "Add KML File"))
        self.pushButton_remove.setToolTip(_translate("KMLOverlayDockWidget", "Remove Checked KML Files "))
        self.pushButton_remove.setText(_translate("KMLOverlayDockWidget", "Remove"))
        self.pushButton_remove_all.setToolTip(_translate("KMLOverlayDockWidget", "Remove All KML Files"))
        self.pushButton_remove_all.setText(_translate("KMLOverlayDockWidget", "Remove All"))
        self.pushButton_merge.setToolTip(_translate("KMLOverlayDockWidget", "Merge multiple KML Files into one"))
        self.pushButton_merge.setText(_translate("KMLOverlayDockWidget", "Merge and Export KML File"))

