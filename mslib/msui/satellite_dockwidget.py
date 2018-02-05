# -*- coding: utf-8 -*-
"""

    mslib.msui.satellite_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control to load satellite track predictions into the top view.

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

from builtins import str

import logging
import os
from datetime import datetime, timedelta
import numpy as np

from mslib.msui.mss_qt import QtWidgets
from mslib.msui.mss_qt import ui_satellite_dockwidget as ui
from mslib.utils import save_settings_pickle, load_settings_pickle
from fs import open_fs
from fslib.fs_filepicker import getOpenFileName


def read_nasa_satellite_prediction(fname):
    """Read a text file as downloaded from the NASA satellite prediction tool.

    This method reads satellite overpass predictions in ASCII format as
    downloaded from http://www-air.larc.nasa.gov/tools/predict.htm.

    Returns a list of dictionaries with keys
      -- utc: Nx1 array with utc times as datetime objects
      -- satpos: Nx2 array with lon/lat (x/y) of satellite positions
      -- heading: Nx1 array with satellite headings in degrees
      -- swath_left: Nx2 array with lon/lat of left swath boundary
      -- swath_right: Nx2 array with lon/lat of right swath boundary
    Each dictionary represents a separate overpass.

    All arrays are masked arrays, note that missing values are common. Filter
    out missing values with numpy.ma.compress_rows().

    NOTE: ****** LON in the 'predict' files seems to be wrong --> needs to be
                 multiplied by -1. ******
    """
    # Read the file into a list of strings.
    _dirname, _name = os.path.split(fname)
    _fs = open_fs(_dirname)
    satfile = _fs.open(_name, 'r')
    satlines = satfile.readlines()
    satfile.close()

    # Determine the date from the first line.
    date = datetime.strptime(satlines[0].split()[0], "%Y/%m/%d")
    basedate = datetime.strptime("", "")

    # "result" will store the individual overpass segments.
    result = []
    segment = {"utc": [], "satpos": [], "heading": [],
               "swath_left": [], "swath_right": []}

    # Define a time difference that specifies when to start a new segment.
    # If the time between to subsequent points in the file is larger than
    # this time, a new segment will be started.
    seg_diff_time = timedelta(minutes=10)

    # Loop over data lines. Either append point to current segment or start
    # new segment. Before storing segments to the "result" list, convert
    # to masked arrays.
    for line in satlines[2:]:
        values = line.split()
        time = date + (datetime.strptime(values[0], "%H:%M:%S") - basedate)

        if len(segment["utc"]) == 0 or (time - segment["utc"][-1]) < seg_diff_time:
            segment["utc"].append(time)
            segment["satpos"].append([-1. * float(values[2]), float(values[1])])
            segment["heading"].append(float(values[3]))
            if len(values) == 8:
                segment["swath_left"].append([-1. * float(values[5]), float(values[4])])
                segment["swath_right"].append([-1. * float(values[7]), float(values[6])])
            else:
                # TODO 20100504: workaround for instruments without swath
                segment["swath_left"].append([-1. * float(values[2]), float(values[1])])
                segment["swath_right"].append([-1. * float(values[2]), float(values[1])])

        else:
            segment["utc"] = np.array(segment["utc"])
            segment["satpos"] = np.ma.masked_equal(segment["satpos"], -999.)
            segment["heading"] = np.ma.masked_equal(segment["heading"], -999.)
            segment["swath_left"] = np.ma.masked_equal(segment["swath_left"], -999.)
            segment["swath_right"] = np.ma.masked_equal(segment["swath_right"], -999.)
            result.append(segment)
            segment = {"utc": [], "satpos": [], "heading": [],
                       "swath_left": [], "swath_right": []}

    return result


class SatelliteControlWidget(QtWidgets.QWidget, ui.Ui_SatelliteDockWidget):
    def __init__(self, parent=None, view=None):
        super(SatelliteControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view

        # Currently loaded satellite overpass segments.
        self.overpass_segments = None

        # Connect slots and signals.
        self.btSelectFile.clicked.connect(self.select_file)
        self.btLoadFile.clicked.connect(self.load_file)
        self.cbSatelliteOverpasses.currentIndexChanged.connect(self.plot_overpass_track)

        self.settings_tag = "satellitedock"
        settings = load_settings_pickle(self.settings_tag, {"filename": ""})
        self.leFile.setText(settings["filename"])

    def select_file(self):
        """Slot that opens a file dialog to choose a file with satellite
           overpass predictions.
        """
        filename = getOpenFileName(self, os.path.join(os.path.dirname(str(self.leFile.text())), ''), u'All Files (*)',
                                   title=u"Open NASA satellite overpass prediction")
        if not filename:
            return
        self.leFile.setText(filename)
        save_settings_pickle(self.settings_tag, {"filename": filename})

    def load_file(self):
        """Load the file specified in leFile and fill the combobox with the
           available track segments.
        """
        # ToDo nappy needs filelike object first
        # _dirname, _name = os.path.split(self.leFile.text())
        # _fs = open_fs(_dirname)
        filename = str(self.leFile.text())
        logging.debug("loading satellite overpasses in file '%s'", filename)

        try:
            overpass_segments = read_nasa_satellite_prediction(filename)
        except (IOError, OSError, ValueError) as ex:
            logging.error(u"Problem accessing '%s' file", filename)
            QtWidgets.QMessageBox.critical(self, self.tr("Satellite Overpass Tool"),
                                           self.tr(u"ERROR:\n{}\n{}".format(type(ex), ex)))
        else:
            logging.debug("read %i segments", len(overpass_segments))

            self.cbSatelliteOverpasses.clear()
            items = [u"{} to {}".format(str(seg["utc"][0]), str(seg["utc"][-1]))
                     for seg in overpass_segments]
            items.insert(0, "None (select item to plot)")
            self.cbSatelliteOverpasses.addItems(items)

            self.overpass_segments = overpass_segments

    def plot_overpass_track(self, index):
        """
        """
        index -= 1
        logging.debug("plotting satellite overpass #%i", index)
        segment = None
        if 0 <= index < len(self.overpass_segments):
            segment = self.overpass_segments[index]
        if self.view is not None:
            self.view.plot_satellite_overpass(segment)
