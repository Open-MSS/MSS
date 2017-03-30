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

from abc import ABCMeta, abstractmethod
import glob
import re
import os
import logging
import netCDF4
from datetime import datetime, timedelta
import time
import hashlib
import pickle

from mslib import netCDF4tools
from mslib.mswms.msschem import MSSChemTargets

valid_time_cache = None
# Maximum size of the cache in bytes.
valid_time_cache_max_size_bytes = 10 * 1024 * 1024
# Maximum age of a cached file in seconds.
valid_time_cache_max_age_seconds = 10 * 86400


class NWPDataAccess(object):
    """Abstract superclass providing a framework to let the user query
       in which data file a given variable at a given time can be found.

    The class provides the method get_filename(). It derives filenames from
    CF variable names, initialisation and valid times.
    The method get_datapath() provides the root path where the data
    can be found.

    In subclasses, the protected method _determine_filename() must be
    implemented.
    """
    __metaclass__ = ABCMeta

    def __init__(self, rootpath):
        """Constructor takes the path of the data directory.
        """
        self._root_path = rootpath

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

    def md5_filename(self, filename):
        """
        """
        md5_filename = hashlib.md5(filename + repr(os.path.getmtime(filename))).hexdigest()
        md5_filename += ".vt_cache_pickle"
        return md5_filename

    def check_valid_cache(self, filename):
        """
        """
        valid_times = None
        filename = os.path.join(valid_time_cache, self.md5_filename(filename))
        if os.path.exists(filename):
            try:
                with open(filename, "r") as fileobj:
                    valid_times = pickle.load(fileobj)
            except (pickle.UnpicklingError, OSError, IOError), ex:
                logging.error(u"Error reading cache file '{}': {} - {}".format(filename, type(ex), ex))
                logging.error(u"os.stat: {}".format(os.stat(filename)))

        return valid_times

    def save_valid_cache(self, filename, valid_times):
        """
        """
        if valid_time_cache is not None and not os.path.exists(valid_time_cache):
            os.makedirs(valid_time_cache)
        filename = os.path.join(valid_time_cache, self.md5_filename(filename))
        if not os.path.exists(filename):
            try:
                with open(filename, "w") as fileobj:
                    pickle.dump(valid_times, fileobj)
            except (pickle.PicklingError, OSError, IOError), ex:
                logging.error(u"Error writing cache file '{}': {} - {}".format(filename, type(ex), ex))

    def serviceCache(self):
        """Service the cache: Remove all files older than the maximum file
           age specified below, and remove the oldest files if the
           maximum cache size has been reached.
        """
        # logging.debug("servicing cache..")

        # Create a list of all files in the cache.
        files = [os.path.join(valid_time_cache, f) for f in os.listdir(valid_time_cache)]
        # Add the ages of the files (via modification times in sec since epoch)
        # and the file sizes.
        # (current time in sec since epoch)
        current_time = time.time()
        files = [(f, os.path.getsize(f), current_time - os.path.getmtime(f))
                 for f in files if os.path.isfile(f)]
        # Sort the files accordings to their age (i.e. use the
        # third argument of the tuples (file, fsize, fage) as the sorting key).
        files.sort(key=lambda x: x[2])

        # Loop over all cached files, staring with the youngest. Once the
        # maximum cache size has been reached, all files left will be
        # removed (i.e. the oldest files). All files exceeding the maximum
        # file age will also be removed.
        cum_size_bytes = 0
        removed_files = 0
        for filename, filesize, fileage in files:
            cum_size_bytes += filesize
            if (cum_size_bytes > valid_time_cache_max_size_bytes) or fileage > valid_time_cache_max_age_seconds:
                try:
                    os.remove(filename)
                except (OSError, IOError), ex:
                    logging.error(u"Could not remove {:}: {:} - {:}".format(filename, type(ex), ex))
                    logging.error(u"os.stat: {}".format(os.stat(filename)))
                else:
                    removed_files += 1
        logging.info(u"cache has been cleaned ({:d} files removed).".format(removed_files))

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


