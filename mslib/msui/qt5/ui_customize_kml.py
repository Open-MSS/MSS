# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_customize_kml.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CustomizeKMLDialog(object):
    def setupUi(self, CustomizeKMLDialog):
        CustomizeKMLDialog.setObjectName("CustomizeKMLDialog")
        CustomizeKMLDialog.resize(425, 109)
        self.verticalLayout = QtWidgets.QVBoxLayout(CustomizeKMLDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(CustomizeKMLDialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.pushButton_colour = QtWidgets.QPushButton(CustomizeKMLDialog)
        self.pushButton_colour.setObjectName("pushButton_colour")
        self.horizontalLayout.addWidget(self.pushButton_colour)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(CustomizeKMLDialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.pushButton_linewidth = QtWidgets.QPushButton(CustomizeKMLDialog)
        self.pushButton_linewidth.setObjectName("pushButton_linewidth")
        self.horizontalLayout_2.addWidget(self.pushButton_linewidth)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(CustomizeKMLDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CustomizeKMLDialog)
        self.buttonBox.accepted.connect(CustomizeKMLDialog.accept)
        self.buttonBox.rejected.connect(CustomizeKMLDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CustomizeKMLDialog)

    def retranslateUi(self, CustomizeKMLDialog):
        _translate = QtCore.QCoreApplication.translate
        CustomizeKMLDialog.setWindowTitle(_translate("CustomizeKMLDialog", "Customize KML File"))
        self.label.setText(_translate("CustomizeKMLDialog", "Placemark Colour"))
        self.pushButton_colour.setText(_translate("CustomizeKMLDialog", "Change Colour"))
        self.label_2.setText(_translate("CustomizeKMLDialog", "LineWidth "))
        self.pushButton_linewidth.setText(_translate("CustomizeKMLDialog", "Change LineWidth"))

