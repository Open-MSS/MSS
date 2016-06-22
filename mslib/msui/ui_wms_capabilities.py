# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_wms_capabilities.ui'
#
# Created: Mon Jan 17 12:53:38 2011
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui


class Ui_WMSCapabilitiesBrowser(object):
    def setupUi(self, WMSCapabilitiesBrowser):
        WMSCapabilitiesBrowser.setObjectName("WMSCapabilitiesBrowser")
        WMSCapabilitiesBrowser.resize(754, 393)
        self.verticalLayout = QtGui.QVBoxLayout(WMSCapabilitiesBrowser)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtGui.QLabel(WMSCapabilitiesBrowser)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lblURL = QtGui.QLabel(WMSCapabilitiesBrowser)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblURL.sizePolicy().hasHeightForWidth())
        self.lblURL.setSizePolicy(sizePolicy)
        self.lblURL.setObjectName("lblURL")
        self.horizontalLayout_2.addWidget(self.lblURL)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.txtCapabilities = QtGui.QTextBrowser(WMSCapabilitiesBrowser)
        self.txtCapabilities.setOpenExternalLinks(False)
        self.txtCapabilities.setObjectName("txtCapabilities")
        self.verticalLayout.addWidget(self.txtCapabilities)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btClose = QtGui.QPushButton(WMSCapabilitiesBrowser)
        self.btClose.setObjectName("btClose")
        self.horizontalLayout.addWidget(self.btClose)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(WMSCapabilitiesBrowser)
        QtCore.QObject.connect(self.btClose, QtCore.SIGNAL("clicked()"), WMSCapabilitiesBrowser.close)
        QtCore.QMetaObject.connectSlotsByName(WMSCapabilitiesBrowser)

    def retranslateUi(self, WMSCapabilitiesBrowser):
        WMSCapabilitiesBrowser.setWindowTitle(
            QtGui.QApplication.translate("WMSCapabilitiesBrowser", "Browse WMS Capabilities - DLR/IPA Mission Support",
                                         None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("WMSCapabilitiesBrowser", "Capabilities document of:", None,
                                                        QtGui.QApplication.UnicodeUTF8))
        self.lblURL.setText(
            QtGui.QApplication.translate("WMSCapabilitiesBrowser", "<URL>", None, QtGui.QApplication.UnicodeUTF8))
        self.btClose.setText(
            QtGui.QApplication.translate("WMSCapabilitiesBrowser", "close", None, QtGui.QApplication.UnicodeUTF8))