class ECMWFDataAccess(NWPDataAccess):
    """Subclass to NWPDataAccess for accessing ECMWF data.

    Constructor needs information on domain ID.
    """
    _file_template = "$Y$m$d_$H_ecmwf_forecast.{gridtype}.{domain_id}.{fc_step:03d}.{vartype}.nc"
    _file_regexp = "(?P<date>\d{8})_(?P<time>\d{2})_ecmwf_forecast\.(?P<vartype>.*)\.%s\.(?P<step>\d{3}).*\.nc$"
    _forecast_times = [36, 72, 144, 240]
    _data_organisation_table = {
        "low_cloud_area_fraction": {"sfc": "SFC"},
        "medium_cloud_area_fraction": {"sfc": "SFC"},
        "high_cloud_area_fraction": {"sfc": "SFC"},
        "air_pressure_at_sea_level": {"sfc": "SFC"},
        "surface_eastward_wind": {"sfc": "SFC"},
        "surface_northward_wind": {"sfc": "SFC"},
        "surface_air_pressure": {"sfc": "SFC"},
        "surface_temperature": {"sfc": "SFC"},
        "surface_dew_point_temperature": {"sfc": "SFC"},
        "surface_geopotential": {"sfc": "SFC"},
        "sea_ice_area_fraction": {"sfc": "SFC"},
        "atmosphere_boundary_layer_thickness": {"sfc": "SFC"},
        "solar_elevation_angle": {"sfc": "SEA"},
        "air_pressure": {"ml": "P_derived",
                         "tl": "THETA_LEVELS",
                         "pv": "PVU"},
        "geopotential_height": {"ml": "Z_derived",
                                "pl": "PRESSURE_LEVELS",
                                "pv": "PVU"},
        "air_temperature": {"ml": "T",
                            "pl": "PRESSURE_LEVELS"},
        "air_potential_temperature": {"ml": "PT_derived",
                                      "pl": "PRESSURE_LEVELS",
                                      "pv": "PVU"},
        "ertel_potential_vorticity": {"ml": "PV_derived",
                                      "pl": "PRESSURE_LEVELS",
                                      "tl": "THETA_LEVELS"},
        "equivalent_latitude": {"pl": "PRESSURE_LEVELS"},
        "specific_cloud_liquid_water_content": {"ml": "CLWC"},
        "specific_cloud_ice_water_content": {"ml": "CIWC"},
        "specific_humidity": {"ml": "Q",
                              "pl": "PRESSURE_LEVELS"},
        "mass_fraction_of_ozone_in_air": {"ml": "O3",
                                          "pl": "PRESSURE_LEVELS"},
        "mole_fraction_of_ozone_in_air": {"ml": "O3",
                                          "pl": "PRESSURE_LEVELS",
                                          "tl": "THETA_LEVELS"},
        "msg_brightness_temperature_108": {"sfc": "SFC"},
        "cloud_area_fraction_in_atmosphere_layer": {"ml": "CC"},
        "eastward_wind": {"ml": "U",
                          "pl": "PRESSURE_LEVELS"},
        "northward_wind": {"ml": "V",
                           "pl": "PRESSURE_LEVELS"},
        "omega": {"ml": "W",
                  "pl": "PRESSURE_LEVELS"},
        "divergence_of_wind": {"ml": "D",
                               "pl": "PRESSURE_LEVELS"},
        "vertically_integrated_probability_of_wcb_occurrence": {"sfc": "ProbWCB_LAGRANTO_derived"},
        "probability_of_wcb_occurrence": {"ml": "ProbWCB_LAGRANTO_derived"}
        # "vertically_integrated_probability_of_wcb_occurrence": {"sfc": ("ProbWCB_LAGRANTO_derived", "ml")}
        # "": {"": ""},
    }

    # Workaround for the numerical issue concering the lon dimension in
    # NetCDF files produced by netcdf-java 4.3..
    _mfDatasetArgsDict = {"skipDimCheck": ["lon"]}

    def __init__(self, rootpath, domain_id):
        NWPDataAccess.__init__(self, rootpath)
        self._domain_id = domain_id
        # Compile regular expression to match filenames.
        self._filename_re = re.compile(self._file_regexp % domain_id)

    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """Determines the name of the ECMWF data file the contains
           the variable <variable> of the forecast specified by
           init_time and valid_time.
        """
        variable_dict = self._data_organisation_table.get(variable, None)

        # Compute the time step in hours from the forecast valid time
        # and the initialisation time.
        fc_step = valid_time - init_time
        fc_step = fc_step.days * 24 + fc_step.seconds / 3600

        # ECMWF forecasts are stored in a series of files containing
        # different time steps. Determine into which time step interval
        # the requested valid_time falls.
        for t in self._forecast_times:
            if t >= fc_step:
                fc_step = t
                break

        # Substitute variable identifiers in the template filename.
        if variable_dict is not None and vartype not in variable_dict.keys():
            raise ValueError(u"variable type {} not available for variable {}"
                             .format(vartype, variable))

        if variable_dict is None:
            name = self._file_template.format(
                gridtype=vartype, domain_id=self._domain_id,
                fc_step=fc_step, vartype=vartype)
        elif isinstance(variable_dict[vartype], basestring):
            # The string stored for the given variable type contains the
            # variable identifier in the filename.
            name = self._file_template.format(
                gridtype=variable_dict[vartype], domain_id=self._domain_id,
                fc_step=fc_step, vartype=vartype)
        elif isinstance(variable_dict[vartype], tuple):
            # The tuple stored for the given variable type contains the
            # variable identifier and an override level identifier.
            name = self._file_template.format(
                gridtype=variable_dict[vartype][0], domain_id=self._domain_id,
                fc_step=fc_step, vartype=variable_dict[vartype][1])

        # Substitute init time and time step interval identifiers.
        name = name.replace('$', '%')
        name = datetime.strftime(init_time, name)
        return name

    def build_filetree(self):
        """Build a tree structure with information on the available
           forecast times and variables.

        The first index of 'filetree' is the forecast date/time, the second the
        timestep, the third the variable. The names of all available files are
        parsed corresponding to the above specified regular expression and
        inserted into the tree.
        """
        # Get a list of the available data files.
        available_files = os.listdir(self._root_path)

        # Build the tree structure.
        filetree = {}
        for filename in available_files:
            m = self._filename_re.match(filename)
            if m:
                # Extract information from the filename.
                # date = int(m.group(1))
                # time = int(m.group(2))
                var = m.group("vartype")
                step = int(m.group("step"))
                # dtime = int(m.group(1)+m.group(2))
                dtime = m.group("date") + m.group("time")
                dtime = datetime.strptime(dtime, "%Y%m%d%H")

                # Insert the filename into the tree.
                if dtime not in filetree.keys():
                    filetree[dtime] = {}
                if step not in filetree[dtime].keys():
                    filetree[dtime][step] = {}
                filetree[dtime][step][var] = filename

        return filetree

    def get_init_times(self):
        """Returns a list of available forecast init times (base times).
        """
        filetree = self.build_filetree()
        init_times = filetree.keys()
        init_times.sort()
        return init_times

    def get_valid_times(self, variable, vartype, init_time):
        """Returns a list of available valid times for the specified
           variable at the specified init time.
        """
        valid_times = []
        for t in self._forecast_times:
            # Open each forecast file belonging to this variable. To do this,
            # query get_filename() with a time one hour less than the upper
            # limits of the individual files.
            delta = timedelta(seconds=3600 * (t - 1))
            check_time = init_time + delta
            filename = self.get_filename(variable, vartype,
                                         init_time, check_time,
                                         fullpath=True)
            if os.path.exists(filename):
                # If the file exists, open the file and read the contained
                # times. Add the list of times to valid_times.
                cached_valid_times = self.check_valid_cache(filename)
                if cached_valid_times is not None:
                    valid_times.extend(cached_valid_times)
                else:
                    dataset = netCDF4.Dataset(filename)
                    timename, timevar = netCDF4tools.identify_CF_time(dataset)
                    times = netCDF4tools.num2date(timevar[:], timevar.units)
                    valid_times.extend(times)
                    dataset.close()
                    self.save_valid_cache(filename, times)

        return valid_times

    def get_all_valid_times(self, variable, vartype):
        """Similar to get_valid_times(), but returns the combined valid times
           of all available init times.
        """
        valid_times = set()
        filetree = self.build_filetree()
        for init_time in filetree.keys():
            vtimes = self.get_valid_times(variable, vartype, init_time)
            valid_times.update(vtimes)
        return sorted(list(valid_times))

    def get_all_datafiles(self):
        """Return a list of all available data files.
        """
        return os.listdir(self._root_path)


