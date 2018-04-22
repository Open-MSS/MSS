# -*- coding: utf-8 -*-
"""

    mslib.msui.timeseriesview
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Window for the display of trajectory time series.


    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

from mslib.msui.mss_qt import QtGui  # Qt bindings

from mslib.msui.mss_qt import ui_timeseriesview_window as ui
from mslib.msui.viewwindows import MSSMplViewWindow
from mslib.msui.icons import icons


class MSSTimeSeriesViewWindow(MSSMplViewWindow, ui.Ui_TimeSeriesViewWindow):
    """PyQt window implementing a time series view.
    """
    name = "Time Series View"

    def __init__(self, parent=None):
        """Set up user interface, connect signal/slots.
        """
        super(MSSTimeSeriesViewWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))

    def setIdentifier(self, identifier):
        super(MSSTimeSeriesViewWindow, self).setIdentifier(identifier)
        self.mpl.canvas.setIdentifier(identifier)
