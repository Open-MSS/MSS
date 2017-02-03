"""
AUTHORS:
========

* Joern Ungermann (ju)

"""

import importlib
import traceback
import sys

USE_PYQT5 = False
try:
    # import the Qt4Agg FigureCanvas object, that binds Figure to
    # Qt4Agg backend. It also inherits from QWidget
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

    # import the NavigationToolbar Qt4Agg widget
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

    from PyQt4 import QtGui, QtCore
    QtWidgets = QtGui  # Follow the PyQt5 style and access objects from the modules of PyQt5
    from PyQt4.QtCore import QString  # import QString as this does not exist in PyQt5

    _qt_ui_prefix = "mslib.msui.qt4."

except ImportError:
    # import the Qt5Agg FigureCanvas object, that binds Figure to
    # Qt5Agg backend. It also inherits from QWidget
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

    # import the NavigationToolbar Qt5Agg widget
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.QtCore import QVariant, Qt, QModelIndex, QAbstractTableModel
    from PyQt5.QtWidgets import QItemDelegate, QComboBox, QDialog, QWidget, QMainWindow, QLabel, QListWidgetItem, \
        QApplication, QAction, QFileDialog, QMessageBox, QProgressDialog, QVBoxLayout

    QString = unicode  # QString is not exposed anymore but is used transparently by PyQt5

    _qt_ui_prefix = "mslib.msui.qt5."

    USE_PYQT5 = True

# Import all Dialogues from the proper module directory.
for mod in [
        "ui_about_dialog",
        "ui_hexagon_dockwidget",
        "ui_imageloop_load_dialog",
        "ui_imageloop_widget",
        "ui_kmloverlay_dockwidget",
        "ui_loopwindow",
        "ui_mainwindow",
        "ui_performance_settings",
        "ui_remotesensing_dockwidget",
        "ui_satellite_dockwidget",
        "ui_sideview_options",
        "ui_sideview_window",
        "ui_tableview_window",
        "ui_timeseriesview_window",
        "ui_topview_mapappearance",
        "ui_topview_window",
        "ui_trajectories_window",
        "ui_wms_capabilities",
        "ui_wms_dockwidget",
        "ui_wms_password_dialog"]:
    globals()[mod] = importlib.import_module(_qt_ui_prefix + mod)


# Add some functions that are used.
# TODO Can probably be tidied up in a neater fashion by rewriting the using code.
if USE_PYQT5:
    def _fromUtf8(s):
        return s

    _translate = QtCore.QCoreApplication.translate

    # PyQt5 silently aborts on a Python Exception
    def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')
    sys.excepthook = excepthook

else:
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