class CLAMSDataAccess(ECMWFDataAccess):
    """Subclass to ECMWFDataAccess for accessing CLAMS data.
    """
    _file_template = "$Y$m$d_$H_clams_forecast.{domain_id}.{fc_step:03d}.{vartype}.nc"
    _file_regexp = "(?P<date>\d{8})_(?P<time>\d{2})_clams_forecast\.%s\.(?P<step>\d{3})\.(?P<vartype>.*)\.nc$"
    _forecast_times = [144]
    _data_organisation_table = {}

    # Workaround for the numerical issue concering the lon dimension in
    # NetCDF files produced by netcdf-java 4.3..
    _mfDatasetArgsDict = {"skipDimCheck": ["lon"]}


class CLAMSICEDataAccess(ECMWFDataAccess):
    """Subclass to ECMWFDataAccess for accessing CLAMS data.
    """
    _file_template = "$Y$m$d_$H_clamsice_forecast.{domain_id}.{fc_step:03d}.{vartype}.nc"
    _file_regexp = "(?P<date>\d{8})_(?P<time>\d{2})_clamsice_forecast\.%s\.(?P<step>\d{3})\.(?P<vartype>.*)\.nc$"
    _forecast_times = [144]
    _data_organisation_table = {}

    # Workaround for the numerical issue concering the lon dimension in
    # NetCDF files produced by netcdf-java 4.3..
    _mfDatasetArgsDict = {"skipDimCheck": ["lon"]}


