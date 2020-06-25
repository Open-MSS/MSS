# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_add_multiple_kml_overlay.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.setEnabled(True)
        Dialog.resize(400, 300)
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setGeometry(QtCore.QRect(30, 40, 256, 192))
        self.listWidget.setObjectName("listWidget")
        self.pushButton_add = QtWidgets.QPushButton(Dialog)
        self.pushButton_add.setGeometry(QtCore.QRect(300, 50, 89, 25))
        self.pushButton_add.setObjectName("pushButton_add")
        self.pushButton_remove = QtWidgets.QPushButton(Dialog)
        self.pushButton_remove.setGeometry(QtCore.QRect(300, 90, 89, 25))
        self.pushButton_remove.setObjectName("pushButton_remove")
        self.pushButton_load = QtWidgets.QPushButton(Dialog)
        self.pushButton_load.setGeometry(QtCore.QRect(300, 190, 89, 25))
        self.pushButton_load.setObjectName("pushButton_load")
        self.pushButton_merge = QtWidgets.QPushButton(Dialog)
        self.pushButton_merge.setGeometry(QtCore.QRect(50, 260, 221, 25))
        self.pushButton_merge.setObjectName("pushButton_merge")
        self.pushButton_remove_all = QtWidgets.QPushButton(Dialog)
        self.pushButton_remove_all.setGeometry(QtCore.QRect(300, 140, 89, 25))
        self.pushButton_remove_all.setObjectName("pushButton_remove_all")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Add Multiple KML Files"))
        self.pushButton_add.setText(_translate("Dialog", "Add"))
        self.pushButton_remove.setText(_translate("Dialog", "Remove"))
        self.pushButton_load.setText(_translate("Dialog", "Load"))
        self.pushButton_merge.setText(_translate("Dialog", "Merge and Export as KML File"))
        self.pushButton_remove_all.setText(_translate("Dialog", "Remove All"))

