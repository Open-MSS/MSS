# -*- coding: utf-8 -*-
"""

    mslib.msui.linearview
    ~~~~~~~~~~~~~~~~~~~

    Linear view module of the msui

    This file is part of mss.

    :copyright: Copyright 2021 May Baer
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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

from mslib.utils import config_loader, save_settings_qsettings, load_settings_qsettings
from PyQt5 import QtGui, QtWidgets
from mslib.msui.mss_qt import ui_linearview_window as ui
from mslib.msui.mss_qt import ui_linearview_options as ui_opt
from mslib.msui.viewwindows import MSSMplViewWindow
from mslib.msui import wms_control as wms
from mslib.msui.icons import icons

# Dock window indices.
WMS = 0


class MSS_LV_Options_Dialog(QtWidgets.QDialog, ui_opt.Ui_LinearViewOptionsDialog):
    """
    Dialog class to specify Linear View Options.
    """

    def __init__(self, parent=None, settings_dict=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        settings_dict -- dictionary containing sideview options.
        """
        super(MSS_LV_Options_Dialog, self).__init__(parent)
        self.setupUi(self)

        default_settings_dict = {
            "plot_title_size": "default",
            "axes_label_size": "default"
        }

        if settings_dict is not None:
            default_settings_dict.update(settings_dict)
        settings_dict = default_settings_dict

        for i in range(self.lv_cbtitlesize.count()):
            if self.lv_cbtitlesize.itemText(i) == settings_dict["plot_title_size"]:
                self.lv_cbtitlesize.setCurrentIndex(i)

        for i in range(self.lv_cbaxessize.count()):
            if self.lv_cbaxessize.itemText(i) == settings_dict["axes_label_size"]:
                self.lv_cbaxessize.setCurrentIndex(i)

    def get_settings(self):
        """
        Returns the specified settings from the GUI elements.
        """
        settings_dict = {
            "plot_title_size": self.lv_cbtitlesize.currentText(),
            "axes_label_size": self.lv_cbaxessize.currentText()
        }

        return settings_dict


class MSSLinearViewWindow(MSSMplViewWindow, ui.Ui_LinearWindow):
    """
    PyQt window implementing a matplotlib canvas as linear flight track view.
    """
    name = "Linear View"

    def __init__(self, parent=None, model=None, _id=None):
        """
        Set up user interface, connect signal/slots.
        """
        super(MSSLinearViewWindow, self).__init__(parent, model, _id)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))

        # Dock windows [WMS]:
        self.cbTools.clear()
        self.cbTools.addItems(["(select to open control)", "Linear Section WMS"])
        self.docks = [None]

        self.setFlightTrackModel(model)

        self.settings_tag = "linearview"
        self.load_settings()

        # Connect slots and signals.
        # ==========================

        # Tool opener.
        self.cbTools.currentIndexChanged.connect(self.openTool)
        self.lvoptionbtn.clicked.connect(self.set_options)

        self.openTool(WMS + 1)

    def __del__(self):
        del self.mpl.canvas.waypoints_interactor

    def update_predefined_maps(self, extra):
        pass

    def openTool(self, index):
        """
        Slot that handles requests to open tool windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == WMS:
                # Open a WMS control widget.
                title = "Web Service Plot Control"
                widget = wms.LSecWMSControlWidget(
                    default_WMS=config_loader(dataset="default_LSEC_WMS"),
                    waypoints_model=self.waypoints_model,
                    view=self.mpl.canvas,
                    wms_cache=config_loader(dataset="wms_cache"))
                self.mpl.canvas.waypoints_interactor.signal_get_lsec.connect(widget.call_get_lsec)
            else:
                raise IndexError("invalid control index")
            # Create the actual dock widget containing <widget>.
            self.createDockWidget(index, title, widget)

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the view displays.
        """
        super(MSSLinearViewWindow, self).setFlightTrackModel(model)
        if self.docks[WMS] is not None:
            self.docks[WMS].widget().setFlightTrackModel(model)

    def set_options(self):
        settings = self.getView().get_settings()
        dlg = MSS_LV_Options_Dialog(parent=self, settings_dict=settings)
        dlg.setModal(True)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.get_settings()
            self.getView().set_settings(settings)
            self.save_settings()
        dlg.destroy()

    def save_settings(self):
        """
        Save the current settings of plot options to the file self.settingsfile.
        """
        settings = self.getView().get_settings()
        save_settings_qsettings(self.settings_tag, settings)

    def load_settings(self):
        """
        Load settings from the file self.settingsfile.
        """
        settings = load_settings_qsettings(self.settings_tag)
        self.getView().set_settings(settings)
