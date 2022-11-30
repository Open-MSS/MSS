# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_linearview_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LinearWindow(object):
    def setupUi(self, LinearWindow):
        LinearWindow.setObjectName("LinearWindow")
        LinearWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(LinearWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mpl = MplLinearViewWidget(self.centralwidget)
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
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.lvoptionbtn = QtWidgets.QPushButton(self.centralwidget)
        self.lvoptionbtn.setObjectName("lvoptionbtn")
        self.horizontalLayout.addWidget(self.lvoptionbtn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        LinearWindow.setCentralWidget(self.centralwidget)
        self.actionCloseWindow = QtWidgets.QAction(LinearWindow)
        self.actionCloseWindow.setObjectName("actionCloseWindow")
        LinearWindow.addAction(self.actionCloseWindow)

        self.retranslateUi(LinearWindow)
        self.actionCloseWindow.triggered.connect(LinearWindow.close)
        QtCore.QMetaObject.connectSlotsByName(LinearWindow)

    def retranslateUi(self, LinearWindow):
        _translate = QtCore.QCoreApplication.translate
        LinearWindow.setWindowTitle(_translate("LinearWindow", "Linear View - Mission Support System"))
        self.cbTools.setItemText(0, _translate("LinearWindow", "(select to open control)"))
        self.cbTools.setItemText(1, _translate("LinearWindow", "WMS"))
        self.lvoptionbtn.setText(_translate("LinearWindow", "options"))
        self.actionCloseWindow.setText(_translate("LinearWindow", "CloseWindow"))
        self.actionCloseWindow.setShortcut(_translate("LinearWindow", "Ctrl+W"))
from mslib.msui.mpl_qtwidget import MplLinearViewWidget
