# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mss_rename_message.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MSSMainWindow(object):
    def setupUi(self, MSSMainWindow):
        MSSMainWindow.setObjectName("MSSMainWindow")
        MSSMainWindow.resize(580, 275)
        self.centralwidget = QtWidgets.QWidget(MSSMainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        MSSMainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MSSMainWindow)
        self.pushButton.clicked.connect(MSSMainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MSSMainWindow)

    def retranslateUi(self, MSSMainWindow):
        _translate = QtCore.QCoreApplication.translate
        MSSMainWindow.setWindowTitle(_translate("MSSMainWindow", "Mission Support System"))
        self.label.setText(_translate("MSSMainWindow", "Mission Support System"))
        self.textBrowser.setHtml(_translate("MSSMainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The \'mss\' program has been renamed to \'<span style=\" font-weight:600;\">msui</span>\'.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Please use the new command to start the MS User Interface application.</p></body></html>"))
        self.pushButton.setText(_translate("MSSMainWindow", "OK"))