class GWFCDataAccess(ECMWFDataAccess):
    """Subclass to ECMWFDataAccess for accessing gravity wave forecast and related data.
    """
    _file_template = "$Y$m$d_$H_gravity_wave_forecast.{gridtype}.{domain_id}.{fc_step:03d}.{vartype}.nc"
    _file_regexp = "(?P<date>\d{8})_(?P<time>\d{2})_gravity_wave_forecast\.(?P<vartype>.*)\.%s\.(?P<step>\d{3}).*\.nc$"
    _forecast_times = range(0, 150, 6)
    _data_organisation_table = {
        "gravity_wave_temperature_perturbation": {"ml": "ALTITUDE_LEVELS"},
        "air_pressure": {"ml": "ALTITUDE_LEVELS"},
        "air_potential_temperature": {"ml": "ALTITUDE_LEVELS"},
        "brunt_vaisala_frequency_in_air": {"ml": "ALTITUDE_LEVELS"},
        "square_of_brunt_vaisala_frequency_in_air": {"ml": "ALTITUDE_LEVELS"},
        "tropopause_altitude": {"sfc": "SFC"},
        "tropopause_air_pressure": {"sfc": "SFC"},
        "max_of_square_of_brunt_vaisala_frequency_above_tropopause_in_air": {"sfc": "SFC"},
        "mean_of_square_of_brunt_vaisala_frequency_above_tropopause_in_air": {"sfc": "SFC"},
    }


