# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_sideview_window.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SideViewWindow(object):
    def setupUi(self, SideViewWindow):
        SideViewWindow.setObjectName("SideViewWindow")
        SideViewWindow.resize(931, 635)
        self.centralwidget = QtWidgets.QWidget(SideViewWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mpl = MplSideViewWidget(self.centralwidget)
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
        SideViewWindow.setCentralWidget(self.centralwidget)
        self.actionCloseWindow = QtWidgets.QAction(SideViewWindow)
        self.actionCloseWindow.setObjectName("actionCloseWindow")
        SideViewWindow.addAction(self.actionCloseWindow)

        self.retranslateUi(SideViewWindow)
        self.actionCloseWindow.triggered.connect(SideViewWindow.close)
        QtCore.QMetaObject.connectSlotsByName(SideViewWindow)

    def retranslateUi(self, SideViewWindow):
        _translate = QtCore.QCoreApplication.translate
        SideViewWindow.setWindowTitle(_translate("SideViewWindow", "Side View - Mission Support System"))
        self.btOptions.setText(_translate("SideViewWindow", "options"))
        self.cbTools.setItemText(0, _translate("SideViewWindow", "(select to open control)"))
        self.cbTools.setItemText(1, _translate("SideViewWindow", "WMS"))
        self.actionCloseWindow.setText(_translate("SideViewWindow", "CloseWindow"))
        self.actionCloseWindow.setShortcut(_translate("SideViewWindow", "Ctrl+W"))

from mslib.msui.mpl_qtwidget import MplSideViewWidget
