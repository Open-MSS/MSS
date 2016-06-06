# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_sideview_window.ui'
#
# Created: Wed Mar  2 14:02:25 2011
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from mpl_qtwidget import MplSideViewWidget


class Ui_SideViewWindow(object):
    def setupUi(self, SideViewWindow):
        SideViewWindow.setObjectName("SideViewWindow")
        SideViewWindow.resize(931, 635)
        self.centralwidget = QtGui.QWidget(SideViewWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mpl = MplSideViewWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setObjectName("mpl")
        self.verticalLayout.addWidget(self.mpl)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btOptions = QtGui.QPushButton(self.centralwidget)
        self.btOptions.setObjectName("btOptions")
        self.horizontalLayout.addWidget(self.btOptions)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cbTools = QtGui.QComboBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbTools.sizePolicy().hasHeightForWidth())
        self.cbTools.setSizePolicy(sizePolicy)
        self.cbTools.setObjectName("cbTools")
        self.cbTools.addItem("")
        self.cbTools.addItem("")
        self.horizontalLayout.addWidget(self.cbTools)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.btMvWaypoint = QtGui.QToolButton(self.centralwidget)
        self.btMvWaypoint.setCheckable(True)
        self.btMvWaypoint.setChecked(True)
        self.btMvWaypoint.setAutoExclusive(True)
        self.btMvWaypoint.setObjectName("btMvWaypoint")
        self.horizontalLayout.addWidget(self.btMvWaypoint)
        self.btInsWaypoint = QtGui.QToolButton(self.centralwidget)
        self.btInsWaypoint.setEnabled(False)
        self.btInsWaypoint.setCheckable(True)
        self.btInsWaypoint.setAutoExclusive(True)
        self.btInsWaypoint.setObjectName("btInsWaypoint")
        self.horizontalLayout.addWidget(self.btInsWaypoint)
        self.btDelWaypoint = QtGui.QToolButton(self.centralwidget)
        self.btDelWaypoint.setCheckable(True)
        self.btDelWaypoint.setAutoExclusive(True)
        self.btDelWaypoint.setObjectName("btDelWaypoint")
        self.horizontalLayout.addWidget(self.btDelWaypoint)
        self.verticalLayout.addLayout(self.horizontalLayout)
        SideViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(SideViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 931, 26))
        self.menubar.setObjectName("menubar")
        SideViewWindow.setMenuBar(self.menubar)

        self.retranslateUi(SideViewWindow)
        QtCore.QMetaObject.connectSlotsByName(SideViewWindow)

    def retranslateUi(self, SideViewWindow):
        SideViewWindow.setWindowTitle(
            QtGui.QApplication.translate("SideViewWindow", "Side View - DLR/IPA Mission Support", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.btOptions.setText(
            QtGui.QApplication.translate("SideViewWindow", "options", None, QtGui.QApplication.UnicodeUTF8))
        self.cbTools.setItemText(0, QtGui.QApplication.translate("SideViewWindow", "(select to open control)", None,
                                                                 QtGui.QApplication.UnicodeUTF8))
        self.cbTools.setItemText(1, QtGui.QApplication.translate("SideViewWindow", "WMS", None,
                                                                 QtGui.QApplication.UnicodeUTF8))
        self.label.setText(
            QtGui.QApplication.translate("SideViewWindow", "Waypoint edit mode:", None, QtGui.QApplication.UnicodeUTF8))
        self.btMvWaypoint.setText(
            QtGui.QApplication.translate("SideViewWindow", "Mv", None, QtGui.QApplication.UnicodeUTF8))
        self.btMvWaypoint.setShortcut(
            QtGui.QApplication.translate("SideViewWindow", "M", None, QtGui.QApplication.UnicodeUTF8))
        self.btInsWaypoint.setText(
            QtGui.QApplication.translate("SideViewWindow", "Ins", None, QtGui.QApplication.UnicodeUTF8))
        self.btInsWaypoint.setShortcut(
            QtGui.QApplication.translate("SideViewWindow", "I", None, QtGui.QApplication.UnicodeUTF8))
        self.btDelWaypoint.setText(
            QtGui.QApplication.translate("SideViewWindow", "Del", None, QtGui.QApplication.UnicodeUTF8))
        self.btDelWaypoint.setShortcut(
            QtGui.QApplication.translate("SideViewWindow", "D", None, QtGui.QApplication.UnicodeUTF8))