class EMACDataAccess(NWPDataAccess):
    """Subclass to NWPDataAccess for accessing EMAC datasets.

    NOTE: This class is a prototype to access EMAC simulations. It may
          not be suitable for all EMAC simulations.

          The class assumes the following file structure:

          V07____________20100417_0000_ECHAM5.nc
          V07____________20100417_0000_tracer_gp.nc
          V07____________201004xx_0000_postproc.nc

          where the ECHAM5 files contain the ECHAM meteorology, the tracer_gp
          files contain the tracer data, and the postproc file contains
          postprocessed data such as total column density.

          For the first two types of file, on file per day exists. The third
          type consists of one file containing all time steps.

          All files with the same initialisation time must be placed
          in a directory named YYYYMMDD_HH, for instance,
          20100401_00. The initialisation time is obtained from the
          directory name.

          NOTE that the class assumes that all data exist for the same
          timesteps. Valid times are only determined from the tracer_gp
          files.

          (mr, 2011-03-04)
    """

    # NOTE: If the output files of different model runs are called differently,
    # add a keyword to __init__ and the regexp (as domain_id for EMCWF data).

    _file_template = "V07____________$Y$m$d_0000_%s.nc"
    _file_regexp = "V07____________(\d{8})_(\d{4})_tracer_gp.nc$"

    # If the filename structure of a variable deviates from the pattern
    # specified in _file_template, add the "replace" tuple to its
    # dictionary (e.g. in "emac_column_density").
    _data_organisation_table = {
        "air_pressure": {"ml": "ECHAM5"},
        "air_temperature": {"ml": "ECHAM5"},
        "emac_R12": {"ml": "tracer_gp"},
        "emac_column_density": {"sfc": "postproc", "replace": ("$Y$m$d", "$Y$mxx")}
        # "": {"": ""},
    }

    def __init__(self, rootpath):
        NWPDataAccess.__init__(self, rootpath)
        # Compile regular expression to match filenames.
        self._filename_re = re.compile(self._file_regexp)

    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """Determines the name of the EMAC data file the contains
           the variable <variable> of the forecast specified by
           init_time and valid_time.
        """
        variable_dict = self._data_organisation_table[variable]

        # Substitute variable identifiers in the template filename.
        if vartype not in variable_dict.keys():
            raise ValueError(u"variable type {} not available for variable {}"
                             .format(vartype, variable))

        name = self._file_template % variable_dict[vartype]
        if "replace" in variable_dict.keys():
            pattern = variable_dict["replace"]
            name = name.replace(pattern[0], pattern[1])
        name = name.replace('$', '%')
        name = valid_time.strftime(name)
        name = os.path.join(init_time.strftime("%Y%m%d_%H"), name)

        return name

    def get_init_times(self):
        """Returns a list of available forecast init times (base times).
        """
        # Get a list of the available data directories (one for each init time).
        available_data_dirs = os.listdir(self._root_path)

        init_times = []
        for d in available_data_dirs:
            try:
                dt = datetime.strptime(d, "%Y%m%d_%H")
                init_times.append(dt)
            except:
                pass

        init_times.sort()
        return init_times

    def get_valid_times(self, variable, vartype, init_time):
        """Returns a list of available valid times for the specified
           variable at the specified init time.
        """
        valid_times = []

        # Assemble data directory path.
        data_dir = os.path.join(self._root_path, init_time.strftime("%Y%m%d_%H"))

        # If the requested data directory exists, start to scan the contained
        # files.
        if os.path.exists(data_dir):
            data_files = os.listdir(data_dir)

            for filename in data_files:
                if self._filename_re.match(filename):

                    cached_valid_times = self.check_valid_cache(filename)
                    if cached_valid_times is not None:
                        valid_times.extend(cached_valid_times)
                    else:
                        dataset = netCDF4.Dataset(os.path.join(data_dir, filename))
                        timename, timevar = netCDF4tools.identify_CF_time(dataset)
                        times = netCDF4tools.num2date(timevar[:], timevar.units)
                        valid_times.extend(times)
                        dataset.close()
                        self.save_valid_cache(filename, times)

        valid_times.sort()
        return valid_times

    def get_all_valid_times(self, variable, vartype):
        """Similar to get_valid_times(), but returns the combined valid times
           of all available init times.
        """
        valid_times = set()
        for init_time in self.get_init_times():
            vtimes = self.get_valid_times(variable, vartype, init_time)
            valid_times.update(vtimes)
        valid_times = list(valid_times)
        valid_times.sort()
        return list(valid_times)

    def get_all_datafiles(self):
        """Return a list of all available data files.
        """
        files = []
        for init_time in self.get_init_times():
            data_dir = os.path.join(self._root_path,
                                    init_time.strftime("%Y%m%d_%H"))
            files.extend(os.listdir(data_dir))
        return files


