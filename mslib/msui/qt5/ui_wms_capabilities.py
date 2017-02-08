# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_wms_capabilities.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_WMSCapabilitiesBrowser(object):
    def setupUi(self, WMSCapabilitiesBrowser):
        WMSCapabilitiesBrowser.setObjectName("WMSCapabilitiesBrowser")
        WMSCapabilitiesBrowser.resize(754, 393)
        self.verticalLayout = QtWidgets.QVBoxLayout(WMSCapabilitiesBrowser)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(WMSCapabilitiesBrowser)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lblURL = QtWidgets.QLabel(WMSCapabilitiesBrowser)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblURL.sizePolicy().hasHeightForWidth())
        self.lblURL.setSizePolicy(sizePolicy)
        self.lblURL.setObjectName("lblURL")
        self.horizontalLayout_2.addWidget(self.lblURL)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.txtCapabilities = QtWidgets.QTextBrowser(WMSCapabilitiesBrowser)
        self.txtCapabilities.setOpenExternalLinks(False)
        self.txtCapabilities.setObjectName("txtCapabilities")
        self.verticalLayout.addWidget(self.txtCapabilities)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btClose = QtWidgets.QPushButton(WMSCapabilitiesBrowser)
        self.btClose.setObjectName("btClose")
        self.horizontalLayout.addWidget(self.btClose)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(WMSCapabilitiesBrowser)
        self.btClose.clicked.connect(WMSCapabilitiesBrowser.close)
        QtCore.QMetaObject.connectSlotsByName(WMSCapabilitiesBrowser)

    def retranslateUi(self, WMSCapabilitiesBrowser):
        _translate = QtCore.QCoreApplication.translate
        WMSCapabilitiesBrowser.setWindowTitle(_translate("WMSCapabilitiesBrowser", "Browse WMS Capabilities - Mission Support System"))
        self.label.setText(_translate("WMSCapabilitiesBrowser", "Capabilities document of:"))
        self.lblURL.setText(_translate("WMSCapabilitiesBrowser", "<URL>"))
        self.btClose.setText(_translate("WMSCapabilitiesBrowser", "close"))

