# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_1dview_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_OneDWindow(object):
    def setupUi(self, OneDWindow):
        OneDWindow.setObjectName("OneDWindow")
        OneDWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(OneDWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mpl = Mpl1DViewWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setMinimumSize(QtCore.QSize(100, 100))
        self.mpl.setObjectName("mpl")
        self.verticalLayout.addWidget(self.mpl)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btOptions = QtWidgets.QPushButton(self.centralwidget)
        self.btOptions.setObjectName("btOptions")
        self.horizontalLayout.addWidget(self.btOptions)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cbTools = QtWidgets.QComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbTools.sizePolicy().hasHeightForWidth())
        self.cbTools.setSizePolicy(sizePolicy)
        self.cbTools.setObjectName("cbTools")
        self.cbTools.addItem("")
        self.cbTools.addItem("")
        self.horizontalLayout.addWidget(self.cbTools)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        OneDWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(OneDWindow)
        QtCore.QMetaObject.connectSlotsByName(OneDWindow)

    def retranslateUi(self, OneDWindow):
        _translate = QtCore.QCoreApplication.translate
        OneDWindow.setWindowTitle(_translate("OneDWindow", "1D View - Mission Support System"))
        self.btOptions.setText(_translate("OneDWindow", "options"))
        self.cbTools.setItemText(0, _translate("OneDWindow", "(select to open control)"))
        self.cbTools.setItemText(1, _translate("OneDWindow", "WMS"))
from mslib.msui.mpl_qtwidget import Mpl1DViewWidget
