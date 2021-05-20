# -*- coding: utf-8 -*-
"""

    mslib.mswms.dataaccess
    ~~~~~~~~~~~~~~~~~~~~~~

    This module provides functions to access data

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

from abc import ABCMeta, abstractmethod
import itertools
import os
import logging
import netCDF4
import numpy as np
import pint

from mslib import netCDF4tools
from mslib.utils import UR


class NWPDataAccess(metaclass=ABCMeta):
    """Abstract superclass providing a framework to let the user query
       in which data file a given variable at a given time can be found.

    The class provides the method get_filename(). It derives filenames from
    CF variable names, initialisation and valid times.q
    The method get_datapath() provides the root path where the data
    can be found.

    In subclasses, the protected method _determine_filename() must be
    implemented.
    """

    def __init__(self, rootpath, uses_init_time=True, uses_valid_time=True):
        """
        Constructor takes the path of the data directory and determines whether
        this class employs different init_times or valid_times.
        """
        self._root_path = rootpath
        self._modelname = ""
        self._use_init_time = uses_init_time
        self._use_valid_time = uses_valid_time

    @abstractmethod
    def setup(self):
        """
        Checks for existing files etc. and sets up the class. Called by
        server whenever a client requests a current capability document.
        """
        pass

    def have_data(self, variable, vartype, init_time, valid_time):
        """
        Checks whether a file with data for the specified variable,
        type and times is known. This does not trigger a search for
        updated data files on disk.
        """
        try:
            self._determine_filename(
                variable, vartype, init_time, valid_time, reload=False)
        except ValueError:
            return False
        else:
            return True

    def get_filename(self, variable, vartype, init_time, valid_time,
                     fullpath=False):
        """
        Get the filename of the file in which a given variable at
        a given time can be found.

        In case no file is available, the disk is searched for updated
        data before failing.

        Arguments:
        variable -- string with CF name of variable
        vartype -- string specifying the type of the variable (model specific).
                   For example, can be ml (model level), pl (pressure level),
                   or sfc (surface) for, e.g., ECMWF data.
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
    def is_reload_required(self, filenames):
        """
        Must be overwritten in subclass. Checks if a file was modified since last
        read-in.
        """
        pass

    @abstractmethod
    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """
        Must be overwritten in subclass. Determines the filename
        (without path) of the variable <variable> at the forecast
        timestep specified by init_time and valid_time.
        """
        pass

    def get_datapath(self):
        """
        Return the path to the data directory.
        """
        return self._root_path

    def uses_inittime_dimension(self):
        """
        Return whether this data set supports multiple init times
        """
        return self._use_init_time

    def uses_validtime_dimension(self):
        """
        Return whether this data set supports multiple valid times
        """
        return self._use_valid_time

    @abstractmethod
    def get_all_datafiles(self):
        """
        Return a list of all available data files.
        """
        pass

    @abstractmethod
    def get_init_times(self):
        """
        Return a list of available forecast init times (base times).
        """
        pass

    @abstractmethod
    def get_valid_times(self):
        """
        Return a list of available forecast times.
        """
        pass

    @abstractmethod
    def get_elevations(self, vert_type):
        """
        Return a list of available elevations for a vertical level type.
        """
        pass

    @abstractmethod
    def get_elevation_units(self, vert_type):
        """
        Returns units of supplied vertical type.
        """
        pass

    _mfDatasetArgsDict = {}

    def mfDatasetArgs(self):
        """
        Returns additional keyword for the MFDatasetCommonDims instance that
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

    def __init__(self, rootpath, domain_id, skip_dim_check=[], **kwargs):
        """
        Constructor takes the path of the data directory and determines whether
        this class employs different init_times or valid_times.
        """
        NWPDataAccess.__init__(self, rootpath, **kwargs)
        self._domain_id = domain_id
        self._available_files = None
        self._filetree = None
        self._mfDatasetArgsDict = {"skip_dim_check": skip_dim_check}
        self._file_cache = {}

    def _determine_filename(self, variable, vartype, init_time, valid_time, reload=True):
        """
        Determines the name of the data file that contains
        the variable <variable> with type <vartype> of the forecast specified
        by <init_time> and <valid_time>.
        """
        assert self._filetree is not None, "filetree is None. Forgot to call setup()?"
        try:
            filename = self._filetree[vartype][init_time][variable][valid_time]
            mtime = os.path.getmtime(os.path.join(self._root_path, filename))
            if filename in self._file_cache and mtime == self._file_cache[filename][0]:
                return filename
            else:
                raise KeyError
        except KeyError:
            if reload:
                self.setup()
            try:
                return self._filetree[vartype][init_time][variable][valid_time]
            except KeyError as ex:
                logging.error("Could not identify filename. %s %s %s %s %s %s",
                              variable, vartype, init_time, valid_time, type(ex), ex)
                raise ValueError(f"variable type {vartype} not available for variable {variable}")

    def is_reload_required(self, filenames):
        reload = False
        for filename in filenames:
            basename = os.path.basename(filename)
            if basename not in self._file_cache:
                reload = True
                break
            fullname = os.path.join(self._root_path, basename)
            if not os.path.exists(fullname):
                reload = True
                break
            mtime = os.path.getmtime(fullname)
            if mtime != self._file_cache[basename][0]:
                reload = True
                break
        if reload:
            self.setup()
        return reload

    def _parse_file(self, filename):
        elevations = {"levels": [], "units": None}
        with netCDF4.Dataset(os.path.join(self._root_path, filename)) as dataset:

            time_name, time_var = netCDF4tools.identify_CF_time(dataset)
            init_time = netCDF4tools.num2date(0, time_var.units)
            if not self.uses_inittime_dimension():
                init_time = None
            valid_times = netCDF4tools.num2date(time_var[:], time_var.units)
            if not self.uses_validtime_dimension():
                if len(valid_times) > 0:
                    raise IOError(f"Skipping file '{filename}: no support for valid time, but multiple "
                                  f"time steps present")
                valid_times = [None]
            lat_name, lat_var, lon_name, lon_var = netCDF4tools.identify_CF_lonlat(dataset)
            vert_name, vert_var, _, _, vert_type = netCDF4tools.identify_vertical_axis(dataset)

            if len(time_var.dimensions) != 1 or time_var.dimensions[0] != time_name:
                raise IOError("Problem with time coordinate variable")
            if len(lat_var.dimensions) != 1 or lat_var.dimensions[0] != lat_name:
                raise IOError("Problem with latitude coordinate variable")
            if len(lon_var.dimensions) != 1 or lon_var.dimensions[0] != lon_name:
                raise IOError("Problem with longitude coordinate variable")

            if vert_type != "sfc":
                elevations = {"levels": vert_var[:], "units": getattr(vert_var, "units", "1")}
                if vert_type in self._elevations:
                    if len(vert_var[:]) != len(self._elevations[vert_type]["levels"]):
                        raise IOError(f"Number of vertical levels does not fit to levels of "
                                      f"previous file '{self._elevations[vert_type]['filename']}'.")
                    if not np.allclose(vert_var[:], self._elevations[vert_type]["levels"]):
                        raise IOError(f"vertical levels do not fit to levels of previous "
                                      f"file '{self._elevations[vert_type]['filename']}'.")
                    if elevations["units"] != self._elevations[vert_type]["units"]:
                        raise IOError(f"vertical level units do not match previous "
                                      f"file '{self._elevations[vert_type]['filename']}'")

            standard_names = []
            for ncvarname, ncvar in dataset.variables.items():
                if hasattr(ncvar, "standard_name") and (len(ncvar.dimensions) >= 3):
                    if (ncvar.dimensions[0] != time_name or
                            ncvar.dimensions[-2] != lat_name or
                            ncvar.dimensions[-1] != lon_name):
                        logging.error("Skipping variable '%s' in file '%s': Incorrect order of dimensions",
                                      ncvarname, filename)
                        continue
                    if not hasattr(ncvar, "units"):
                        logging.error("Skipping variable '%s' in file '%s': No units attribute",
                                      ncvarname, filename)
                        continue
                    if ncvar.standard_name != "time":
                        try:
                            UR(ncvar.units)
                        except (AttributeError, ValueError, pint.UndefinedUnitError, pint.DefinitionSyntaxError):
                            logging.error("Skipping variable '%s' in file '%s': unparseable units attribute '%s'",
                                          ncvarname, filename, ncvar.units)
                            continue
                    if len(ncvar.shape) == 4 and vert_name in ncvar.dimensions:
                        standard_names.append(ncvar.standard_name)
                    elif len(ncvar.shape) == 3 and vert_type == "sfc":
                        standard_names.append(ncvar.standard_name)
        return {
            "vert_type": vert_type,
            "elevations": elevations,
            "init_time": init_time,
            "valid_times": valid_times,
            "standard_names": standard_names
        }

    def _add_to_filetree(self, filename, content):
        logging.info("File '%s' identified as '%s' type", filename, content["vert_type"])
        logging.info("Found init time '%s', %s valid_times and %s standard_names",
                     content["init_time"], len(content["valid_times"]), len(content["standard_names"]))
        if len(content["valid_times"]) == 0 or len(content["standard_names"]) == 0:
            logging.error(
                "Something is wrong with this file... valid_times='%s' standard_names='%s'",
                content["valid_times"], content["standard_names"])
        else:
            logging.debug("valid_times='%s' standard_names='%s'",
                          content["valid_times"], content["standard_names"])
        leaf = self._filetree.setdefault(content["vert_type"], {}).setdefault(content["init_time"], {})
        for standard_name in content["standard_names"]:
            var_leaf = leaf.setdefault(standard_name, {})
            for valid_time in content["valid_times"]:
                if valid_time in var_leaf:
                    logging.warning(
                        "some data was found twice! vartype='%s' init_time='%s' standard_name='%s' "
                        "valid_time='%s' first_file='%s' second_file='%s'",
                        content["vert_type"], content["init_time"], standard_name,
                        valid_time, var_leaf[valid_time], filename)
                else:
                    var_leaf[valid_time] = filename

    def setup(self):
        # Get a list of the available data files.
        self._available_files = [
            _filename for _filename in os.listdir(self._root_path) if self._domain_id in _filename]
        logging.info("Files identified for domain '%s': %s",
                     self._domain_id, self._available_files)

        for filename in list(self._file_cache):
            if filename not in self._available_files:
                del self._file_cache[filename]

        self._filetree = {}
        self._elevations = {"sfc": {"filename": None, "levels": [], "units": None}}

        # Build the tree structure.
        for filename in self._available_files:
            mtime = os.path.getmtime(os.path.join(self._root_path, filename))
            if (filename in self._file_cache) and (mtime == self._file_cache[filename][0]):
                logging.info("Using cached candidate '%s'", filename)
                content = self._file_cache[filename][1]
                if content["vert_type"] != "sfc":
                    if content["vert_type"] not in self._elevations:
                        self._elevations[content["vert_type"]] = content["elevations"]
                    if ((len(self._elevations[content["vert_type"]]["levels"]) !=
                         len(content["elevations"]["levels"])) or
                        (not np.allclose(
                         self._elevations[content["vert_type"]]["levels"],
                         content["elevations"]["levels"]))):
                        logging.error("Skipping file '%s' due to elevation mismatch", filename)
                        continue

            else:
                if filename in self._file_cache:
                    del self._file_cache[filename]
                logging.info("Opening candidate '%s'", filename)
                try:
                    content = self._parse_file(filename)
                except IOError as ex:
                    logging.error("Skipping file '%s' (%s: %s)", filename, type(ex), ex)
                    continue
                self._file_cache[filename] = (mtime, content)
            self._add_to_filetree(filename, content)

    def get_init_times(self):
        """
        Returns a list of available forecast init times (base times).
        """
        init_times = set(itertools.chain.from_iterable(
            self._filetree[_x].keys() for _x in self._filetree))
        return sorted(init_times)

    def get_valid_times(self, variable, vartype, init_time):
        """
        Returns a list of available valid times for the specified
        variable at the specified init time.
        """
        try:
            return sorted(self._filetree[vartype][init_time][variable])
        except KeyError as ex:
            logging.error("Could not find times! %s %s", type(ex), ex)
            return []

    def get_elevations(self, vert_type):
        """
        Return a list of available elevations for a vertical level type.
        """
        return self._elevations[vert_type]["levels"]

    def get_elevation_units(self, vert_type):
        """
        Return a list of available elevations for a vertical level type.
        """
        return self._elevations[vert_type]["units"]

    def get_all_valid_times(self, variable, vartype):
        """
        Similar to get_valid_times(), but returns the combined valid times
        of all available init times.
        """
        all_valid_times = []
        if vartype not in self._filetree:
            return []
        for init_time in self._filetree[vartype]:
            if variable in self._filetree[vartype][init_time]:
                all_valid_times.extend(list(self._filetree[vartype][init_time][variable]))
        return sorted(set(all_valid_times))

    def get_all_datafiles(self):
        """
        Return a list of all available data files.
        """
        return self._available_files


# to retain backwards compatibility
CachedDataAccess = DefaultDataAccess
