# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MSSMscolabWindow(object):
    def setupUi(self, MSSMscolabWindow):
        MSSMscolabWindow.setObjectName("MSSMscolabWindow")
        MSSMscolabWindow.resize(570, 629)
        MSSMscolabWindow.setMinimumSize(QtCore.QSize(510, 510))
        self.centralwidget = QtWidgets.QWidget(MSSMscolabWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QtCore.QSize(500, 500))
        self.groupBox.setStyleSheet("margin-top")
        self.groupBox.setTitle("")
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.urlWidget = QtWidgets.QWidget(self.groupBox)
        self.urlWidget.setObjectName("urlWidget")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.urlWidget)
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_2 = QtWidgets.QLabel(self.urlWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_5.addWidget(self.label_2)
        self.url = QtWidgets.QComboBox(self.urlWidget)
        self.url.setObjectName("url")
        self.horizontalLayout_5.addWidget(self.url)
        self.toggleConnectionBtn = QtWidgets.QPushButton(self.urlWidget)
        self.toggleConnectionBtn.setObjectName("toggleConnectionBtn")
        self.horizontalLayout_5.addWidget(self.toggleConnectionBtn)
        self.horizontalLayout_5.setStretch(1, 2)
        self.horizontalLayout_5.setStretch(2, 1)
        self.verticalLayout_9.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.status = QtWidgets.QLabel(self.urlWidget)
        self.status.setObjectName("status")
        self.horizontalLayout_6.addWidget(self.status)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem)
        self.verticalLayout_9.addLayout(self.horizontalLayout_6)
        self.verticalLayout_3.addWidget(self.urlWidget)
        self.loggedInWidget = QtWidgets.QWidget(self.groupBox)
        self.loggedInWidget.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loggedInWidget.sizePolicy().hasHeightForWidth())
        self.loggedInWidget.setSizePolicy(sizePolicy)
        self.loggedInWidget.setObjectName("loggedInWidget")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.loggedInWidget)
        self.horizontalLayout_7.setContentsMargins(0, -1, 0, -1)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label = QtWidgets.QLabel(self.loggedInWidget)
        self.label.setMaximumSize(QtCore.QSize(300, 16777215))
        self.label.setObjectName("label")
        self.horizontalLayout_7.addWidget(self.label)
        self.logoutButton = QtWidgets.QPushButton(self.loggedInWidget)
        self.logoutButton.setObjectName("logoutButton")
        self.horizontalLayout_7.addWidget(self.logoutButton)
        self.deleteAccountButton = QtWidgets.QPushButton(self.loggedInWidget)
        self.deleteAccountButton.setObjectName("deleteAccountButton")
        self.horizontalLayout_7.addWidget(self.deleteAccountButton)
        spacerItem1 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem1)
        self.verticalLayout_3.addWidget(self.loggedInWidget)
        self.loginWidget = QtWidgets.QWidget(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loginWidget.sizePolicy().hasHeightForWidth())
        self.loginWidget.setSizePolicy(sizePolicy)
        self.loginWidget.setObjectName("loginWidget")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.loginWidget)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.emailid = QtWidgets.QLineEdit(self.loginWidget)
        self.emailid.setObjectName("emailid")
        self.horizontalLayout_3.addWidget(self.emailid)
        self.password = QtWidgets.QLineEdit(self.loginWidget)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.horizontalLayout_3.addWidget(self.password)
        self.loginButton = QtWidgets.QPushButton(self.loginWidget)
        self.loginButton.setObjectName("loginButton")
        self.horizontalLayout_3.addWidget(self.loginButton)
        self.addUser = QtWidgets.QPushButton(self.loginWidget)
        self.addUser.setMaximumSize(QtCore.QSize(80, 16777215))
        self.addUser.setObjectName("addUser")
        self.horizontalLayout_3.addWidget(self.addUser)
        self.verticalLayout_8.addLayout(self.horizontalLayout_3)
        self.verticalLayout_3.addWidget(self.loginWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.helperTextLabel = QtWidgets.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.helperTextLabel.setFont(font)
        self.helperTextLabel.setText("")
        self.helperTextLabel.setWordWrap(True)
        self.helperTextLabel.setObjectName("helperTextLabel")
        self.verticalLayout.addWidget(self.helperTextLabel)
        self.listProjects = QtWidgets.QListWidget(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listProjects.sizePolicy().hasHeightForWidth())
        self.listProjects.setSizePolicy(sizePolicy)
        self.listProjects.setAlternatingRowColors(False)
        self.listProjects.setTextElideMode(QtCore.Qt.ElideNone)
        self.listProjects.setObjectName("listProjects")
        self.verticalLayout.addWidget(self.listProjects)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.linearview = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.linearview.sizePolicy().hasHeightForWidth())
        self.linearview.setSizePolicy(sizePolicy)
        self.linearview.setObjectName("linearview")
        self.horizontalLayout.addWidget(self.linearview)
        self.tableview = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableview.sizePolicy().hasHeightForWidth())
        self.tableview.setSizePolicy(sizePolicy)
        self.tableview.setObjectName("tableview")
        self.horizontalLayout.addWidget(self.tableview)
        self.sideview = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sideview.sizePolicy().hasHeightForWidth())
        self.sideview.setSizePolicy(sizePolicy)
        self.sideview.setObjectName("sideview")
        self.horizontalLayout.addWidget(self.sideview)
        self.topview = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.topview.sizePolicy().hasHeightForWidth())
        self.topview.setSizePolicy(sizePolicy)
        self.topview.setObjectName("topview")
        self.horizontalLayout.addWidget(self.topview)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.line_5 = QtWidgets.QFrame(self.groupBox)
        self.line_5.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.horizontalLayout_2.addWidget(self.line_5)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.helpBtn = QtWidgets.QPushButton(self.groupBox)
        self.helpBtn.setObjectName("helpBtn")
        self.verticalLayout_2.addWidget(self.helpBtn)
        self.addProject = QtWidgets.QPushButton(self.groupBox)
        self.addProject.setObjectName("addProject")
        self.verticalLayout_2.addWidget(self.addProject)
        self.line_4 = QtWidgets.QFrame(self.groupBox)
        self.line_4.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.verticalLayout_2.addWidget(self.line_4)
        self.importBtn = QtWidgets.QPushButton(self.groupBox)
        self.importBtn.setObjectName("importBtn")
        self.verticalLayout_2.addWidget(self.importBtn)
        self.exportBtn = QtWidgets.QPushButton(self.groupBox)
        self.exportBtn.setObjectName("exportBtn")
        self.verticalLayout_2.addWidget(self.exportBtn)
        self.line_2 = QtWidgets.QFrame(self.groupBox)
        self.line_2.setStyleSheet("margin-top: 3;")
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout_2.addWidget(self.line_2)
        self.workLocallyCheckBox = QtWidgets.QCheckBox(self.groupBox)
        self.workLocallyCheckBox.setObjectName("workLocallyCheckBox")
        self.verticalLayout_2.addWidget(self.workLocallyCheckBox)
        self.save_ft = QtWidgets.QPushButton(self.groupBox)
        self.save_ft.setObjectName("save_ft")
        self.verticalLayout_2.addWidget(self.save_ft)
        self.fetch_ft = QtWidgets.QPushButton(self.groupBox)
        self.fetch_ft.setObjectName("fetch_ft")
        self.verticalLayout_2.addWidget(self.fetch_ft)
        self.line = QtWidgets.QFrame(self.groupBox)
        self.line.setStyleSheet("margin-top: 3;")
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout_2.addWidget(self.line)
        self.chatWindowBtn = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.chatWindowBtn.sizePolicy().hasHeightForWidth())
        self.chatWindowBtn.setSizePolicy(sizePolicy)
        self.chatWindowBtn.setObjectName("chatWindowBtn")
        self.verticalLayout_2.addWidget(self.chatWindowBtn)
        self.adminWindowBtn = QtWidgets.QPushButton(self.groupBox)
        self.adminWindowBtn.setObjectName("adminWindowBtn")
        self.verticalLayout_2.addWidget(self.adminWindowBtn)
        self.versionHistoryBtn = QtWidgets.QPushButton(self.groupBox)
        self.versionHistoryBtn.setObjectName("versionHistoryBtn")
        self.verticalLayout_2.addWidget(self.versionHistoryBtn)
        self.line_3 = QtWidgets.QFrame(self.groupBox)
        self.line_3.setStyleSheet("margin-top: 3;")
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.verticalLayout_2.addWidget(self.line_3)
        self.deleteProjectBtn = QtWidgets.QPushButton(self.groupBox)
        self.deleteProjectBtn.setAutoFillBackground(False)
        self.deleteProjectBtn.setStyleSheet("")
        self.deleteProjectBtn.setObjectName("deleteProjectBtn")
        self.verticalLayout_2.addWidget(self.deleteProjectBtn)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.gridLayout.addLayout(self.verticalLayout_3, 0, 0, 1, 1)
        self.horizontalLayout_4.addWidget(self.groupBox)
        MSSMscolabWindow.setCentralWidget(self.centralwidget)
        self.actionCloseWindow = QtWidgets.QAction(MSSMscolabWindow)
        self.actionCloseWindow.setObjectName("actionCloseWindow")
        MSSMscolabWindow.addAction(self.actionCloseWindow)

        self.retranslateUi(MSSMscolabWindow)
        self.actionCloseWindow.triggered.connect(MSSMscolabWindow.close)
        self.password.returnPressed.connect(self.loginButton.click)
        self.emailid.returnPressed.connect(self.password.setFocus)
        QtCore.QMetaObject.connectSlotsByName(MSSMscolabWindow)

    def retranslateUi(self, MSSMscolabWindow):
        _translate = QtCore.QCoreApplication.translate
        MSSMscolabWindow.setWindowTitle(_translate("MSSMscolabWindow", "Mission Support Collaboration"))
        self.label_2.setText(_translate("MSSMscolabWindow", "MSColab URL:"))
        self.toggleConnectionBtn.setToolTip(_translate("MSSMscolabWindow", "Connect to or disconnect from Mscolab server"))
        self.toggleConnectionBtn.setWhatsThis(_translate("MSSMscolabWindow", "Connect to or disconnect from Mscolab server"))
        self.toggleConnectionBtn.setText(_translate("MSSMscolabWindow", "Connect"))
        self.status.setText(_translate("MSSMscolabWindow", "Status: Disconnected"))
        self.label.setText(_translate("MSSMscolabWindow", "TextLabel"))
        self.logoutButton.setText(_translate("MSSMscolabWindow", "Logout"))
        self.deleteAccountButton.setToolTip(_translate("MSSMscolabWindow", "Delete your mscolab account"))
        self.deleteAccountButton.setText(_translate("MSSMscolabWindow", "Delete Account"))
        self.emailid.setPlaceholderText(_translate("MSSMscolabWindow", "Email ID"))
        self.password.setPlaceholderText(_translate("MSSMscolabWindow", "Password"))
        self.loginButton.setText(_translate("MSSMscolabWindow", "Login"))
        self.addUser.setToolTip(_translate("MSSMscolabWindow", "Add new user"))
        self.addUser.setText(_translate("MSSMscolabWindow", "Add User"))
        self.listProjects.setToolTip(_translate("MSSMscolabWindow", "List of mscolab projects."))
        self.linearview.setText(_translate("MSSMscolabWindow", "Linear View"))
        self.tableview.setText(_translate("MSSMscolabWindow", "Table View"))
        self.sideview.setText(_translate("MSSMscolabWindow", "Side View"))
        self.topview.setText(_translate("MSSMscolabWindow", "Top View"))
        self.helpBtn.setText(_translate("MSSMscolabWindow", "Help"))
        self.addProject.setToolTip(_translate("MSSMscolabWindow", "Add new project"))
        self.addProject.setText(_translate("MSSMscolabWindow", "Add Project"))
        self.importBtn.setToolTip(_translate("MSSMscolabWindow", "Import a FTML file to your project"))
        self.importBtn.setText(_translate("MSSMscolabWindow", "Import"))
        self.exportBtn.setToolTip(_translate("MSSMscolabWindow", "Export your project as a FTML file"))
        self.exportBtn.setText(_translate("MSSMscolabWindow", "Export"))
        self.workLocallyCheckBox.setToolTip(_translate("MSSMscolabWindow", "Work on your local file"))
        self.workLocallyCheckBox.setText(_translate("MSSMscolabWindow", "Work Locally"))
        self.save_ft.setToolTip(_translate("MSSMscolabWindow", "Save your local file changes to server"))
        self.save_ft.setText(_translate("MSSMscolabWindow", "Save To Server"))
        self.fetch_ft.setToolTip(_translate("MSSMscolabWindow", "Fetch the server data to your local file"))
        self.fetch_ft.setText(_translate("MSSMscolabWindow", "Fetch From Server"))
        self.chatWindowBtn.setToolTip(_translate("MSSMscolabWindow", "Open project chat window"))
        self.chatWindowBtn.setText(_translate("MSSMscolabWindow", "Chat"))
        self.adminWindowBtn.setToolTip(_translate("MSSMscolabWindow", "Open project admin window"))
        self.adminWindowBtn.setText(_translate("MSSMscolabWindow", "Manage Users"))
        self.versionHistoryBtn.setToolTip(_translate("MSSMscolabWindow", "Open project version history window"))
        self.versionHistoryBtn.setText(_translate("MSSMscolabWindow", "Version History"))
        self.deleteProjectBtn.setToolTip(_translate("MSSMscolabWindow", "Delete selected project"))
        self.deleteProjectBtn.setText(_translate("MSSMscolabWindow", "Delete"))
        self.actionCloseWindow.setText(_translate("MSSMscolabWindow", "CloseWindow"))
        self.actionCloseWindow.setShortcut(_translate("MSSMscolabWindow", "Ctrl+W"))