class MeteosatDataAccess(NWPDataAccess):
    """Subclass to NWPDataAccess for accessing Meteosat data.

    Constructor needs information on domain ID.
    """
    _file_template = "$Y$m$d_meteosat.%s.nc"
    _file_regexp = "(\d{8})_meteosat\.%s\.nc$"

    def __init__(self, rootpath, domain_id):
        NWPDataAccess.__init__(self, rootpath)
        self._domain_id = domain_id
        # Compile regular expression to match filenames.
        self._filename_re = re.compile(self._file_regexp % domain_id)

    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """Determines the name of the Meteosat data file that contains
           the variable <variable> at time valid_time. init_time is ignored.
        """
        name = self._file_template % (self._domain_id)

        # Substitute init time and time step interval identifiers.
        name = name.replace('$', '%')
        name = datetime.strftime(valid_time, name)
        return name

    def get_init_times(self):
        """For Meteosat products, the day of the image is used as init time
           (e.g. 2013/10/10 00Z for an image at 2013/10/10 15:30).
        """
        init_times = []

        available_files = self.get_all_datafiles()

        for f in available_files:

            match = self._filename_re.match(f)

            if match:
                filename = os.path.join(self._root_path, f)
                dataset = netCDF4.Dataset(filename)
                timename, timevar = netCDF4tools.identify_CF_time(dataset)
                init_time = netCDF4tools.num2date(0, timevar.units)
                dataset.close()

                init_times.append(init_time)

        return init_times

    def get_valid_times(self, variable, vartype, init_time):
        """Returns a list of available valid times for the specified
           variable at the specified init time.
        """
        valid_times = []

        available_files = self.get_all_datafiles()

        for f in available_files:

            match = self._filename_re.match(f)

            if match:

                filename = os.path.join(self._root_path, f)

                # If the file exists, open the file and read the contained
                # times. Add the list of times to valid_times.
                cached_valid_times = self.check_valid_cache(filename)
                if cached_valid_times is not None:
                    valid_times.extend(cached_valid_times)
                else:
                    dataset = netCDF4.Dataset(filename)
                    timename, timevar = netCDF4tools.identify_CF_time(dataset)
                    times = netCDF4tools.num2date(timevar[:], timevar.units)
                    valid_times.extend(times)
                    dataset.close()
                    self.save_valid_cache(filename, times)

        return valid_times

    def get_all_valid_times(self, variable, vartype):
        """Similar to get_valid_times(), but returns the combined valid times
           of all available init times.
        """
        return self.get_valid_times(variable, vartype, None)

    def get_all_datafiles(self):
        """Return a list of all available data files.
        """
        return os.listdir(self._root_path)


