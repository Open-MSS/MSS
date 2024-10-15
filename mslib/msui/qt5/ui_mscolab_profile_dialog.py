# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_profile_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ProfileWindow(object):
    def setupUi(self, ProfileWindow):
        ProfileWindow.setObjectName("ProfileWindow")
        ProfileWindow.resize(387, 149)
        self.gridLayout = QtWidgets.QGridLayout(ProfileWindow)
        self.gridLayout.setObjectName("gridLayout")
        self.infoGl = QtWidgets.QGridLayout()
        self.infoGl.setObjectName("infoGl")
        self.emailLabel_2 = QtWidgets.QLabel(ProfileWindow)
        self.emailLabel_2.setText("")
        self.emailLabel_2.setObjectName("emailLabel_2")
        self.infoGl.addWidget(self.emailLabel_2, 1, 2, 1, 1)
        self.label = QtWidgets.QLabel(ProfileWindow)
        self.label.setObjectName("label")
        self.infoGl.addWidget(self.label, 0, 1, 1, 1, QtCore.Qt.AlignLeft)
        self.emailLabel = QtWidgets.QLabel(ProfileWindow)
        self.emailLabel.setObjectName("emailLabel")
        self.infoGl.addWidget(self.emailLabel, 1, 0, 1, 1)
        self.usernameLabel = QtWidgets.QLabel(ProfileWindow)
        self.usernameLabel.setObjectName("usernameLabel")
        self.infoGl.addWidget(self.usernameLabel, 0, 0, 1, 1)
        self.usernameLabel_2 = QtWidgets.QLabel(ProfileWindow)
        self.usernameLabel_2.setText("")
        self.usernameLabel_2.setObjectName("usernameLabel_2")
        self.infoGl.addWidget(self.usernameLabel_2, 0, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(ProfileWindow)
        self.label_3.setObjectName("label_3")
        self.infoGl.addWidget(self.label_3, 2, 1, 1, 1)
        self.mscolabURLLabel_2 = QtWidgets.QLabel(ProfileWindow)
        self.mscolabURLLabel_2.setText("")
        self.mscolabURLLabel_2.setObjectName("mscolabURLLabel_2")
        self.infoGl.addWidget(self.mscolabURLLabel_2, 2, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(ProfileWindow)
        self.label_2.setObjectName("label_2")
        self.infoGl.addWidget(self.label_2, 1, 1, 1, 1, QtCore.Qt.AlignLeft)
        self.mscolabURLLabel = QtWidgets.QLabel(ProfileWindow)
        self.mscolabURLLabel.setObjectName("mscolabURLLabel")
        self.infoGl.addWidget(self.mscolabURLLabel, 2, 0, 1, 1)
        self.gridLayout.addLayout(self.infoGl, 0, 0, 1, 2)
        self.gravatarVl = QtWidgets.QVBoxLayout()
        self.gravatarVl.setObjectName("gravatarVl")
        self.gravatarLabel = QtWidgets.QLabel(ProfileWindow)
        self.gravatarLabel.setText("")
        self.gravatarLabel.setPixmap(QtGui.QPixmap(":/gravatars/default-gravatars/default.png"))
        self.gravatarLabel.setScaledContents(True)
        self.gravatarLabel.setObjectName("gravatarLabel")
        self.gravatarVl.addWidget(self.gravatarLabel, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.gridLayout.addLayout(self.gravatarVl, 0, 2, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.deleteAccountBtn = QtWidgets.QPushButton(ProfileWindow)
        self.deleteAccountBtn.setIconSize(QtCore.QSize(40, 20))
        self.deleteAccountBtn.setAutoDefault(False)
        self.deleteAccountBtn.setObjectName("deleteAccountBtn")
        self.horizontalLayout.addWidget(self.deleteAccountBtn)
        self.uploadImageBtn = QtWidgets.QPushButton(ProfileWindow)
        self.uploadImageBtn.setObjectName("uploadImageBtn")
        self.horizontalLayout.addWidget(self.uploadImageBtn)
        self.buttonBox = QtWidgets.QDialogButtonBox(ProfileWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setMouseTracking(False)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignHCenter)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 3)

        self.retranslateUi(ProfileWindow)
        QtCore.QMetaObject.connectSlotsByName(ProfileWindow)

    def retranslateUi(self, ProfileWindow):
        _translate = QtCore.QCoreApplication.translate
        ProfileWindow.setWindowTitle(_translate("ProfileWindow", "MSColab Profile"))
        self.label.setText(_translate("ProfileWindow", ":"))
        self.emailLabel.setText(_translate("ProfileWindow", "Email"))
        self.usernameLabel.setText(_translate("ProfileWindow", "Name"))
        self.label_3.setText(_translate("ProfileWindow", ":"))
        self.label_2.setText(_translate("ProfileWindow", ":"))
        self.mscolabURLLabel.setText(_translate("ProfileWindow", "Mscolab"))
        self.deleteAccountBtn.setText(_translate("ProfileWindow", "Delete Account"))
        self.uploadImageBtn.setText(_translate("ProfileWindow", "Change Avatar"))


from . import resources_rc
