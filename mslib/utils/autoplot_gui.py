import sys
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QListWidgetItem, QVBoxLayout, QPushButton, QLabel
from mslib.msui.qt5.mssautoplot_gui import Ui_Form


class Layers(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Layers Window')
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel('Select Layers Under development', self)
        layout.addWidget(self.label)

        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        self.setLayout(layout)


class Upload(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cpath = None
        self.view = None
        self.itime = None
        self.vtime = None
        self.intv = None
        self.num_interpolation_points = None
        self.num_labels = None
        self.stime = None
        self.etime = None
        self.sections = None
        self.level = None
        self.resolution = None
        self.ftrack = {}
        self.operations = {}
        self.url = []

        # cpath
        self.pushButton.clicked.connect(self.open_file_dialog)
        # all QcomboBox
        self.comboBox.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox))
        self.comboBox_2.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox_2))
        self.comboBox_3.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox_3))
        self.comboBox_4.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox_4))
        self.comboBox_5.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox_5))
        self.comboBox_6.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox_6))
        self.comboBox_9.currentIndexChanged.connect(lambda: self.combo_box_input(self.comboBox_9))
        # all spinBox
        self.spinBox.valueChanged.connect(lambda value: self.on_spin_box_value_changed(value, self.spinBox))
        self.spinBox_2.valueChanged.connect(lambda value: self.on_spin_box_value_changed(value, self.spinBox_2))
        self.spinBox_3.valueChanged.connect(lambda value: self.on_spin_box_value_changed(value, self.spinBox_3))
        self.spinBox_4.valueChanged.connect(lambda value: self.on_spin_box_value_changed(value, self.spinBox_4))
        # all pushButton
        self.pushButton_9.clicked.connect(self.add_ftrack)
        self.pushButton_8.clicked.connect(self.remove_ftrack)
        self.pushButton_11.clicked.connect(self.add_operation)
        self.pushButton_10.clicked.connect(self.remove_operation)
        self.pushButton_5.clicked.connect(self.add_url)
        self.pushButton_6.clicked.connect(self.remove_url)
        self.pushButton_4.clicked.connect(self.layers_window)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select .json Config File", "", "JSON Files (*.json)", options=options)
        if file_name:
            self.cpath = file_name

    def combo_box_input(self, combo):
        combo_box_name = combo.objectName()
        if combo_box_name == "comboBox":
            self.view = self.comboBox.currentText()
        elif combo_box_name == "comboBox_2":
            self.view = self.comboBox_2.currentText()
        elif combo_box_name == "comboBox_3":
            self.view = self.comboBox_3.currentText()
        elif combo_box_name == "comboBox_4":
            self.view = self.comboBox_4.currentText()
        elif combo_box_name == "comboBox_5":
            self.itime = self.comboBox_5.currentText()
        elif combo_box_name == "comboBox_6":
            self.vtime = self.comboBox_6.currentText()
        elif combo_box_name == "comboBox_9":
            self.intv = self.comboBox_9.currentText()

    def on_spin_box_value_changed(self, value, spin_name):
        spin_box_name = spin_name.objectName()
        if spin_box_name == "spinBox":
            self.num_interpolation_points = value
        elif spin_box_name == "spinBox_2":
            self.num_labels = value
        elif spin_box_name == "spinBox_3":
            self.stime = value
        elif spin_box_name == "spinBox_4":
            self.etime = value

    def add_ftrack(self):
        text = self.lineEdit_2.text()
        if text:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Select .ftml flights File", "", "ftml Files (*.ftml)", options=options)
            path = file_name
            if path:
                self.ftrack[text] = path
                item = QListWidgetItem(text)
                self.listWidget_2.addItem(item)
            self.lineEdit_2.clear()

    def remove_ftrack(self):
        selected = self.listWidget_2.selectedItems()
        if selected:
            for i in selected:
                del self.ftrack[i.text()]
                self.listWidget_2.takeItem(self.listWidget_2.row(i))

    def add_operation(self):
        text = self.lineEdit_4.text()
        if text:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Select Operations File", "", "JSON Files (*.json)", options=options)
            path = file_name
            if path:
                self.operations[text] = path
                item = QListWidgetItem(text)
                self.listWidget_3.addItem(item)
            self.lineEdit_4.clear()

    def remove_operation(self):
        selected = self.listWidget_3.selectedItems()
        if selected:
            for i in selected:
                del self.operations[i.text()]
                self.listWidget_3.takeItem(self.listWidget_3.row(i))

    def add_url(self):
        text = self.lineEdit.text()
        if text:
            item = QListWidgetItem(text)
            self.listWidget.addItem(item)
            self.lineEdit.clear()
            self.url.append(text)

    def remove_url(self):
        selected = self.listWidget.selectedItems()
        if selected:
            for i in selected:
                self.url.remove(i.text())
                self.listWidget.takeItem(self.listWidget.row(i))

    def layers_window(self):
        self.layerobj = Layers()
        self.layerobj.show()


def main():
    app = QApplication(sys.argv)
    window = Upload()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
