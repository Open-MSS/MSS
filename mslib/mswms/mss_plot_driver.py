"""Driver classes to create plots from ECMWF NetCDF data.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
             2016-2017 see AUTHORS

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

This file is part of the DLR/IPA Mission Support System Web Map Service
(MSS-WMS).

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
from datetime import datetime

import logging
import os
from abc import ABCMeta, abstractmethod

# related third party imports
import numpy as np

# local application imports
from mslib import netCDF4tools
from mslib import mss_util

"""
MSS Plot Driver
"""


class MSSPlotDriver(object):
    """Abstract super class for implementing driver classes that provide
       access to the MSS data server.

    The idea of a driver class is to encapsulate all methods related to
    loading data fields into memory. A driver can control objects from
    plotting classes that provide (a) a list of required variables and
    (b) a plotting method that only accepts data fields already loaded into
    memory.

    MSSPlotDriver implements methods that determine, given a list of required
    variables from a plotting instance <plot_object> and a forecast time
    specified by intitialisation and valid time, the corresponding data files.
    The files are opened and the NetCDF variable objects are determined.

    Classes that derive from this class need to implement the two methods
    set_plot_parameters() and plot().
    """
    __metaclass__ = ABCMeta

    def __init__(self, data_access_object):
        """Requires an instance of a data access object from the MSS
           configuration (i.e. an NWPDataAccess instance).
        """
        self.data_access = data_access_object
        self.dataset = None
        self.plot_object = None

    def __del__(self):
        """Closes the open NetCDF dataset, if existing.
        """
        logging.debug("closing plot driver")
        if self.dataset is not None:
            self.dataset.close()

    def _set_time(self, init_time, fc_time):
        """Open the dataset that corresponds to a forecast field specified
           by an initialisation and a valid time.

        This method
          determines the files that correspond to an init time and forecast step
          checks if an open NetCDF dataset exists
            if yes, checks whether it contains the requested valid time
              if not, closes the dataset and opens the corresponding one
          loads dimension data if required.
        """
        if len(self.plot_object.required_datafields) == 0:
            logging.debug("no datasets required.")
            self.dataset = None
            self.init_time = None
            self.fc_time = None
            self.times = np.array([])
            self.lat_data = np.array([])
            self.lon_data = np.array([])
            self.lat_order = 1
            self.vert_data = None
            self.vert_order = None
            self.vert_units = None
            return

        if fc_time < init_time:
            msg = "Forecast valid time cannot be earlier than " \
                  "initialisation time."
            logging.error(msg)
            raise ValueError(msg)
        fc_step = fc_time - init_time
        fc_step = fc_step.days * 24 + fc_step.seconds / 3600
        self.fc_time = fc_time
        logging.debug(u"\trequested initialisation time {}".format(init_time))
        logging.debug(u"\trequested forecast valid time {} (step {} hrs)".format(fc_time, fc_step))

        # Check if a dataset is open and if it contains the requested times.
        # (a dataset will only be open if the used layer has not changed,
        # i.e. the required variables have not changed as well).
        if self.dataset is not None:
            logging.debug("checking on open dataset.")
            if self.init_time == init_time:
                logging.debug(u"\tinitialisation time ok ({}).".format(init_time))
                if fc_time in self.times:
                    logging.debug(u"\tforecast valid time contained ({}).".format(fc_time))
                    return
            logging.debug("need to re-open input files.")
            self.dataset.close()
            self.dataset = None

        # Determine the input files from the required variables and the
        # requested time:

        # Get a list of the available data files. The path to the data files
        # is provided by the NWPDataAccess object in self.data_access.
        available_files = self.data_access.get_all_datafiles()

        # Create the names of the files containing the required parameters.
        filenames = []
        for vartype, var in self.plot_object.required_datafields:
            filename = self.data_access.get_filename(var, vartype,
                                                     init_time, fc_time,
                                                     fullpath=True)
            short_filename = os.path.basename(filename)
            if filename not in filenames:
                filenames.append(filename)
            logging.debug(u"\tvariable '{}' requires input file '{}'".format(var, short_filename))
            if short_filename not in available_files:
                logging.error(u"ERROR: file '{}' does not exist".format(short_filename))
                raise IOError(u"file '{}' does not exist".format(short_filename))

        if len(filenames) == 0:
            raise ValueError("no files found that correspond to the specified "
                             "datafields. Aborting..")

        self.init_time = init_time

        # Open NetCDF files as one dataset with common dimensions.
        logging.debug("opening datasets.")
        dsKWargs = self.data_access.mfDatasetArgs()
        dataset = netCDF4tools.MFDatasetCommonDims(filenames, **dsKWargs)

        # Load and check time dimension. self.dataset will remain None
        # if an Exception is raised here.
        timename, timevar = netCDF4tools.identify_CF_time(dataset)
        times = netCDF4tools.num2date(timevar[:], timevar.units)
        if init_time != netCDF4tools.num2date(0, timevar.units):
            dataset.close()
            raise ValueError("wrong initialisation time in input")

        if fc_time not in times:
            msg = u"Forecast valid time {} is not available.".format(fc_time)
            logging.error(msg)
            dataset.close()
            raise ValueError(msg)

        # Load lat/lon dimensions.
        try:
            lat_data, lon_data, lat_order = \
                netCDF4tools.get_latlon_data(dataset)
        except Exception as ex:
            logging.error("ERROR: {} {}".format(type(ex), ex))
            dataset.close()
            raise

        # Try to load vertical hybrid coordinate (model levels), isopressure
        # coordinate (pressure levels) or iso-potential-vorticity (pv levels).
        # NOTE: This code assumes that a file contains data on exactly one level
        # type, not on more that one!
        vert_data = None
        vert_orientation = None
        vert_units = None

        hybrid_name, hybrid_var, hybrid_orientation = \
            netCDF4tools.identify_CF_hybrid(dataset)
        if hybrid_var is not None:
            vert_data = hybrid_var[:]
            vert_orientation = hybrid_orientation
            vert_units = "model_level"

        if vert_data is None:
            isopressure_name, isopressure_var, isopressure_orientation = \
                netCDF4tools.identify_CF_isopressure(dataset)
            if isopressure_var is not None:
                vert_data = isopressure_var[:]
                vert_orientation = isopressure_orientation
                vert_units = "hPa"

        if vert_data is None:
            isopotvort_name, isopotvort_var, isopotvort_orientation = \
                netCDF4tools.identify_CF_isopotvort(dataset)
            if isopotvort_var is not None:
                vert_data = isopotvort_var[:]
                vert_orientation = isopotvort_orientation
                vert_units = "10^-3 PVU"

        if vert_data is None:
            isoalt_name, isoalt_var, isoalt_orientation = \
                netCDF4tools.identify_CF_isoaltitude(dataset)
            if isoalt_var is not None:
                vert_data = isoalt_var[:]
                vert_orientation = isoalt_orientation
                vert_units = isoalt_var.units

        if vert_data is None:
            isoalt_name, isoalt_var, isoalt_orientation = \
                netCDF4tools.identify_CF_isopottemp(dataset)
            if isoalt_var is not None:
                vert_data = isoalt_var[:]
                vert_orientation = isoalt_orientation
                vert_units = isoalt_var.units
        self.dataset = dataset
        self.times = times
        self.lat_data = lat_data
        self.lon_data = lon_data
        self.lat_order = lat_order
        self.vert_data = vert_data
        self.vert_order = vert_orientation
        self.vert_units = vert_units

        # Identify the variable objects from the NetCDF file that correspond
        # to the data fields required by the plot object.
        self._find_data_vars()

    def _find_data_vars(self):
        """Find NetCDF variables of required data fields.

        A dictionary data_vars is created. Its keys are the CF standard names
        of the variables provided by the plot object. The values are pointers
        to the NetCDF variable objects.

        <data_vars> can be accessed as <self.data_vars>.
        """
        self.data_vars = {}
        for df_type, df_name in self.plot_object.required_datafields:
            varname, var = netCDF4tools.identify_variable(self.dataset, df_name)
            logging.debug("\tidentified variable <{}> for field <{}>".format(varname, df_name))
            self.data_vars[df_name] = var

    @abstractmethod
    def set_plot_parameters(self, plot_object, init_time=None, valid_time=None,
                            style=None, bbox=None, figsize=(800, 600),
                            noframe=False, require_reload=False, transparent=False,
                            return_format="image/png"):
        """Set parameters controlling the plot.

        Parameters not passed as arguments are reset to standard values.

        THIS METHOD NEEDS TO BE REIMPLEMENTED IN ANY CLASS DERIVING FROM
        MSSPlotDriver!

        Derived methods need to call the super method before all other
        statements.
        """
        logging.debug("using plot object '{}'".format(plot_object.name))
        logging.debug("\tfigure size {} in pixels".format(figsize))

        # If the plot object has been changed, the dataset needs to be reloaded
        # (the required variables could have changed).
        if self.plot_object is not None:
            require_reload = require_reload or (self.plot_object != plot_object)
        if require_reload and self.dataset is not None:
            self.dataset.close()
            self.dataset = None

        self.plot_object = plot_object
        self.figsize = figsize
        self.noframe = noframe
        self.style = style
        self.bbox = bbox
        self.transparent = transparent
        self.return_format = return_format

        self._set_time(init_time, valid_time)

    @abstractmethod
    def update_plot_parameters(self, plot_object=None, figsize=None, style=None,
                               bbox=None, init_time=None, valid_time=None,
                               noframe=None, transparent=None, return_format=None):
        """Update parameters controlling the plot.

        Similar to set_plot_parameters(), but keeps all parameters already
        set except the ones that are specified.

        THIS METHOD NEEDS TO BE REIMPLEMENTED IN ANY CLASS DERIVING FROM
        MSSPlotDriver!

        Derived methods need to call the super method before all other
        statements.
        """
        plot_object = plot_object if plot_object is not None else self.plot_object
        figsize = figsize if figsize is not None else self.figsize
        noframe = noframe if noframe is not None else self.noframe
        init_time = init_time if init_time is not None else self.init_time
        valid_time = valid_time if valid_time is not None else self.valid_time
        style = style if style is not None else self.style
        bbox = bbox if bbox is not None else self.bbox
        transparent = transparent if transparent is not None else self.transparent
        return_format = return_format if return_format is not None else self.return_format
        # Explicitly call MSSPlotDriver's set_plot_parameters(). A "self.--"
        # call would call the derived class's method and thus reset
        # parameters specific to the derived class.
        MSSPlotDriver.set_plot_parameters(self, plot_object,
                                          init_time=init_time,
                                          valid_time=valid_time,
                                          figsize=figsize,
                                          style=style,
                                          bbox=bbox,
                                          noframe=noframe,
                                          transparent=transparent,
                                          return_format=return_format)

    @abstractmethod
    def plot(self):
        """Plot the figure (i.e. load the data fields and call the
           corresponding plotting routines of the plot object).

        THIS METHOD NEEDS TO BE REIMPLEMENTED IN ANY CLASS DERIVING FROM
        MSSPlotDriver!
        """
        pass

    def get_init_times(self):
        """Returns a list of available forecast init times (base times).
        """
        return self.data_access.get_init_times()

    def get_all_valid_times(self, variable, vartype):
        """See ECMWFDataAccess.get_all_valid_times().
        """
        return self.data_access.get_all_valid_times(variable, vartype)

    def get_valid_times(self, variable, vartype, init_time):
        """See ECMWFDataAccess.get_valid_times().
        """
        return self.data_access.get_valid_times(variable, vartype, init_time)


"""
Vertical Section Driver
"""


class VerticalSectionDriver(MSSPlotDriver):
    """The vertical section driver is responsible for loading the data that
       is to be plotted and for calling the plotting routines (that have
       to be registered).
    """

    def set_plot_parameters(self, plot_object=None, vsec_path=None,
                            vsec_numpoints=101, vsec_path_connection='linear',
                            vsec_numlabels=10,
                            init_time=None, valid_time=None, style=None,
                            bbox=None, figsize=(800, 600), noframe=False,
                            show=False, transparent=False,
                            return_format="image/png"):
        """
        """
        MSSPlotDriver.set_plot_parameters(self, plot_object,
                                          init_time=init_time,
                                          valid_time=valid_time,
                                          style=style,
                                          bbox=bbox,
                                          figsize=figsize, noframe=noframe,
                                          transparent=transparent,
                                          return_format=return_format)
        self._set_vertical_section_path(vsec_path, vsec_numpoints,
                                        vsec_path_connection)
        self.show = show
        self.vsec_numlabels = vsec_numlabels

    def update_plot_parameters(self, plot_object=None, vsec_path=None,
                               vsec_numpoints=None, vsec_path_connection=None,
                               vsec_numlabels=None,
                               init_time=None, valid_time=None, style=None,
                               bbox=None, figsize=None, noframe=None, show=None,
                               transparent=None, return_format=None):
        """
        """
        plot_object = plot_object if plot_object is not None else self.plot_object
        figsize = figsize if figsize is not None else self.figsize
        noframe = noframe if noframe is not None else self.noframe
        init_time = init_time if init_time is not None else self.init_time
        valid_time = valid_time if valid_time is not None else self.valid_time
        style = style if style is not None else self.style
        bbox = bbox if bbox is not None else self.bbox
        vsec_path = vsec_path if vsec_path is not None else self.vsec_path
        vsec_numpoints = vsec_numpoints if vsec_numpoints is not None else self.vsec_numpoints
        vsec_numlabels = vsec_numlabels if vsec_numlabels is not None else self.vsec_numlabels
        vsec_path_connection = vsec_path_connection if vsec_path_connection is not None \
            else self.vsec_path_connection
        show = show if show else self.show
        transparent = transparent if transparent is not None else self.transparent
        return_format = return_format if return_format is not None else self.return_format
        self.set_plot_parameters(plot_object=plot_object,
                                 vsec_path=vsec_path,
                                 vsec_numpoints=vsec_numpoints,
                                 vsec_path_connection=vsec_path_connection,
                                 vsec_numlabels=vsec_numlabels,
                                 init_time=init_time,
                                 valid_time=valid_time,
                                 style=style,
                                 bbox=bbox,
                                 figsize=figsize,
                                 noframe=noframe,
                                 show=show,
                                 transparent=transparent,
                                 return_format=return_format)

    def _set_vertical_section_path(self, vsec_path, vsec_numpoints=101,
                                   vsec_path_connection='linear'):
        """
        """
        logging.debug("computing {:} interpolation points, connection: {}"
                      .format(vsec_numpoints, vsec_path_connection))
        self.lats, self.lons = mss_util.path_points(vsec_path,
                                                    numpoints=vsec_numpoints,
                                                    connection=vsec_path_connection)
        self.vsec_path = vsec_path
        self.vsec_numpoints = vsec_numpoints
        self.vsec_path_connection = vsec_path_connection

    def _load_interpolate_timestep(self):
        """Load and interpolate the data fields as required by the vertical
           section style instance. Only data of time <fc_time> is processed.

        Shifts the data fields such that the longitudes are in the range
        left_longitude .. left_longitude+360, where left_longitude is the
        westmost longitude appearing in the list of waypoints minus one
        gridpoint (to include all waypoint longitudes).

        Necessary to prevent data cut-offs in situations where the requested
        cross section crosses the data longitude boundaries (e.g. data is
        stored on a 0..360 grid, but the path is in the range -10..+20).
        """
        if self.dataset is None:
            return {}
        data = {}
        timestep = self.times.searchsorted(self.fc_time)
        logging.debug("loading data for time step {} ({})".format(timestep, self.fc_time))

        # Determine the westmost longitude in the cross-section path. Subtract
        # one gridbox size to obtain "left_longitude".
        dlon = self.lon_data[1] - self.lon_data[0]
        left_longitude = self.lons.min() - dlon
        logging.debug("shifting data grid to gridpoint west of westmost "
                      "longitude in path: {:.2f} (path {:.2f}).."
                      .format(left_longitude, self.lons.min()))

        # Shift the longitude field such that the data is in the range
        # left_longitude .. left_longitude+360.
        # NOTE: This does not overwrite self.lon_data (which is required
        # in its original form in case other data is loaded while this
        # file is open).
        # print self.lon_data
        lon_data = ((self.lon_data - left_longitude) % 360) + left_longitude
        # print lon_data
        lon_indices = lon_data.argsort()
        lon_data = lon_data[lon_indices]
        # print lon_data

        for name, var in self.data_vars.items():
            if len(var.shape) == 4:
                var_data = var[timestep, ::-self.vert_order, ::self.lat_order, :]
            else:
                var_data = var[:][timestep, np.newaxis, ::self.lat_order, :]
            logging.debug("\tLoaded {:.2f} Mbytes from data field <{:}> at timestep {:}.".format(
                          var_data.nbytes / 1048576., name, timestep))
            logging.debug("\tVertical dimension direction is {}.".format(
                          "up" if self.vert_order == 1 else "down"))
            logging.debug("\tInterpolating to cross-section path.")
            # Re-arange longitude dimension in the data field.
            var_data = var_data[:, :, lon_indices]
            data[name] = mss_util.interpolate_vertsec3(var_data, self.lat_data, lon_data,
                                                       self.lats, self.lons)
            # print data[name][:,30]
            # Free memory.
            del var_data

        return data

    def shift_data(self):
        """Shift the data fields such that the longitudes are in the range
        left_longitude .. left_longitude+360, where left_longitude is the
        westmost longitude appearing in the list of waypoints minus one
        gridpoint (to include all waypoint longitudes).

        Necessary to prevent data cut-offs in situations where the requested
        cross section crosses the data longitude boundaries (e.g. data is
        stored on a 0..360 grid, but the path is in the range -10..+20).
        """
        # Determine the leftmost longitude in the plot.
        left_longitude = self.lons.min()
        logging.debug(u"shifting data grid to leftmost longitude in path "
                      u"({:.2f})..".format(left_longitude))

        # Shift the longitude field such that the data is in the range
        # left_longitude .. left_longitude+360.
        # print self.lons
        self.lons = ((self.lons - left_longitude) % 360) + left_longitude
        lon_indices = self.lons.argsort()
        self.lons = self.lons[lon_indices]
        # print self.lons

        # Shift data fields correspondingly.
        for key in self.data.keys():
            self.data[key] = self.data[key][:, lon_indices]

    def plot(self):
        """
        """
        d1 = datetime.now()

        # Load and interpolate the data fields as required by the vertical
        # section style instance. <data> is a dictionary containing the
        # interpolated curtains of the variables identified through CF
        # standard names as specified by <self.vsec_style_instance>.
        data = self._load_interpolate_timestep()

        d2 = datetime.now()
        logging.debug("Loaded and interpolated data (required time {}).".format(d2 - d1))
        logging.debug("Plotting interpolated curtain.")

        if len(self.lat_data) > 1 and len(self.lon_data) > 1:
            resolution = (self.lon_data[1] - self.lon_data[0],
                          self.lat_data[1] - self.lat_data[0])
        else:
            resolution = (-1, -1)

        # Call the plotting method of the vertical section style instance.
        image = self.plot_object.plot_vsection(data, self.lats, self.lons,
                                               valid_time=self.fc_time,
                                               init_time=self.init_time,
                                               resolution=resolution,
                                               bbox=self.bbox,
                                               style=self.style,
                                               show=self.show,
                                               highlight=self.vsec_path,
                                               noframe=self.noframe,
                                               figsize=self.figsize,
                                               transparent=self.transparent,
                                               numlabels=self.vsec_numlabels,
                                               return_format=self.return_format)
        # Free memory.
        del data

        d3 = datetime.now()
        logging.debug("Finished plotting (required time {}; total "
                      "time {}).\n".format(d3 - d2, d3 - d1))

        return image


"""
Horizontal Section Driver
"""


class HorizontalSectionDriver(MSSPlotDriver):
    """The horizontal section driver is responsible for loading the data that
       is to be plotted and for calling the plotting routines (that have
       to be registered).
    """

    def set_plot_parameters(self, plot_object=None, bbox=None,
                            level=None, epsg=None,
                            init_time=None, valid_time=None, style=None,
                            figsize=(800, 600), noframe=False, show=False,
                            transparent=False, return_format="image/png"):
        """
        """
        MSSPlotDriver.set_plot_parameters(self, plot_object,
                                          init_time=init_time,
                                          valid_time=valid_time,
                                          style=style,
                                          bbox=bbox,
                                          figsize=figsize, noframe=noframe,
                                          transparent=transparent,
                                          return_format=return_format)
        self.level = level
        self.actual_level = None
        self.epsg = epsg
        self.show = show

    def update_plot_parameters(self, plot_object=None, bbox=None,
                               level=None, epsg=None,
                               init_time=None, valid_time=None, style=None,
                               figsize=None, noframe=None, show=None,
                               transparent=None, return_format=None):
        """
        """
        plot_object = plot_object if plot_object is not None else self.plot_object
        figsize = figsize if figsize is not None else self.figsize
        noframe = noframe if noframe is not None else self.noframe
        init_time = init_time if init_time is not None else self.init_time
        valid_time = valid_time if valid_time is not None else self.valid_time
        style = style if style is not None else self.style
        bbox = bbox if bbox is not None else self.bbox
        level = level if level is not None else self.level
        epsg = epsg if epsg is not None else self.epsg
        show = show if show is not None else self.show
        transparent = transparent if transparent is not None else self.transparent
        return_format = return_format if return_format is not None else self.return_format
        self.set_plot_parameters(plot_object=plot_object,
                                 bbox=bbox,
                                 level=level,
                                 epsg=epsg,
                                 init_time=init_time,
                                 valid_time=valid_time,
                                 style=style,
                                 figsize=figsize,
                                 noframe=noframe,
                                 show=show,
                                 transparent=transparent,
                                 return_format=return_format)

    def _load_timestep(self):
        """Load the data fields as required by the horizontal section style
           instance at the current timestep.
        """
        if self.dataset is None:
            return {}
        data = {}
        timestep = self.times.searchsorted(self.fc_time)
        level = None
        if self.level is not None:
            level = self.vert_data[::self.vert_order].searchsorted(self.level)
            if self.vert_order == -1:
                level = len(self.vert_data) - 1 - level
            self.actual_level = self.vert_data[level]
        logging.debug("loading data for time step {} ({}), level index {} (level {})".format(
                      timestep, self.fc_time, level, self.level))
        for name, var in self.data_vars.items():
            if level is None or len(var.shape) == 3:
                # 2D fields: time, lat, lon.
                var_data = var[timestep, ::self.lat_order, :]
            else:
                # 3D fields: time, level, lat, lon.
                var_data = var[timestep, level, ::self.lat_order, :]
            logging.debug("\tLoaded {:.2f} Mbytes from data field <{}>."
                          .format(var_data.nbytes / 1048576., name))
            data[name] = var_data
            # Free memory.
            del var_data

        return data

    def plot(self):
        """
        """
        d1 = datetime.now()

        # Load and interpolate the data fields as required by the horizontal
        # section style instance. <data> is a dictionary containing the
        # horizontal sections of the variables identified through CF
        # standard names as specified by <self.hsec_style_instance>.
        data = self._load_timestep()

        d2 = datetime.now()
        logging.debug("Loaded data (required time %s)." % (d2 - d1))
        logging.debug("Plotting horizontal section.")

        if len(self.lat_data) > 1:
            resolution = (self.lat_data[1] - self.lat_data[0])
        else:
            resolution = 0

        # Call the plotting method of the horizontal section style instance.
        image = self.plot_object.plot_hsection(data,
                                               self.lat_data,
                                               self.lon_data,
                                               self.bbox,
                                               level=self.actual_level,
                                               valid_time=self.fc_time,
                                               init_time=self.init_time,
                                               resolution=resolution,
                                               show=self.show,
                                               epsg=self.epsg,
                                               style=self.style,
                                               noframe=self.noframe,
                                               figsize=self.figsize,
                                               transparent=self.transparent)
        # Free memory.
        del data

        d3 = datetime.now()
        logging.debug("Finished plotting (required time {}; total "
                      "time {}).\n".format(d3 - d2, d3 - d1))

        return image


"""
Module TESTING
"""


def test_vsec_clouds_path():
    """TEST: Create a vertical section of the CLOUDS style.
    """
    # Define cross-section path (great circle interpolation between two points).
    p1 = [45.00, 8.]
    p2 = [50.00, 12.]
    p3 = [51.00, 15.]
    p4 = [48.00, 11.]

    import mss_wms_settings
    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2010, 12, 14, 00)
    valid_time = datetime(2010, 12, 14, 15)

    import mpl_vsec_styles
    # plot_object = mpl_vsec_styles.VSCloudsStyle01(p_top=20000.)
    plot_object = mpl_vsec_styles.VSTemperatureStyle01(p_top=2000.)

    vsec = VerticalSectionDriver(nwpaccess)
    vsec.set_plot_parameters(plot_object=plot_object,
                             vsec_path=[p1, p2, p3, p4],
                             vsec_numpoints=101,
                             vsec_path_connection='greatcircle',
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=False,
                             show=True)
    vsec.plot()


def test_hsec_clouds_total():
    """TEST: Create a horizontal section of the CLOUDS style.
    """
    # Define a bounding box for the map.
    #    bbox = [0,30,30,60]
    bbox = [-22.5, 27.5, 55, 62.5]

    import mss_wms_settings
    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2010, 12, 14, 00)
    valid_time = datetime(2010, 12, 14, 15)

    import mpl_hsec_styles
    plot_object = mpl_hsec_styles.HSCloudsStyle01()

    hsec = HorizontalSectionDriver(nwpaccess)
    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             # epsg=4326,
                             epsg=77790010,
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=False,
                             show=True)
    hsec.plot()


def test_hsec_temp():
    """TEST: Create a horizontal section of the TEMPERATURE style.
    """
    # Define a bounding box for the map.
    #    bbox = [0,30,30,60]
    bbox = [-22.5, 27.5, 55, 62.5]

    import mss_wms_settings
    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2010, 12, 16, 00)
    valid_time = datetime(2010, 12, 16, 15)

    import mpl_hsec_styles
    #    plot_object = mpl_hsec_styles.HS_TemperatureStyle_ML_01()
    #    level = 50
    plot_object = mpl_hsec_styles.HS_TemperatureStyle_PL_01()
    level = 925

    hsec = HorizontalSectionDriver(nwpaccess)
    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             level=level,
                             # epsg=4326,
                             epsg=77790010,
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=True,
                             show=True)
    hsec.plot()


def test_hsec_geopwind():
    """TEST: Create a horizontal section.
    """
    # Define a bounding box for the map.
    bbox = [-22.5, 27.5, 55, 62.5]

    import mss_wms_settings
    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2010, 12, 16, 00)
    valid_time = datetime(2010, 12, 16, 15)

    import mpl_hsec_styles
    plot_object = mpl_hsec_styles.HS_GeopotentialWindStyle_PL()
    level = 300

    hsec = HorizontalSectionDriver(nwpaccess)
    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             level=level,
                             # epsg=4326,
                             epsg=77790010,
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=True,
                             show=True)
    hsec.plot()


if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s %(asctime)s %(funcName)s || %(message)s")

    # test_vsec_clouds_path()
    # test_hsec_clouds_total()
    test_hsec_temp()
    # test_hsec_geopwind()
