# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_topview_window.ui'
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

class Ui_TopViewWindow(object):
    def setupUi(self, TopViewWindow):
        TopViewWindow.setObjectName(_fromUtf8("TopViewWindow"))
        TopViewWindow.resize(952, 782)
        self.centralwidget = QtGui.QWidget(TopViewWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.mpl = MplTopViewWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setObjectName(_fromUtf8("mpl"))
        self.horizontalLayout_2.addWidget(self.mpl)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btMapRedraw = QtGui.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.btMapRedraw.setFont(font)
        self.btMapRedraw.setFlat(False)
        self.btMapRedraw.setObjectName(_fromUtf8("btMapRedraw"))
        self.horizontalLayout.addWidget(self.btMapRedraw)
        self.btSettings = QtGui.QPushButton(self.centralwidget)
        self.btSettings.setObjectName(_fromUtf8("btSettings"))
        self.horizontalLayout.addWidget(self.btSettings)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cbTools = QtGui.QComboBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbTools.sizePolicy().hasHeightForWidth())
        self.cbTools.setSizePolicy(sizePolicy)
        self.cbTools.setObjectName(_fromUtf8("cbTools"))
        self.cbTools.addItem(_fromUtf8(""))
        self.cbTools.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.cbTools)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.cbChangeMapSection = QtGui.QComboBox(self.centralwidget)
        self.cbChangeMapSection.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cbChangeMapSection.setObjectName(_fromUtf8("cbChangeMapSection"))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.cbChangeMapSection.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.cbChangeMapSection)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.btMvWaypoint = QtGui.QToolButton(self.centralwidget)
        self.btMvWaypoint.setCheckable(True)
        self.btMvWaypoint.setChecked(True)
        self.btMvWaypoint.setAutoExclusive(True)
        self.btMvWaypoint.setObjectName(_fromUtf8("btMvWaypoint"))
        self.horizontalLayout.addWidget(self.btMvWaypoint)
        self.btInsWaypoint = QtGui.QToolButton(self.centralwidget)
        self.btInsWaypoint.setCheckable(True)
        self.btInsWaypoint.setAutoExclusive(True)
        self.btInsWaypoint.setObjectName(_fromUtf8("btInsWaypoint"))
        self.horizontalLayout.addWidget(self.btInsWaypoint)
        self.btDelWaypoint = QtGui.QToolButton(self.centralwidget)
        self.btDelWaypoint.setCheckable(True)
        self.btDelWaypoint.setAutoExclusive(True)
        self.btDelWaypoint.setObjectName(_fromUtf8("btDelWaypoint"))
        self.horizontalLayout.addWidget(self.btDelWaypoint)
        self.verticalLayout.addLayout(self.horizontalLayout)
        TopViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TopViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 952, 26))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        TopViewWindow.setMenuBar(self.menubar)

        self.retranslateUi(TopViewWindow)
        QtCore.QMetaObject.connectSlotsByName(TopViewWindow)

    def retranslateUi(self, TopViewWindow):
        TopViewWindow.setWindowTitle(_translate("TopViewWindow", "Top View - Mission Support System", None))
        self.btMapRedraw.setText(_translate("TopViewWindow", "&REDRAW MAP", None))
        self.btMapRedraw.setShortcut(_translate("TopViewWindow", "R", None))
        self.btSettings.setText(_translate("TopViewWindow", "map appearance", None))
        self.cbTools.setItemText(0, _translate("TopViewWindow", "(select to open tool)", None))
        self.cbTools.setItemText(1, _translate("TopViewWindow", "WMS", None))
        self.cbChangeMapSection.setItemText(0, _translate("TopViewWindow", "to reset map select a region", None))
        self.cbChangeMapSection.setItemText(1, _translate("TopViewWindow", "Spitsbergen, large", None))
        self.cbChangeMapSection.setItemText(2, _translate("TopViewWindow", "Spitsbergen, local", None))
        self.cbChangeMapSection.setItemText(3, _translate("TopViewWindow", "Europe (ste)", None))
        self.cbChangeMapSection.setItemText(4, _translate("TopViewWindow", "Germany (ste)", None))
        self.cbChangeMapSection.setItemText(5, _translate("TopViewWindow", "Europe (cyl)", None))
        self.cbChangeMapSection.setItemText(6, _translate("TopViewWindow", "Germany (cyl)", None))
        self.label.setText(_translate("TopViewWindow", "waypoint edit mode:", None))
        self.btMvWaypoint.setText(_translate("TopViewWindow", "&Mv", None))
        self.btMvWaypoint.setShortcut(_translate("TopViewWindow", "M", None))
        self.btInsWaypoint.setText(_translate("TopViewWindow", "&Ins", None))
        self.btInsWaypoint.setShortcut(_translate("TopViewWindow", "I", None))
        self.btDelWaypoint.setText(_translate("TopViewWindow", "&Del", None))
        self.btDelWaypoint.setShortcut(_translate("TopViewWindow", "D", None))

from mslib.msui.mpl_qtwidget import MplTopViewWidget
