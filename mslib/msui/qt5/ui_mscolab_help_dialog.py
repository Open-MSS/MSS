# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_mscolab_help_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_mscolabHelpDialog(object):
    def setupUi(self, mscolabHelpDialog):
        mscolabHelpDialog.setObjectName("mscolabHelpDialog")
        mscolabHelpDialog.resize(710, 703)
        self.gridLayout = QtWidgets.QGridLayout(mscolabHelpDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(mscolabHelpDialog)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setObjectName("tabWidget")
        self.connectingTab = QtWidgets.QWidget()
        self.connectingTab.setObjectName("connectingTab")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.connectingTab)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setContentsMargins(-1, 10, -1, 10)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem)
        self.label_9 = QtWidgets.QLabel(self.connectingTab)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_8.addWidget(self.label_9)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_8)
        self.textEdit_17 = QtWidgets.QTextEdit(self.connectingTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textEdit_17.sizePolicy().hasHeightForWidth())
        self.textEdit_17.setSizePolicy(sizePolicy)
        self.textEdit_17.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_17.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_17.setReadOnly(True)
        self.textEdit_17.setObjectName("textEdit_17")
        self.verticalLayout_3.addWidget(self.textEdit_17)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem2)
        self.label_10 = QtWidgets.QLabel(self.connectingTab)
        self.label_10.setText("")
        self.label_10.setPixmap(QtGui.QPixmap(":/images/mscolab-help/connect.png"))
        self.label_10.setScaledContents(True)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_9.addWidget(self.label_10)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem3)
        self.verticalLayout_3.addLayout(self.horizontalLayout_9)
        self.textEdit_18 = QtWidgets.QTextEdit(self.connectingTab)
        self.textEdit_18.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_18.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_18.setReadOnly(True)
        self.textEdit_18.setObjectName("textEdit_18")
        self.verticalLayout_3.addWidget(self.textEdit_18)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setContentsMargins(-1, -1, -1, 8)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem4)
        self.label_12 = QtWidgets.QLabel(self.connectingTab)
        self.label_12.setText("")
        self.label_12.setPixmap(QtGui.QPixmap(":/images/mscolab-help/add-user.png"))
        self.label_12.setScaledContents(True)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_10.addWidget(self.label_12)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem5)
        self.verticalLayout_3.addLayout(self.horizontalLayout_10)
        self.verticalLayout_3.setStretch(1, 1)
        self.verticalLayout_3.setStretch(3, 1)
        self.gridLayout_4.addLayout(self.verticalLayout_3, 0, 0, 1, 1)
        self.tabWidget.addTab(self.connectingTab, "")
        self.createProjectTab = QtWidgets.QWidget()
        self.createProjectTab.setObjectName("createProjectTab")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.createProjectTab)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.textEdit_20 = QtWidgets.QTextEdit(self.createProjectTab)
        self.textEdit_20.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.textEdit_20.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_20.setReadOnly(True)
        self.textEdit_20.setObjectName("textEdit_20")
        self.verticalLayout_4.addWidget(self.textEdit_20)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem6)
        self.label_13 = QtWidgets.QLabel(self.createProjectTab)
        self.label_13.setText("")
        self.label_13.setPixmap(QtGui.QPixmap(":/images/mscolab-help/add-operation.png"))
        self.label_13.setScaledContents(True)
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_11.addWidget(self.label_13)
        spacerItem7 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem7)
        self.verticalLayout_4.addLayout(self.horizontalLayout_11)
        self.gridLayout_3.addLayout(self.verticalLayout_4, 0, 0, 1, 1)
        self.tabWidget.addTab(self.createProjectTab, "")
        self.adminTab = QtWidgets.QWidget()
        self.adminTab.setObjectName("adminTab")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.adminTab)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.textEdit_22 = QtWidgets.QTextEdit(self.adminTab)
        self.textEdit_22.setEnabled(True)
        self.textEdit_22.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.textEdit_22.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_22.setUndoRedoEnabled(False)
        self.textEdit_22.setReadOnly(True)
        self.textEdit_22.setObjectName("textEdit_22")
        self.verticalLayout_5.addWidget(self.textEdit_22)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        spacerItem8 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem8)
        self.label_14 = QtWidgets.QLabel(self.adminTab)
        self.label_14.setText("")
        self.label_14.setPixmap(QtGui.QPixmap(":/images/mscolab-help/admin-window.png"))
        self.label_14.setScaledContents(True)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_12.addWidget(self.label_14)
        spacerItem9 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem9)
        self.verticalLayout_5.addLayout(self.horizontalLayout_12)
        self.gridLayout_5.addLayout(self.verticalLayout_5, 0, 0, 1, 1)
        self.tabWidget.addTab(self.adminTab, "")
        self.chatTab = QtWidgets.QWidget()
        self.chatTab.setObjectName("chatTab")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.chatTab)
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.textEdit_23 = QtWidgets.QTextEdit(self.chatTab)
        self.textEdit_23.setEnabled(True)
        self.textEdit_23.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.textEdit_23.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_23.setUndoRedoEnabled(False)
        self.textEdit_23.setReadOnly(True)
        self.textEdit_23.setObjectName("textEdit_23")
        self.verticalLayout_6.addWidget(self.textEdit_23)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        spacerItem10 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem10)
        self.label = QtWidgets.QLabel(self.chatTab)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/images/mscolab-help/chat-window.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.horizontalLayout_13.addWidget(self.label)
        spacerItem11 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem11)
        self.verticalLayout_6.addLayout(self.horizontalLayout_13)
        self.gridLayout_7.addLayout(self.verticalLayout_6, 0, 0, 1, 1)
        self.tabWidget.addTab(self.chatTab, "")
        self.versionTab = QtWidgets.QWidget()
        self.versionTab.setObjectName("versionTab")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.versionTab)
        self.gridLayout_9.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.textEdit_24 = QtWidgets.QTextEdit(self.versionTab)
        self.textEdit_24.setEnabled(True)
        self.textEdit_24.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_24.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_24.setUndoRedoEnabled(False)
        self.textEdit_24.setReadOnly(True)
        self.textEdit_24.setObjectName("textEdit_24")
        self.verticalLayout_7.addWidget(self.textEdit_24)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        spacerItem12 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_14.addItem(spacerItem12)
        self.label_16 = QtWidgets.QLabel(self.versionTab)
        self.label_16.setText("")
        self.label_16.setPixmap(QtGui.QPixmap(":/images/mscolab-help/version-window.png"))
        self.label_16.setScaledContents(True)
        self.label_16.setObjectName("label_16")
        self.horizontalLayout_14.addWidget(self.label_16)
        spacerItem13 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_14.addItem(spacerItem13)
        self.verticalLayout_7.addLayout(self.horizontalLayout_14)
        self.gridLayout_9.addLayout(self.verticalLayout_7, 0, 0, 1, 1)
        self.tabWidget.addTab(self.versionTab, "")
        self.operationWorkTab = QtWidgets.QWidget()
        self.operationWorkTab.setObjectName("operationWorkTab")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.operationWorkTab)
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.textEdit_25 = QtWidgets.QTextEdit(self.operationWorkTab)
        self.textEdit_25.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.textEdit_25.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_25.setReadOnly(True)
        self.textEdit_25.setObjectName("textEdit_25")
        self.verticalLayout_8.addWidget(self.textEdit_25)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        spacerItem14 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem14)
        self.label_17 = QtWidgets.QLabel(self.operationWorkTab)
        self.label_17.setText("")
        self.label_17.setPixmap(QtGui.QPixmap(":/images/mscolab-help/merge-window.png"))
        self.label_17.setScaledContents(True)
        self.label_17.setObjectName("label_17")
        self.horizontalLayout_15.addWidget(self.label_17)
        spacerItem15 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem15)
        self.verticalLayout_8.addLayout(self.horizontalLayout_15)
        self.gridLayout_8.addLayout(self.verticalLayout_8, 0, 0, 1, 1)
        self.tabWidget.addTab(self.operationWorkTab, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem16 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem16)
        self.okayBtn = QtWidgets.QPushButton(mscolabHelpDialog)
        self.okayBtn.setObjectName("okayBtn")
        self.horizontalLayout.addWidget(self.okayBtn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(mscolabHelpDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(mscolabHelpDialog)

    def retranslateUi(self, mscolabHelpDialog):
        _translate = QtCore.QCoreApplication.translate
        mscolabHelpDialog.setWindowTitle(_translate("mscolabHelpDialog", "Help"))
        self.label_9.setText(_translate("mscolabHelpDialog", "Welcome to Mission Support Collaboration!"))
        self.textEdit_17.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">We suggest you go through this guide before you start using mscolab to understand all the features it has to offer.<br /><br />1. To get started, click on the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Connect to MSColab</span><span style=\" font-family:\'.SF NS Text\';\"> button on the main window.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">2. In the connect window that appears, enter your MSColab Server URL and press the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Connect</span><span style=\" font-family:\'.SF NS Text\';\"> button.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p></body></html>"))
        self.textEdit_18.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">If you\'re using MSColab for the first time, click on the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Add User&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> button after connecting and register yourself by filling the required details. </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">The status bar will notify if/not the new user is registered on the server. If successfully registered, you\'ll be taken to the login page where you can login with the new user credentials.</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.connectingTab), _translate("mscolabHelpDialog", "Connecting"))
        self.textEdit_20.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">1. Each flight track in mscolab is called a </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Project&quot;</span><span style=\" font-family:\'.SF NS Text\';\">. You can create your operation by clicking on the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;MSColab Project&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> menu under the &quot;New&quot; section of File menu and filling in the required details.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">2. The operation list shows all the operations you have access to along with your access level to the operation. There are </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">4 access levels</span><span style=\" font-family:\'.SF NS Text\';\"> you can have to a operation. These are: </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">    1. Creator</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">    2. Admin</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">    3. Collaborator</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">    4. Viewer</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">3. You can select a operation by </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">double-clicking</span><span style=\" font-family:\'.SF NS Text\';\"> on it in the operation list and then start working on it.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">4. Select a operation and you can start editing the flight track in 4 different views - Top, Side and Table, Linear. (Note: Already open views will automatically change the waypoints model to the newly selected operation\'s waypoints model)</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">5. You can use the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Import/Export</span><span style=\" font-family:\'.SF NS Text\';\"> menu from the &quot;File&quot; menu to import or export Flighttrack files in FTML/CSV or any other supported plugin format.</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.createProjectTab), _translate("mscolabHelpDialog", "Creating a Project"))
        self.textEdit_22.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">To collaborate with other users, you can add them to a operation if you are the creator of the operation or have administrator access. Click on the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Manage Users&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> sub-menu under the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Project menu</span><span style=\" font-family:\'.SF NS Text\';\">, after selecting the operation.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">A user can have 4 access levels:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">1. </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Creator</span><span style=\" font-family:\'.SF NS Text\';\"> - The user that creates the operation. This user\'s permission can\'t be changed. This user has all the access an Admin has and can also delete the operation.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">2. </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Admin</span><span style=\" font-family:\'.SF NS Text\';\"> - The admin has permission to add and update access levels of other users working on the operation. They can also view the version history of the operation and checkout to a previous version.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">3. </span><span style=\" font-weight:600;\">Collaborator</span> - The collaborator can edit the flight track path and use the version history but has no ability to manage users.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">4. </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Viewer</span><span style=\" font-family:\'.SF NS Text\';\"> - The viewer has the least access. They can only view the flight tracks and can\'t edit anything.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">What can you do with the Mscolab Admin Window?</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">1. Select users on your Mscolab server and add them to your operation or update the access level of existing users.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">2. Clone the permissions from a different operation using the clone button at the top, allowing your team to quickly get started on a new operation.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">3. Easily search users using the search bar. You can use the username or email id to search for a user.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">4. Apply filter based on access level to find exactly who you need.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.adminTab), _translate("mscolabHelpDialog", "Adding Users to Project"))
        self.textEdit_23.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">You can chat with all the users added to a operation by opening the chat window using the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Chat&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> sub-menu under the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Project menu</span><span style=\" font-family:\'.SF NS Text\';\">. You can send normal messages and upload images and documents as well. </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">You can also use common markdown syntax to format your messages.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">1. *text* for italics</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">2. **text** for bold</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">3. - for bullet list</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">4. # for heading</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">5. [text](url) for adding link to text</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">You can use the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Preview&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> button to preview how your message looks before sending it.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">There are other features supported like editing, deleting and replying to a message. Right click on any message to see these options.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.chatTab), _translate("mscolabHelpDialog", "Chat"))
        self.textEdit_24.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">You can keep track of all the changes made to your operation by opening the version history window using the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Version History&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> sub-menu under the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Project menu</span><span style=\" font-family:\'.SF NS Text\';\">.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">Every change made by any user working the operation is saved in the version history window. At any time you can revert to a preview version by just selecting the version from the list and clicking on the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Checkout&quot; </span><span style=\" font-family:\'.SF NS Text\';\">button.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">You can also give names to the important versions so you can view only the important named versions by changing the filter above the version list</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.versionTab), _translate("mscolabHelpDialog", "Manage Versions"))
        self.textEdit_25.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">While working on a operation you can be working in 2 modes:</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">1. The </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">default mode</span><span style=\" font-family:\'.SF NS Text\';\"> is when the  </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Work Asynchronously&quot; </span><span style=\" font-family:\'.SF NS Text\';\">checkbox is </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">unchecked</span><span style=\" font-family:\'.SF NS Text\';\">. In this mode all your changes will be shared with all other users in real-time. Each change made will also be recorded in the version history window in this mode.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">2. If you just want to try some changes on your own and not share with everyone else, you can turn the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Work Asynchronously&quot; </span><span style=\" font-family:\'.SF NS Text\';\">checkbox </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">on</span><span style=\" font-family:\'.SF NS Text\';\">. In work locally mode your changes are kept on your machine and not shared with anyone. Once you\'re done making changes you can use the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Save to Server&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> option in the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">Server Options drop-down list</span><span style=\" font-family:\'.SF NS Text\';\"> to save your changes with everyone. On clicking the save option a merge dialog is opened. Here you can choose to completely overwrite the shared flight track with your local one or choose what you want to keep from your local data and the shared data. You can also use the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Fetch from Server&quot; </span><span style=\" font-family:\'.SF NS Text\';\">option so you can merge the shared flight track data with your local data.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'.SF NS Text\';\">You can toggle between these modes at any moment you like. All your local changes are saved on your machine and are </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">not</span><span style=\" font-family:\'.SF NS Text\';\"> discarded. You can uncheck the </span><span style=\" font-family:\'.SF NS Text\'; font-weight:600;\">&quot;Work Asynchronously&quot;</span><span style=\" font-family:\'.SF NS Text\';\"> checkbox at any time, work on the shared file and then turn it back on and continue from where you left off.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\';\"><br /></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.operationWorkTab), _translate("mscolabHelpDialog", "Working on a Project"))
        self.okayBtn.setText(_translate("mscolabHelpDialog", "Okay"))

from . import resources_rc
