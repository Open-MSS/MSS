import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from mslib.utils import mssautoplot as autoplot
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from mslib.utils.config import config_loader, read_config_file
from mslib.msui import constants
from owslib.wms import WebMapService
from datetime import datetime


class Ui_mssautoplot(object):
	def setupUi(self, mssautoplot):
		mssautoplot.setObjectName("mssautoplot")
		mssautoplot.resize(523, 552)
		self.centralwidget = QtWidgets.QWidget(mssautoplot)
		self.centralwidget.setObjectName("centralwidget")
		self.View = QtWidgets.QLabel(self.centralwidget)
		self.View.setGeometry(QtCore.QRect(40, 30, 67, 17))
		self.View.setObjectName("View")
		self.top_view = QtWidgets.QRadioButton(self.centralwidget)
		self.top_view.setGeometry(QtCore.QRect(40, 60, 112, 23))
		self.top_view.setObjectName("top_view")
		self.side_view = QtWidgets.QRadioButton(self.centralwidget)
		self.side_view.setGeometry(QtCore.QRect(140, 60, 112, 23))
		self.side_view.setObjectName("side_view")
		self.conf_path = QtWidgets.QLabel(self.centralwidget)
		self.conf_path.setGeometry(QtCore.QRect(40, 110, 81, 17))
		self.conf_path.setObjectName("conf_path")
		self.conf_path.hide()
		
		self.config_edit = QtWidgets.QLineEdit(self.centralwidget)
		self.config_edit.setGeometry(QtCore.QRect(40, 130, 151, 25))
		self.config_edit.setObjectName("config_edit")
		self.config_edit.hide()

		self.file = QtWidgets.QLabel(self.centralwidget)
		self.file.setGeometry(QtCore.QRect(40, 180, 67, 17))
		self.file.setObjectName("file")
		self.file.hide()

		self.flight = QtWidgets.QLabel(self.centralwidget)
		self.flight.setGeometry(QtCore.QRect(290, 110, 81, 16))
		self.flight.setObjectName("flight")
		self.flight.hide()

		self.server = QtWidgets.QLabel(self.centralwidget)
		self.server.setGeometry(QtCore.QRect(40, 250, 91, 17))
		self.server.setObjectName("server")
		self.server.hide()

		self.init_time = QtWidgets.QLabel(self.centralwidget)
		self.init_time.setGeometry(QtCore.QRect(40, 400, 67, 17))
		self.init_time.setObjectName("init_time")
		self.init_time.hide()

		self.section = QtWidgets.QLabel(self.centralwidget)
		self.section.setGeometry(QtCore.QRect(290, 180, 91, 17))
		self.section.setObjectName("section")
		self.section.hide()

		self.vsec = QtWidgets.QLabel(self.centralwidget)
		self.vsec.setGeometry(QtCore.QRect(290, 250, 67, 17))
		self.vsec.setObjectName("vsec")
		self.vsec.hide()

		self.level = QtWidgets.QLabel(self.centralwidget)
		self.level.setGeometry(QtCore.QRect(290, 250, 67, 17))
		self.level.setObjectName("level") 
		self.level.hide()

		self.valid_time = QtWidgets.QLabel(self.centralwidget)
		self.valid_time.setGeometry(QtCore.QRect(290, 400, 67, 17))
		self.valid_time.setObjectName("valid_time")
		self.valid_time.hide()

		self.section_dropdown = QtWidgets.QComboBox(self.centralwidget)
		self.section_dropdown.setGeometry(QtCore.QRect(290, 200, 201, 25))
		self.section_dropdown.setObjectName("section_dropdown")
		path = constants.MSS_AUTOPLOT
		read_config_file(path)
		self.config = config_loader()
		print(self.config["predefined_map_sections"].keys())
		for item in self.config["predefined_map_sections"].keys():
			self.section_dropdown.addItem(item)
		self.section_dropdown.hide()

		self.level_edit = QtWidgets.QLineEdit(self.centralwidget)
		self.level_edit.setGeometry(QtCore.QRect(290, 270, 201, 25))
		self.level_edit.setObjectName("level_edit")
		self.level_edit.hide()
		self.style_edit = QtWidgets.QLineEdit(self.centralwidget)
		self.style_edit.setGeometry(QtCore.QRect(290, 340, 201, 25))
		self.style_edit.setObjectName("style_edit")
		self.style_edit.hide()


		self.vsec_drop_down = QtWidgets.QComboBox(self.centralwidget)
		self.vsec_drop_down.setGeometry(QtCore.QRect(290, 270, 201, 25))
		self.vsec_drop_down.setObjectName("vsec_drop_down")
		self.vsec_drop_down.hide()

		self.init_time_edit = QtWidgets.QDateTimeEdit(self.centralwidget)
		self.init_time_edit.setGeometry(QtCore.QRect(40, 420, 201, 26))
		self.init_time_edit.setObjectName("init_time_edit")
		self.init_time_edit.hide()

		self.valid_time_edit = QtWidgets.QDateTimeEdit(self.centralwidget)
		self.valid_time_edit.setGeometry(QtCore.QRect(290, 420, 201, 26))
		self.valid_time_edit.setObjectName("valid_time_edit")
		self.valid_time_edit.hide()

		self.retrieve = QtWidgets.QPushButton(self.centralwidget)
		self.retrieve.setGeometry(QtCore.QRect(400, 470, 89, 31))
		font = QtGui.QFont()
		font.setPointSize(10)
		font.setBold(True)
		font.setWeight(75)
		self.retrieve.setFont(font)
		self.retrieve.setObjectName("retrieve")

		self.cpath_browse = QtWidgets.QPushButton(self.centralwidget)
		self.cpath_browse.setGeometry(QtCore.QRect(190, 130, 51, 25))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.cpath_browse.setFont(font)
		self.cpath_browse.setObjectName("cpath_browse")
		self.cpath_browse.hide()

		self.file_edit = QtWidgets.QLineEdit(self.centralwidget)
		self.file_edit.setGeometry(QtCore.QRect(40, 200, 151, 25))
		self.file_edit.setObjectName("file_edit")
		self.file_edit.hide()

		self.file_browser = QtWidgets.QPushButton(self.centralwidget)
		self.file_browser.setGeometry(QtCore.QRect(190, 200, 51, 25))
		font = QtGui.QFont() 
		font.setPointSize(10)
		self.file_browser.setFont(font)
		self.file_browser.setObjectName("file_browser")
		self.file_browser.hide()

		self.server_edit = QtWidgets.QLineEdit(self.centralwidget)
		self.server_edit.setGeometry(QtCore.QRect(40, 270, 201, 25))
		self.server_edit.setObjectName("server_edit")
		self.server_edit.hide()

		self.flight_edit = QtWidgets.QLineEdit(self.centralwidget)
		self.flight_edit.setGeometry(QtCore.QRect(290, 130, 201, 25))
		self.flight_edit.setObjectName("flight_edit")
		self.flight_edit.hide()

		self.layer = QtWidgets.QLabel(self.centralwidget)
		self.layer.setGeometry(QtCore.QRect(40, 320, 67, 17))
		self.layer.setObjectName("layer")
		self.layer.hide()

		self.style = QtWidgets.QLabel(self.centralwidget)
		self.style.setGeometry(QtCore.QRect(290, 320, 67, 17))
		self.style.setObjectName("style")
		self.style.hide()

		self.layer_dropdown = QtWidgets.QComboBox(self.centralwidget)
		self.layer_dropdown.setGeometry(QtCore.QRect(40, 340, 201, 25))
		self.layer_dropdown.setObjectName("layer_dropdown")
		self.layer_dropdown.hide()

		self.search = QtWidgets.QPushButton(self.centralwidget)
		self.search.setGeometry(QtCore.QRect(190, 270, 51, 25))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.search.setFont(font)
		self.search.setObjectName("search")
		self.search.hide()


		mssautoplot.setCentralWidget(self.centralwidget)
		self.menubar = QtWidgets.QMenuBar(mssautoplot)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 523, 22))
		self.menubar.setObjectName("menubar")
		mssautoplot.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(mssautoplot)
		self.statusbar.setObjectName("statusbar")
		mssautoplot.setStatusBar(self.statusbar)

		self.retranslateUi(mssautoplot)
		QtCore.QMetaObject.connectSlotsByName(mssautoplot)

		self.cpath_browse.clicked.connect(self.configFileBrowser)
		self.search.clicked.connect(self.layerList)
		self.retrieve.clicked.connect(self.retrieveImage)
		self.file_browser.clicked.connect(self.fileBrowser)
		self.side_view.toggled.connect(self.passToggledside)
		self.top_view.toggled.connect(self.passToggledtop)
		
	def retrieveImage(self):
		flight_name = str(self.flight_edit.text())
		server_url = str(self.server_edit.text())
		layer = str(self.layer_dropdown.currentText())
		section = str(self.section_dropdown.currentText())
		level = str(self.level_edit.text())
		style = str(self.style_edit.text())
		init = self.init_time_edit.dateTime()
		valid = self.valid_time_edit.dateTime()
		initpy = init.toPyDateTime()
		validpy = valid.toPyDateTime()
		inittime = datetime.strftime(initpy, '%Y-%m-%dT%H:%M:%SZ')
		validtime = datetime.strftime(validpy, '%Y-%m-%dT%H:%M:%SZ')
		if self.view == "top":
			top_view = autoplot.TopViewPlotting(self.config_path)
			sec = "automated_plotting_hsecs"
			top_view.draw(flight_name, section, "", self.filename, inittime,
                              validtime, server_url, layer, style, level, no_of_plots=1)
		else:
			side_view = autoplot.SideViewPlotting(self.config_path)
			sec = "automated_plotting_vsecs"


	def layerList(self):
		server_url = self.server_edit.text()
		print(server_url)
		wms = WebMapService(str(server_url))
		layers = list(wms.contents)
		print(layers)
		self.layer_dropdown.addItems(layers)

	def configFileBrowser(self):
		ex = Appl()
		print(ex.file)
		self.config_edit.setText(ex.file)
		self.config_path = ex.path

	def fileBrowser(self):
		ex = FileBrowserDialog()
		print(ex.file)
		self.file_edit.setText(ex.file)
		self.filename = ex.file

	def passToggledtop(self):
		if not self.side_view.isChecked():
			self.view = "top"
			self.conf_path.show()
			self.config_edit.show()
			self.file.show()
			self.flight.show()
			self.server.show()
			self.init_time.show()
			self.section.show()
			self.vsec.hide()
			self.vsec_drop_down.hide()
			self.level.show()
			self.valid_time.show()
			self.section_dropdown.show()
			self.init_time_edit.show()
			self.valid_time_edit.show()
			self.cpath_browse.show()
			self.file_edit.show()
			self.file_browser.show()
			self.server_edit.show()
			self.flight_edit.show()
			self.layer.show()
			self.style.show()
			self.layer_dropdown.show()
			self.search.show()
			self.style_edit.show()
			self.level_edit.show()
	
	def passToggledside(self):
		if not self.top_view.isChecked():
			self.view = "side"
			self.conf_path.show()
			self.config_edit.show()
			self.file.show()
			self.flight.show()
			self.server.show()
			self.init_time.show()
			self.section.show()
			self.level.hide()
			self.vsec.show()
			self.valid_time.show()
			self.section_dropdown.show()
			self.vsec_drop_down.show()
			self.init_time_edit.show()
			self.valid_time_edit.show()
			self.cpath_browse.show()
			self.file_edit.show()
			self.file_browser.show()
			self.server_edit.show()
			self.flight_edit.show()
			self.layer.show()
			self.style.show()
			self.layer_dropdown.show()
			self.search.show()
			self.style_edit.show()
			self.level_edit.show()
			

	def retranslateUi(self, mssautoplot):
		_translate = QtCore.QCoreApplication.translate
		mssautoplot.setWindowTitle(_translate("mssautoplot", "MainWindow"))
		self.View.setText(_translate("mssautoplot", "View"))
		self.top_view.setText(_translate("mssautoplot", "Top view"))
		self.side_view.setText(_translate("mssautoplot", "Side view"))
		self.conf_path.setText(_translate("mssautoplot", "Config Path"))
		self.file.setText(_translate("mssautoplot", "Filename"))
		self.flight.setText(_translate("mssautoplot", "Flight name"))
		self.server.setText(_translate("mssautoplot", "Server URL"))
		self.init_time.setText(_translate("mssautoplot", "Init time"))
		self.section.setText(_translate("mssautoplot", "Map-section"))
		self.level.setText(_translate("mssautoplot", "Level"))
		self.vsec.setText(_translate("mssautoplot", "Vsec"))
		self.valid_time.setText(_translate("mssautoplot", "Valid time"))
		self.retrieve.setText(_translate("mssautoplot", "Retrieve"))
		self.cpath_browse.setText(_translate("mssautoplot", "Browse"))
		self.file_browser.setText(_translate("mssautoplot", "Browse"))
		self.layer.setText(_translate("mssautoplot", "Layer"))
		self.style.setText(_translate("mssautoplot", "Style"))
		self.search.setText(_translate("mssautoplot", "Go"))
		

class FileBrowserDialog(QWidget):
	def __init__(self):
		super().__init__()
		self.title = 'mssautoplot- MSS'
		self.left = 10
		self.top = 10
		self.width = 640
		self.height = 480
		self.initUI()
    
	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		
		self.openFileNameDialog()       
		self.show()
	
	def openFileNameDialog(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		self.path, _ = QFileDialog.getOpenFileName(self,"mssautoplot- File browser", "","All Files (*);;Python Files (*.py)", options=options)
		if self.path:
		    print(self.path)

		self.dir_path = os.path.split(self.path)[0]
		print(self.dir_path)
		self.file = os.path.split(self.path)[1]
		print(self.file)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mssautoplot = QtWidgets.QMainWindow()
    ui = Ui_mssautoplot()
    ui.setupUi(mssautoplot)
    mssautoplot.show()
    sys.exit(app.exec_())

