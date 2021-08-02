# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_webbrowser.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_WebBrowser(object):
    def setupUi(self, WebBrowser):
        WebBrowser.setObjectName("WebBrowser")
        WebBrowser.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(WebBrowser)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.webEngineView = QtWebEngineWidgets.QWebEngineView(self.centralwidget)
        self.webEngineView.setUrl(QtCore.QUrl("about:blank"))
        self.webEngineView.setObjectName("webEngineView")
        self.verticalLayout.addWidget(self.webEngineView)
        WebBrowser.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(WebBrowser)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 20))
        self.menubar.setObjectName("menubar")
        WebBrowser.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(WebBrowser)
        self.statusbar.setObjectName("statusbar")
        WebBrowser.setStatusBar(self.statusbar)

        self.retranslateUi(WebBrowser)
        QtCore.QMetaObject.connectSlotsByName(WebBrowser)

    def retranslateUi(self, WebBrowser):
        _translate = QtCore.QCoreApplication.translate
        WebBrowser.setWindowTitle(_translate("WebBrowser", "MainWindow"))
from PyQt5 import QtWebEngineWidgets
