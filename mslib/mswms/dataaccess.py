# -*- coding: utf-8 -*-
"""

    mslib.mswms.dataaccess
    ~~~~~~~~~~~~~~~~~~~~~~

    This module provides functions to access data

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

from __future__ import division

from abc import ABCMeta, abstractmethod
import itertools
import os
import logging
import netCDF4
import numpy as np

from mslib import netCDF4tools
from future.utils import with_metaclass


class NWPDataAccess(with_metaclass(ABCMeta, object)):
    """Abstract superclass providing a framework to let the user query
       in which data file a given variable at a given time can be found.

    The class provides the method get_filename(). It derives filenames from
    CF variable names, initialisation and valid times.q
    The method get_datapath() provides the root path where the data
    can be found.

    In subclasses, the protected method _determine_filename() must be
    implemented.
    """

    def __init__(self, rootpath):
        """Constructor takes the path of the data directory.
        """
        self._root_path = rootpath
        self._modelname = ""

    @abstractmethod
    def setup(self):
        """Checks for existing files etc. and sets up the class. Called by
           server whenever a client requests a current capability document.
        """
        pass

    def get_filename(self, variable, vartype, init_time, valid_time,
                     fullpath=False):
        """Get the filename of the file in which a given variable at
           a given time can be found.

        Arguments:
        variable -- string with CF name of variable
        vartype -- string specifying the type of the variable (model specific).
                   For example, can be ml (model level), pl (pressure level),
                   or sfc (surface) for ECMWF data.
        init_time -- datetime object with initialisation time of forecast run
        valid_time -- datetime object with valid time of forecast
        fullpath -- if True, the complete path to the file will be returned.
                    Default is False, only the filename will be returned.
        """
        filename = self._determine_filename(variable, vartype,
                                            init_time, valid_time)
        if fullpath:
            return os.path.join(self._root_path, filename)
        else:
            return filename

    @abstractmethod
    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """Must be overwritten in subclass. Determines the filename
           (without path) of the variable <variable> at the forecast
           timestep specified by init_time and valid_time.
        """
        pass

    def get_datapath(self):
        """Return the path to the data directory.
        """
        return self._root_path

    @abstractmethod
    def get_all_datafiles(self):
        """Return a list of all available data files.
        """
        pass

    @abstractmethod
    def get_init_times(self):
        """Return a list of available forecast init times (base times).
        """
        pass

    _mfDatasetArgsDict = {}

    def mfDatasetArgs(self):
        """Returns additional keyword for the MFDatasetCommonDims instance that
           handles the input data of this dataset. See the MFDatasetCommonDims
           documentation for further details.
           Mainly provided as a workaround for numerical inaccuracies introduced
           to the NetCDF files by netcdf-java 4.3.
           (mr, 16Oct2012)
        """
        return self._mfDatasetArgsDict


class DefaultDataAccess(NWPDataAccess):
    """
    Subclass to NWPDataAccess for accessing properly constructed NetCDF files
    Constructor needs information on domain ID.
    """

    # Workaround for the numerical issue concering the lon dimension in
    # NetCDF files produced by netcdf-java 4.3..
    _mfDatasetArgsDict = {"skipDimCheck": ["lon"]}

    def __init__(self, rootpath, domain_id):
        NWPDataAccess.__init__(self, rootpath)
        self._domain_id = domain_id
        self._available_files = None
        self._filetree = None

    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """Determines the name of the ECMWF data file the contains
           the variable <variable> of the forecast specified by
           init_time and valid_time.
        """
        assert self._filetree is not None, "filetree is None. Forgot to call setup()?"
        try:
            print(variable, vartype, self._filetree[vartype][init_time][variable][valid_time])
            return self._filetree[vartype][init_time][variable][valid_time]
        except KeyError as ex:
            self.setup()
            try:
                return self._filetree[vartype][init_time][variable][valid_time]
            except KeyError as ex:
                logging.error("Could not identify filename. %s %s %s %s %s %s",
                              variable, vartype, init_time, valid_time, type(ex), ex)
                raise ValueError(u"variable type {} not available for variable {}"
                                 .format(vartype, variable))

    def setup(self):
        # Get a list of the available data files.
        self._available_files = [
            _filename for _filename in os.listdir(self._root_path) if self._domain_id in _filename]
        logging.info("Files identified for domain '%s': %s",
                     self._domain_id, self._available_files)

        self._filetree = {}
        elevations = {}

        # Build the tree structure.
        for filename in self._available_files:
            logging.info("Opening candidate '%s'", filename)
            try:
                with netCDF4.Dataset(os.path.join(self._root_path, filename)) as dataset:

                    time_name, time_var = netCDF4tools.identify_CF_time(dataset)
                    init_time = netCDF4tools.num2date(0, time_var.units)
                    valid_times = netCDF4tools.num2date(time_var[:], time_var.units)
                    lat_name, lat_var, lon_name, lon_var = netCDF4tools.identify_CF_lonlat(dataset)
                    vert_name, vert_var, _, _, vert_type = netCDF4tools.identify_vertical_axis(dataset)

                    if len(time_var.dimensions) != 1 or time_var.dimensions[0] != time_name:
                        logging.error("Skipping file '%s': problem with time coordinate variable", filename)
                        continue
                    if len(lat_var.dimensions) != 1 or lat_var.dimensions[0] != lat_name:
                        logging.error("Skipping file '%s': problem with latitude coordinate variable", filename)
                        continue
                    if len(lon_var.dimensions) != 1 or lon_var.dimensions[0] != lon_name:
                        logging.error("Skipping file '%s': problem with longitude coordinate variable", filename)
                        continue

                    if vert_type != "sfc":
                        if vert_type in elevations:
                            if not np.allclose(vert_var[:], elevations[vert_type]):
                                logging.error("Skipping file '%s': elevations do not fit to previous elevations.",
                                              filename)
                                continue
                        else:
                            elevations[vert_type] = vert_var[:]

                    standard_names = []
                    for ncvarname, ncvar in dataset.variables.items():
                        if hasattr(ncvar, "standard_name"):
                            if (len(ncvar.dimensions) >= 3 and (
                                    ncvar.dimensions[0] != time_name or
                                    ncvar.dimensions[-2] != lat_name or
                                    ncvar.dimensions[-1] != lon_name)):
                                logging.error("Skipping variable '%s' in file '%s': Incorrect order of dimensions",
                                              ncvarname, filename)
                                continue
                            if len(ncvar.shape) == 4 and vert_name in ncvar.dimensions:
                                standard_names.append(ncvar.standard_name)
                            elif len(ncvar.shape) == 3 and vert_type == "sfc":
                                standard_names.append(ncvar.standard_name)
            except IOError as ex:
                logging.error("Skipping file '%s' (%s: %s)", filename, type(ex), ex)
                continue

            logging.info("File '%s' identified as '%s' type", filename, vert_type)
            logging.info("Found init time '%s', %s valid_times and %s standard_names",
                         init_time, len(valid_times), len(standard_names))
            if len(valid_times) == 0 or len(standard_names) == 0:
                logging.error(
                    "Something is wrong with this file... valid_times='%s' standard_names='%s'",
                    valid_times, standard_names)
            else:
                logging.debug("valid_times='%s' standard_names='%s'", valid_times, standard_names)

            leaf = self._filetree.setdefault(vert_type, {}).setdefault(init_time, {})
            for standard_name in standard_names:
                var_leaf = leaf.setdefault(standard_name, {})
                for valid_time in valid_times:
                    if valid_time in var_leaf:
                        logging.warn(
                            "some data was found twice! vartype='%s' init_time='%s' standard_name='%s' "
                            "valid_time='%s' first_file='%s' second_file='%s'",
                            vert_type, init_time, standard_name, valid_time, var_leaf[valid_time], filename)
                    else:
                        var_leaf[valid_time] = filename

        return self._filetree

    def get_init_times(self):
        """Returns a list of available forecast init times (base times).
        """
        init_times = set(itertools.chain.from_iterable(
            self._filetree[_x].keys() for _x in self._filetree))
        return sorted(list(init_times))

    def get_valid_times(self, variable, vartype, init_time):
        """Returns a list of available valid times for the specified
           variable at the specified init time.
        """
        try:
            return sorted(list(self._filetree[vartype][init_time][variable].keys()))
        except KeyError as ex:
            logging.error("Could not find times! %s %s", type(ex), ex)
            return []

    def get_all_valid_times(self, variable, vartype):
        """Similar to get_valid_times(), but returns the combined valid times
           of all available init times.
        """
        all_valid_times = []
        if vartype not in self._filetree:
            return []
        for init_time in self._filetree[vartype]:
            if variable in self._filetree[vartype][init_time]:
                all_valid_times.extend(list(self._filetree[vartype][init_time][variable].keys()))
        return sorted(list(set(all_valid_times)))

    def get_all_datafiles(self):
        """Return a list of all available data files.
        """
        return self._available_files