class MSSChemDataAccess(NWPDataAccess):
    """Subclass to NWPDataAccess for accessing CTM data prepared by MSS-Chem

    """
    _file_template = "%s_$Y-$m-$d_%s_%s_%s.nc"
    _file_regexp = "(?P<model>.*)_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<hour>\d{2})_(?P<vartype>.*)_(?P<variable>.*)\.nc$"

    def __init__(self, rootpath, modelname, modelstr, vert):
        NWPDataAccess.__init__(self, rootpath)
        # Compile regular expression to match filenames.
        self._filename_re = re.compile(self._file_regexp)
        self._modelname = modelname
        self._modelstr = modelstr
        self._create_data_table(vert)

    def _create_data_table(self, vert):
        self._data_organisation_table = {
                stdname: {vert: shortname.lower()}
                for stdname, (shortname, _, _, _) in MSSChemTargets.items()}
        self._data_organisation_table["air_pressure"] = {vert: "p"}

    def _determine_filename(self, variable, vartype, init_time, valid_time):
        """Determines the name of the CAMS global data file that contains
           the variable <variable> of the forecast specified by
           init_time and valid_time.

        This can be simpler than usual, because MSS-Chem will prepare the data
        such that there is exactly one file per variable, vartype, and
        init_time, which contains all valid_times.

        """
        variable_dict = self._data_organisation_table[variable]

        # Substitute variable identifiers in the template filename.
        if vartype not in variable_dict.keys():
            raise ValueError("variable type %s not available for variable %s"
                             % (vartype, variable))

        if type(variable_dict[vartype]) == str:
            # The string stored for the given variable type contains the
            # variable identifier in the filename.
            name = self._file_template % (self._modelstr,
                                          "{:%H}".format(init_time), vartype,
                                          variable_dict[vartype])

        # Substitute init time and time step interval identifiers.
        name = name.replace('$', '%')
        name = datetime.strftime(init_time, name)
        return name

    def build_filetree(self):
        """Build a tree structure with information on the available
           forecast times and variables.

        The first index of 'filetree' is the forecast date/time, the second the
        timestep, the third the variable. The names of all available files are
        parsed corresponding to the above specified regular expression and
        inserted into the tree.
        """
        # Get a list of the available data files.
        available_files = self.get_all_datafiles()

        # Build the tree structure.
        filetree = {}
        for filename in available_files:
            m = self._filename_re.match(filename)
            if m:
                # Extract information from the filename.
                var = m.group("variable")
                step = 0
                initime = datetime(int(m.group("year")), int(m.group("month")),
                                   int(m.group("day")), int(m.group("hour")))

                # Insert the filename into the tree.
                if initime not in filetree.keys():
                    filetree[initime] = {}
                if step not in filetree[initime].keys():
                    filetree[initime][step] = {}
                filetree[initime][step][var] = filename

        return filetree

    def get_init_times(self):
        """Returns a list of available forecast init times (base times).
        """
        filetree = self.build_filetree()
        init_times = filetree.keys()
        init_times.sort()
        return init_times

    def get_valid_times(self, variable, vartype, init_time):
        """Returns a list of available valid times for the specified
           variable at the specified init time.
        """
        valid_times = []
        # Open the forecast file belonging to this variable.
        filename = self.get_filename(variable, vartype, init_time, None,
                                     fullpath=True)
        if os.path.exists(filename):
            # If the file exists, open the file and read the contained
            # times. Add the list of times to valid_times.
            cached_valid_times = self.check_valid_cache(filename)
            if cached_valid_times is not None:
                valid_times.extend(cached_valid_times)
            else:
                dataset = netCDF4.Dataset(filename)
                timename, timevar = netCDF4tools.identify_CF_time(dataset)
                times = netCDF4tools.num2date(timevar[:], timevar.units)
                valid_times.extend(times)
                dataset.close()
                self.save_valid_cache(filename, times)

        return valid_times

    def get_all_valid_times(self, variable, vartype):
        """Similar to get_valid_times(), but returns the combined valid times
           of all available init times.
        """
        valid_times = set()
        filetree = self.build_filetree()
        for init_time in filetree.keys():
            vtimes = self.get_valid_times(variable, vartype, init_time)
            valid_times.update(vtimes)
        return sorted(list(valid_times))

    def get_all_datafiles(self):
        """Return a list of all available data files.
        """
        return [os.path.basename(fn) for fn
                in glob.glob(os.path.join(self._root_path, "*", "*.nc"))]

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
            return os.path.join(self._root_path,
                                "{:%Y-%m-%d_%H}".format(init_time), filename)
        else:
            return filename
