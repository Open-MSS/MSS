# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_3Dview_window.ui'
#
# Created: Fri Aug  6 11:02:26 2010
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from mss3Dwidget import MSS3DWidget

class Ui_View3DWindow(object):
    def setupUi(self, View3DWindow):
        View3DWindow.setObjectName("View3DWindow")
        View3DWindow.resize(695, 482)
        self.centralwidget = QtGui.QWidget(View3DWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.opengl_viewport = MSS3DWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.opengl_viewport.sizePolicy().hasHeightForWidth())
        self.opengl_viewport.setSizePolicy(sizePolicy)
        self.opengl_viewport.setObjectName("opengl_viewport")
        self.verticalLayout_2.addWidget(self.opengl_viewport)
        self.tab3DView = QtGui.QTabWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab3DView.sizePolicy().hasHeightForWidth())
        self.tab3DView.setSizePolicy(sizePolicy)
        self.tab3DView.setMinimumSize(QtCore.QSize(0, 100))
        self.tab3DView.setObjectName("tab3DView")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.tab3DView.addTab(self.tab_3, "")
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.tab3DView.addTab(self.tab_4, "")
        self.verticalLayout_2.addWidget(self.tab3DView)
        View3DWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(View3DWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 695, 26))
        self.menubar.setObjectName("menubar")
        View3DWindow.setMenuBar(self.menubar)

        self.retranslateUi(View3DWindow)
        self.tab3DView.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(View3DWindow)

    def retranslateUi(self, View3DWindow):
        View3DWindow.setWindowTitle(
            QtGui.QApplication.translate("View3DWindow", "3D View - DLR/IPA Mission Support", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.tab3DView.setTabText(self.tab3DView.indexOf(self.tab_3),
                                  QtGui.QApplication.translate("View3DWindow", "Flight Track", None,
                                                               QtGui.QApplication.UnicodeUTF8))
        self.tab3DView.setTabText(self.tab3DView.indexOf(self.tab_4),
                                  QtGui.QApplication.translate("View3DWindow", "Terrain", None,
                                                               QtGui.QApplication.UnicodeUTF8))



