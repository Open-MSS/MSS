# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_sideview_window.ui'
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

class Ui_SideViewWindow(object):
    def setupUi(self, SideViewWindow):
        SideViewWindow.setObjectName(_fromUtf8("SideViewWindow"))
        SideViewWindow.resize(931, 635)
        self.centralwidget = QtGui.QWidget(SideViewWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.mpl = MplSideViewWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setMinimumSize(QtCore.QSize(100, 100))
        self.mpl.setObjectName(_fromUtf8("mpl"))
        self.verticalLayout.addWidget(self.mpl)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btOptions = QtGui.QPushButton(self.centralwidget)
        self.btOptions.setObjectName(_fromUtf8("btOptions"))
        self.horizontalLayout.addWidget(self.btOptions)
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
        self.btInsWaypoint.setEnabled(False)
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
        SideViewWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(SideViewWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 931, 26))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        SideViewWindow.setMenuBar(self.menubar)

        self.retranslateUi(SideViewWindow)
        QtCore.QMetaObject.connectSlotsByName(SideViewWindow)

    def retranslateUi(self, SideViewWindow):
        SideViewWindow.setWindowTitle(_translate("SideViewWindow", "Side View - Mission Support System", None))
        self.btOptions.setText(_translate("SideViewWindow", "options", None))
        self.cbTools.setItemText(0, _translate("SideViewWindow", "(select to open control)", None))
        self.cbTools.setItemText(1, _translate("SideViewWindow", "WMS", None))
        self.label.setText(_translate("SideViewWindow", "Waypoint edit mode:", None))
        self.btMvWaypoint.setText(_translate("SideViewWindow", "Mv", None))
        self.btMvWaypoint.setShortcut(_translate("SideViewWindow", "M", None))
        self.btInsWaypoint.setText(_translate("SideViewWindow", "Ins", None))
        self.btInsWaypoint.setShortcut(_translate("SideViewWindow", "I", None))
        self.btDelWaypoint.setText(_translate("SideViewWindow", "Del", None))
        self.btDelWaypoint.setShortcut(_translate("SideViewWindow", "D", None))

from mslib.msui.mpl_qtwidget import MplSideViewWidget
