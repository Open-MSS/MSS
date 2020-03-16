import mock
import pyperclip
import os
import sys
from mslib.msui.mss_qt import QtWidgets, QtTest
from mslib.msui import editor


HOME = os.path.expanduser("~/")

class TEST_MSS_ED(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = editor.MainWindow()
        self.window.show
        self.window.path = HOME+"/test_data/testFile.json"
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_file_open(self):
        QtWidgets.QApplication.processEvents()
        self.window.file_open()
        self.window.file_open.path = HOME+"/test_data/testFile.json"
        QtWidgets.QApplication.processEvents()
        assert self.window.file_open.text == "This is for Test."

    @mock.patch("mslib.msui.editor.MainWindow.self.editor")
    def test_file_select(self, mockeditor):
        QtWidgets.QApplication.processEvents()
        self.window.editor.selectAll
        self.mockeditor.copy
        text = pyperclip.paste()
        QtWidgets.QApplication.processEvents()
        assert text == "This is for Test."

    @mock.patch("mslib.msui.editor.MainWindow.self.editor")
    def test_file_copy(self, mockeditor):
        QtWidgets.QApplication.processEvents()
        self.mockeditor.selectAll
        self.window.editor.copy
        text = pyperclip.paste()
        QtWidgets.QApplication.processEvents()
        assert text == "This is for Test."

    @mock.patch("mslib.msui.editor.MainWindow.self.editor")
    def test_file_cut(self, mockeditor):
        QtWidgets.QApplication.processEvents()
        self.mockeditor.selectAll
        self.window.editor.copy
        text = pyperclip.paste()
        QtWidgets.QApplication.processEvents()
        assert text == "This is for Test."

    @mock.patch("mslib.msui.editor.MainWindow")
    def test_file_paste(self, mockwindow):
        QtWidgets.QApplication.processEvents()
        self.window.editor.paste
        mockwindow.file_save(self)
        mockwindow.editor.selectAll
        mockwindow.editor.copy
        text = pyperclip.paste()
        QtWidgets.QApplication.processEvents()
        assert text == "This is for Test."

    @mock.patch("mslib.msui.editor.MainWindow")
    def test_file_save(self, mockwindow):
        QtWidgets.QApplication.processEvents()
        mockwindow.editor.cut
        self.MainWindow.file_save()
        mockwindow.editor.copy
        text = pyperclip.paste()
        mockwindow.editor.paste
        self.MainWindow.file_save()
        QtWidgets.QApplication.processEvents()
        assert text == ""
