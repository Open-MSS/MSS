# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_topview_window.ui'
#
# Created: Wed Mar  2 14:02:18 2011
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from mpl_qtwidget import MplTopViewWidget


class Ui_TopViewWindow(object):
    def setupUi(self, TopViewWindow):
        TopViewWindow.setObjectName("TopViewWindow")
        TopViewWindow.resize(952, 782)
        self.centralwidget = QtGui.QWidget(TopViewWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mpl = MplTopViewWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setObjectName("mpl")
        self.horizontalLayout_2.addWidget(self.mpl)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btMapRedraw = QtGui.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.btMapRedraw.setFont(font)
        self.btMapRedraw.setFlat(False)
        self.btMapRedraw.setObjectName("btMapRedraw")
        self.horizontalLayout.addWidget(self.btMapRedraw)
        self.btSettings = QtGui.QPushButton(self.centralwidget)
        self.btSettings.setObjectName("btSettings")
        self.horizontalLayout.addWidget(self.btSettings)
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
        self.cbChangeMapSection = QtGui.QComboBox(self.centralwidget)
        self.cbChangeMapSection.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cbChangeMapSection.setObjectName("cbChangeMapSection")
        self.cbChangeMapSection.addItem("")
        self.cbChangeMapSection.addItem("")
        self.cbChangeMapSection.addItem("")
        self.cbChangeMapSection.addItem("")
        self.cbChangeMapSection.addItem("")
        self.cbChangeMapSection.addItem("")
        self.cbChangeMapSection.addItem("")
        self.horizontalLayout.addWidget(self.cbChangeMapSection)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
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
        TopViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TopViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 952, 26))
        self.menubar.setObjectName("menubar")
        TopViewWindow.setMenuBar(self.menubar)

        self.retranslateUi(TopViewWindow)
        QtCore.QMetaObject.connectSlotsByName(TopViewWindow)

    def retranslateUi(self, TopViewWindow):
        TopViewWindow.setWindowTitle(
            QtGui.QApplication.translate("TopViewWindow", "Top View - DLR/IPA Mission Support", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.btMapRedraw.setText(
            QtGui.QApplication.translate("TopViewWindow", "&REDRAW MAP", None, QtGui.QApplication.UnicodeUTF8))
        self.btMapRedraw.setShortcut(
            QtGui.QApplication.translate("TopViewWindow", "R", None, QtGui.QApplication.UnicodeUTF8))
        self.btSettings.setText(
            QtGui.QApplication.translate("TopViewWindow", "map appearance", None, QtGui.QApplication.UnicodeUTF8))
        self.cbTools.setItemText(0, QtGui.QApplication.translate("TopViewWindow", "(select to open tool)", None,
                                                                 QtGui.QApplication.UnicodeUTF8))
        self.cbTools.setItemText(1, QtGui.QApplication.translate("TopViewWindow", "WMS", None,
                                                                 QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(0, QtGui.QApplication.translate("TopViewWindow",
                                                                            "to reset map select a region", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(1, QtGui.QApplication.translate("TopViewWindow", "Spitsbergen, large", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(2, QtGui.QApplication.translate("TopViewWindow", "Spitsbergen, local", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(3, QtGui.QApplication.translate("TopViewWindow", "Europe (ste)", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(4, QtGui.QApplication.translate("TopViewWindow", "Germany (ste)", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(5, QtGui.QApplication.translate("TopViewWindow", "Europe (cyl)", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.cbChangeMapSection.setItemText(6, QtGui.QApplication.translate("TopViewWindow", "Germany (cyl)", None,
                                                                            QtGui.QApplication.UnicodeUTF8))
        self.label.setText(
            QtGui.QApplication.translate("TopViewWindow", "waypoint edit mode:", None, QtGui.QApplication.UnicodeUTF8))
        self.btMvWaypoint.setText(
            QtGui.QApplication.translate("TopViewWindow", "&Mv", None, QtGui.QApplication.UnicodeUTF8))
        self.btMvWaypoint.setShortcut(
            QtGui.QApplication.translate("TopViewWindow", "M", None, QtGui.QApplication.UnicodeUTF8))
        self.btInsWaypoint.setText(
            QtGui.QApplication.translate("TopViewWindow", "&Ins", None, QtGui.QApplication.UnicodeUTF8))
        self.btInsWaypoint.setShortcut(
            QtGui.QApplication.translate("TopViewWindow", "I", None, QtGui.QApplication.UnicodeUTF8))
        self.btDelWaypoint.setText(
            QtGui.QApplication.translate("TopViewWindow", "&Del", None, QtGui.QApplication.UnicodeUTF8))
        self.btDelWaypoint.setShortcut(
            QtGui.QApplication.translate("TopViewWindow", "D", None, QtGui.QApplication.UnicodeUTF8))



