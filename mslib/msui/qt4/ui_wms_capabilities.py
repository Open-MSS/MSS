# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_wms_capabilities.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_WMSCapabilitiesBrowser(object):
    def setupUi(self, WMSCapabilitiesBrowser):
        WMSCapabilitiesBrowser.setObjectName(_fromUtf8("WMSCapabilitiesBrowser"))
        WMSCapabilitiesBrowser.resize(754, 393)
        self.verticalLayout = QtGui.QVBoxLayout(WMSCapabilitiesBrowser)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(WMSCapabilitiesBrowser)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.lblURL = QtGui.QLabel(WMSCapabilitiesBrowser)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblURL.sizePolicy().hasHeightForWidth())
        self.lblURL.setSizePolicy(sizePolicy)
        self.lblURL.setObjectName(_fromUtf8("lblURL"))
        self.horizontalLayout_2.addWidget(self.lblURL)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.txtCapabilities = QtGui.QTextBrowser(WMSCapabilitiesBrowser)
        self.txtCapabilities.setOpenExternalLinks(False)
        self.txtCapabilities.setObjectName(_fromUtf8("txtCapabilities"))
        self.verticalLayout.addWidget(self.txtCapabilities)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.cbFullView = QtGui.QCheckBox(WMSCapabilitiesBrowser)
        self.cbFullView.setObjectName(_fromUtf8("cbFullView"))
        self.horizontalLayout.addWidget(self.cbFullView)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btClose = QtGui.QPushButton(WMSCapabilitiesBrowser)
        self.btClose.setObjectName(_fromUtf8("btClose"))
        self.horizontalLayout.addWidget(self.btClose)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(WMSCapabilitiesBrowser)
        QtCore.QObject.connect(self.btClose, QtCore.SIGNAL(_fromUtf8("clicked()")), WMSCapabilitiesBrowser.close)
        QtCore.QMetaObject.connectSlotsByName(WMSCapabilitiesBrowser)

    def retranslateUi(self, WMSCapabilitiesBrowser):
        WMSCapabilitiesBrowser.setWindowTitle(_translate("WMSCapabilitiesBrowser", "Browse WMS Capabilities - Mission Support System", None))
        self.label.setText(_translate("WMSCapabilitiesBrowser", "Capabilities document of:", None))
        self.lblURL.setText(_translate("WMSCapabilitiesBrowser", "<URL>", None))
        self.cbFullView.setText(_translate("WMSCapabilitiesBrowser", "show full XML document", None))
        self.btClose.setText(_translate("WMSCapabilitiesBrowser", "close", None))

