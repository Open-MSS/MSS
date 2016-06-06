# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_loopwindow.ui'
#
# Created: Wed Sep  8 12:41:56 2010
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui


class Ui_ImageLoopWindow(object):
    def setupUi(self, ImageLoopWindow):
        ImageLoopWindow.setObjectName("ImageLoopWindow")
        ImageLoopWindow.resize(1042, 717)
        self.centralwidget = QtGui.QWidget(ImageLoopWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.dteValidTime = QtGui.QDateTimeEdit(self.centralwidget)
        self.dteValidTime.setMinimumSize(QtCore.QSize(220, 0))
        self.dteValidTime.setMaximumSize(QtCore.QSize(160, 16777215))
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setWeight(75)
        font.setItalic(False)
        font.setBold(True)
        self.dteValidTime.setFont(font)
        self.dteValidTime.setReadOnly(True)
        self.dteValidTime.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.dteValidTime.setDate(QtCore.QDate(2010, 1, 22))
        self.dteValidTime.setMinimumDateTime(QtCore.QDateTime(QtCore.QDate(2000, 1, 1), QtCore.QTime(12, 0, 0)))
        self.dteValidTime.setMinimumDate(QtCore.QDate(2000, 1, 1))
        self.dteValidTime.setMinimumTime(QtCore.QTime(12, 0, 0))
        self.dteValidTime.setCalendarPopup(False)
        self.dteValidTime.setTimeSpec(QtCore.Qt.UTC)
        self.dteValidTime.setObjectName("dteValidTime")
        self.horizontalLayout_3.addWidget(self.dteValidTime)
        self.tbValidTime_back = QtGui.QToolButton(self.centralwidget)
        self.tbValidTime_back.setArrowType(QtCore.Qt.LeftArrow)
        self.tbValidTime_back.setObjectName("tbValidTime_back")
        self.horizontalLayout_3.addWidget(self.tbValidTime_back)
        self.cbVTStep = QtGui.QComboBox(self.centralwidget)
        self.cbVTStep.setObjectName("cbVTStep")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.cbVTStep.addItem("")
        self.horizontalLayout_3.addWidget(self.cbVTStep)
        self.tbValidTime_fwd = QtGui.QToolButton(self.centralwidget)
        self.tbValidTime_fwd.setArrowType(QtCore.Qt.RightArrow)
        self.tbValidTime_fwd.setObjectName("tbValidTime_fwd")
        self.horizontalLayout_3.addWidget(self.tbValidTime_fwd)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.centralFrame = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralFrame.sizePolicy().hasHeightForWidth())
        self.centralFrame.setSizePolicy(sizePolicy)
        self.centralFrame.setFrameShape(QtGui.QFrame.Box)
        self.centralFrame.setFrameShadow(QtGui.QFrame.Plain)
        self.centralFrame.setObjectName("centralFrame")
        self.verticalLayout.addWidget(self.centralFrame)
        ImageLoopWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(ImageLoopWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1042, 26))
        self.menubar.setObjectName("menubar")
        self.menu_File = QtGui.QMenu(self.menubar)
        self.menu_File.setObjectName("menu_File")
        self.menu_Layout = QtGui.QMenu(self.menubar)
        self.menu_Layout.setObjectName("menu_Layout")
        ImageLoopWindow.setMenuBar(self.menubar)
        self.statusBar = QtGui.QStatusBar(ImageLoopWindow)
        self.statusBar.setObjectName("statusBar")
        ImageLoopWindow.setStatusBar(self.statusBar)
        self.actionE_xit = QtGui.QAction(ImageLoopWindow)
        self.actionE_xit.setObjectName("actionE_xit")
        self.actionSingleView = QtGui.QAction(ImageLoopWindow)
        self.actionSingleView.setObjectName("actionSingleView")
        self.actionDualView = QtGui.QAction(ImageLoopWindow)
        self.actionDualView.setObjectName("actionDualView")
        self.actionOneLargeTwoSmall = QtGui.QAction(ImageLoopWindow)
        self.actionOneLargeTwoSmall.setObjectName("actionOneLargeTwoSmall")
        self.actionOneLargeThreeSmall = QtGui.QAction(ImageLoopWindow)
        self.actionOneLargeThreeSmall.setObjectName("actionOneLargeThreeSmall")
        self.actionQuadView = QtGui.QAction(ImageLoopWindow)
        self.actionQuadView.setObjectName("actionQuadView")
        self.menu_File.addAction(self.actionE_xit)
        self.menu_Layout.addAction(self.actionSingleView)
        self.menu_Layout.addAction(self.actionDualView)
        self.menu_Layout.addAction(self.actionOneLargeTwoSmall)
        self.menu_Layout.addAction(self.actionOneLargeThreeSmall)
        self.menu_Layout.addAction(self.actionQuadView)
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Layout.menuAction())

        self.retranslateUi(ImageLoopWindow)
        QtCore.QObject.connect(self.actionE_xit, QtCore.SIGNAL("triggered()"), ImageLoopWindow.close)
        QtCore.QMetaObject.connectSlotsByName(ImageLoopWindow)

    def retranslateUi(self, ImageLoopWindow):
        ImageLoopWindow.setWindowTitle(
            QtGui.QApplication.translate("ImageLoopWindow", "Loop View - DLR/IPA Mission Support", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ImageLoopWindow", "Synchronized Valid Time:", None,
                                                          QtGui.QApplication.UnicodeUTF8))
        self.dteValidTime.setDisplayFormat(QtGui.QApplication.translate("ImageLoopWindow", "yyyy-MM-dd hh:mm UTC", None,
                                                                        QtGui.QApplication.UnicodeUTF8))
        self.tbValidTime_back.setToolTip(
            QtGui.QApplication.translate("ImageLoopWindow", "decrement time", None, QtGui.QApplication.UnicodeUTF8))
        self.tbValidTime_back.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "<<", None, QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setToolTip(
            QtGui.QApplication.translate("ImageLoopWindow", "time step for changing the valid time", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(0, QtGui.QApplication.translate("ImageLoopWindow", "5 min", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(1, QtGui.QApplication.translate("ImageLoopWindow", "10 min", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(2, QtGui.QApplication.translate("ImageLoopWindow", "15 min", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(3, QtGui.QApplication.translate("ImageLoopWindow", "30 min", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(4, QtGui.QApplication.translate("ImageLoopWindow", "1 hour", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(5, QtGui.QApplication.translate("ImageLoopWindow", "3 hours", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(6, QtGui.QApplication.translate("ImageLoopWindow", "6 hours", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(7, QtGui.QApplication.translate("ImageLoopWindow", "12 hours", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.cbVTStep.setItemText(8, QtGui.QApplication.translate("ImageLoopWindow", "24 hours", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.tbValidTime_fwd.setToolTip(
            QtGui.QApplication.translate("ImageLoopWindow", "increment time", None, QtGui.QApplication.UnicodeUTF8))
        self.tbValidTime_fwd.setText(
            QtGui.QApplication.translate("ImageLoopWindow", ">>", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_File.setTitle(
            QtGui.QApplication.translate("ImageLoopWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Layout.setTitle(
            QtGui.QApplication.translate("ImageLoopWindow", "&Layout", None, QtGui.QApplication.UnicodeUTF8))
        self.actionE_xit.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "E&xit Module", None, QtGui.QApplication.UnicodeUTF8))
        self.actionE_xit.setShortcut(
            QtGui.QApplication.translate("ImageLoopWindow", "Ctrl+X", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSingleView.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "&Single View", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSingleView.setShortcut(
            QtGui.QApplication.translate("ImageLoopWindow", "Alt+1", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDualView.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "&Dual View", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDualView.setShortcut(
            QtGui.QApplication.translate("ImageLoopWindow", "Alt+2", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOneLargeTwoSmall.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "&One Large, Two Small", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.actionOneLargeTwoSmall.setShortcut(
            QtGui.QApplication.translate("ImageLoopWindow", "Alt+3", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOneLargeThreeSmall.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "One &Large, Three Small", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.actionOneLargeThreeSmall.setShortcut(
            QtGui.QApplication.translate("ImageLoopWindow", "Alt+4", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuadView.setText(
            QtGui.QApplication.translate("ImageLoopWindow", "&Quad View", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuadView.setShortcut(
            QtGui.QApplication.translate("ImageLoopWindow", "Alt+5", None, QtGui.QApplication.UnicodeUTF8))
