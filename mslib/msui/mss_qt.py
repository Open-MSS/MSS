# -*- coding: utf-8 -*-
"""

    mslib.msui.mss_qt
    ~~~~~~~~~~~~~~~~~

    This module switches qt4 or qt5

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import importlib
import logging
import traceback
import sys
from past.builtins import unicode
import platform

USE_PYQT5 = False
try:
    # import the Qt4Agg FigureCanvas object, that binds Figure to
    # Qt4Agg backend. It also inherits from QWidget
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

    # import the NavigationToolbar Qt4Agg widget
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

    from PyQt4 import QtGui, QtCore, QtTest
    QtWidgets = QtGui  # Follow the PyQt5 style and access objects from the modules of PyQt5
    from PyQt4.QtCore import QString  # import QString as this does not exist in PyQt5

    QtTest.QTest.qWaitForWindowExposed = QtTest.QTest.qWaitForWindowShown

    def value(self):
        """
        Backport of needed stuff from PyQt5 value function
        """
        if self.typeName() in ["float", "double"]:
            result, ok = self.toDouble()
            if not ok:
                raise RuntimeError("Problem in converting: {}".format(self))
            return result
        if self.typeName() in ["int"]:
            result, ok = self.toInt()
            if not ok:
                raise RuntimeError("Problem in converting: {}".format(self))
            return result
        if self.typeName() in ["QString"]:
            return self.toString()
        raise RuntimeError("Unsupported type in conversion: {}".format(self.typeName()))

    QtCore.QVariant.value = value

    _qt_ui_prefix = "mslib.msui.qt4."

except ImportError:
    logging.warning("Did not find PyQt4. Switching to PyQt5.")
    # import the Qt5Agg FigureCanvas object, that binds Figure to
    # Qt5Agg backend. It also inherits from QWidget
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

    # import the NavigationToolbar Qt5Agg widget
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

    from PyQt5 import QtGui, QtCore, QtWidgets, QtTest
    QString = str  # QString is not exposed anymore but is used transparently by PyQt5

    _qt_ui_prefix = "mslib.msui.qt5."

    USE_PYQT5 = True


def variant_to_string(variant):
    if isinstance(variant, QtCore.QVariant):
        return unicode(variant.value())
    return unicode(variant)


def variant_to_float(variant, locale=QtCore.QLocale()):
    if isinstance(variant, QtCore.QVariant):
        value = variant.value()
    else:
        value = variant

    if isinstance(value, (int, float)):
        return value
    try:
        float_value, ok = locale.toDouble(value)
        if not ok:
            raise ValueError
    except TypeError:  # neither float nor string, try Python conversion
        logging.error("Unexpected type in float conversion: %s=%s",
                      type(value), value)
        float_value = float(value)
    return float_value


# Import all Dialogues from the proper module directory.
for mod in [
        "ui_about_dialog",
        "ui_hexagon_dockwidget",
        "ui_kmloverlay_dockwidget",
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


# PyQt5 silently aborts on a Python Exception and PyQt4 does not inform GUI users
def excepthook(type_, value, traceback_):
    """
    This dumps the error to console, logging (i.e. logfile), and tries to open a MessageBox for GUI users.
    """
    import mslib
    import mslib.utils
    tb = "".join(traceback.format_exception(type_, value, traceback_))
    traceback.print_exception(type_, value, traceback_)
    logging.critical(u"MSS Version: %s", mslib.__version__)
    logging.critical(u"Python Version: %s", sys.version)
    logging.critical(u"Platform: %s (%s)", platform.platform(), platform.architecture())
    logging.critical(u"Fatal error: %s", tb)

    if type_ is mslib.utils.FatalUserError:
        QtWidgets.QMessageBox.critical(
            None, u"fatal error",
            u"Fatal user error in MSS {} on {}\n"
            u"Python {}\n"
            u"\n"
            u"{}".format(mslib.__version__, platform.platform(), sys.version, value))
    else:
        QtWidgets.QMessageBox.critical(
            None, u"fatal error",
            u"Fatal error in MSS {} on {}\n"
            u"Python {}\n"
            u"\n"
            u"Please report bugs in MSS to https://bitbucket.org/wxmetvis/mss\n"
            u"\n"
            u"Information about the fatal error:\n"
            u"\n"
            u"{}".format(mslib.__version__, platform.platform(), sys.version, tb))
    QtCore.qFatal('')


sys.excepthook = excepthook
