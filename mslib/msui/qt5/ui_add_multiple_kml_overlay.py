# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_add_multiple_kml_overlay.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog

class Ui_Dialog(QDialog):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setGeometry(QtCore.QRect(30, 40, 256, 192))
        self.listWidget.setObjectName("listWidget")
        self.pushButton_load = QtWidgets.QPushButton(Dialog)
        self.pushButton_load.setGeometry(QtCore.QRect(300, 190, 89, 25))
        self.pushButton_load.setObjectName("pushButton_load")
        self.pushButton_merge = QtWidgets.QPushButton(Dialog)
        self.pushButton_merge.setGeometry(QtCore.QRect(50, 260, 221, 25))
        self.pushButton_merge.setObjectName("pushButton_merge")
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setGeometry(QtCore.QRect(300, 50, 91, 89))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton_add = QtWidgets.QPushButton(self.widget)
        self.pushButton_add.setObjectName("pushButton_add")
        self.verticalLayout.addWidget(self.pushButton_add)
        self.pushButton_remove = QtWidgets.QPushButton(self.widget)
        self.pushButton_remove.setObjectName("pushButton_remove")
        self.verticalLayout.addWidget(self.pushButton_remove)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.kml_file()

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Add Multiple KML Files"))
        self.pushButton_load.setText(_translate("Dialog", "Load"))
        self.pushButton_merge.setText(_translate("Dialog", "Merge and Export as KML File"))
        self.pushButton_add.setText(_translate("Dialog", "Add"))
        self.pushButton_remove.setText(_translate("Dialog", "Remove"))

    def kml_file(self):
        self.kml_file = ["color.kml", "line.kml", "folder.kml", "style.kml"]
        self.listWidget.addItems(self.kml_file)
        self.listWidget.setCurrentRow(0)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

