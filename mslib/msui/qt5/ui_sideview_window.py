# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_sideview_window.ui'
#
# Created by: PyQt5 UI code generator 5.6
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
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
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
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.btMvWaypoint = QtWidgets.QToolButton(self.centralwidget)
        self.btMvWaypoint.setCheckable(True)
        self.btMvWaypoint.setChecked(True)
        self.btMvWaypoint.setAutoExclusive(True)
        self.btMvWaypoint.setObjectName("btMvWaypoint")
        self.horizontalLayout.addWidget(self.btMvWaypoint)
        self.btInsWaypoint = QtWidgets.QToolButton(self.centralwidget)
        self.btInsWaypoint.setEnabled(False)
        self.btInsWaypoint.setCheckable(True)
        self.btInsWaypoint.setAutoExclusive(True)
        self.btInsWaypoint.setObjectName("btInsWaypoint")
        self.horizontalLayout.addWidget(self.btInsWaypoint)
        self.btDelWaypoint = QtWidgets.QToolButton(self.centralwidget)
        self.btDelWaypoint.setCheckable(True)
        self.btDelWaypoint.setAutoExclusive(True)
        self.btDelWaypoint.setObjectName("btDelWaypoint")
        self.horizontalLayout.addWidget(self.btDelWaypoint)
        self.verticalLayout.addLayout(self.horizontalLayout)
        SideViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(SideViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 931, 26))
        self.menubar.setObjectName("menubar")
        SideViewWindow.setMenuBar(self.menubar)

        self.retranslateUi(SideViewWindow)
        QtCore.QMetaObject.connectSlotsByName(SideViewWindow)

    def retranslateUi(self, SideViewWindow):
        _translate = QtCore.QCoreApplication.translate
        SideViewWindow.setWindowTitle(_translate("SideViewWindow", "Side View - Mission Support System"))
        self.btOptions.setText(_translate("SideViewWindow", "options"))
        self.cbTools.setItemText(0, _translate("SideViewWindow", "(select to open control)"))
        self.cbTools.setItemText(1, _translate("SideViewWindow", "WMS"))
        self.label.setText(_translate("SideViewWindow", "Waypoint edit mode:"))
        self.btMvWaypoint.setText(_translate("SideViewWindow", "Mv"))
        self.btMvWaypoint.setShortcut(_translate("SideViewWindow", "M"))
        self.btInsWaypoint.setText(_translate("SideViewWindow", "Ins"))
        self.btInsWaypoint.setShortcut(_translate("SideViewWindow", "I"))
        self.btDelWaypoint.setText(_translate("SideViewWindow", "Del"))
        self.btDelWaypoint.setShortcut(_translate("SideViewWindow", "D"))

from mslib.msui.mpl_qtwidget import MplSideViewWidget
