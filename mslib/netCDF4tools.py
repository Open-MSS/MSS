# -*- coding: utf-8 -*-
"""

    mslib.netCDF4tools
    ~~~~~~~~~~~~~~~~~~

    Some useful functions for handling NetCDF files with the netCDF4 library.

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

import glob
import netCDF4


VERTICAL_AXIS = {
    "al": "atmosphere_altitude_coordinate",
    "ml": "atmosphere_hybrid_sigma_pressure_coordinate",
    "pl": "atmosphere_pressure_coordinate",
    "pv": "atmosphere_ertel_potential_vorticity_coordinate",
    "tl": "atmosphere_potential_temperature_coordinate",
}

# NETCDF FILE TOOLS


def identify_variable(ncfile, standard_names, check=False):
    """
    Identify the variable in ncfile that is described by specified rules.

    Arguments:
    ncfile -- Handle to open netCDF4.Dataset().

    check (default False) -- Throw an exception if variable has not been
                             found. If False, return None.

    """
    if not isinstance(standard_names, list):
        standard_names = [standard_names]

    for var_name, variable in ncfile.variables.items():
        if "standard_name" in variable.ncattrs() and variable.standard_name in standard_names:
            return var_name, variable
    if check:
        raise IOError(u"cannot identify NetCDF variable "
                      u"specified by {}".format(standard_names))
    return None, None


def identify_CF_lonlat(ncfile):
    """
    Identify variables representing longitude, latitude, hybrid model levels
    in ECMWF files.


    Returns:
    lat_name, lat_var, lon_name, lon_var
    """
    lat_name, lat_var = identify_variable(ncfile, ["latitude", "latitude_north"], check=True)
    lon_name, lon_var = identify_variable(ncfile, ["longitude", "longitude_east"], check=True)

    return lat_name, lat_var, lon_name, lon_var


def hybrid_orientation(hybrid_var):
    """
    Returns -1 if orientation of hybrid_var is down (largest value first),
    otherwise 1.
    """
    if hybrid_var is None:
        return None
    hybrid_levels = hybrid_var[:]
    if hybrid_levels[0] > hybrid_levels[-1]:
        # Vertical axis INDEX orientation is down (largest value is the first,
        # for ECMWF data this is level closest to the surface).
        return -1
    else:
        # Vertical axis INDEX orientation is up (smallest value is the first,
        # for ECMWF data this level is the uppermost).
        return 1


def identify_vertical_axis(dataset):
    """
    Try to load vertical hybrid coordinate (model levels), isopressure
    coordinate (pressure levels) or iso-potential-vorticity (pv levels).
    NOTE: This code assumes that a file contains data on exactly one level
    type, not on more that one!
    """

    result = []
    for layertype, standard_name in VERTICAL_AXIS.items():
        name, var = identify_variable(dataset, standard_name)
        orientation = hybrid_orientation(var)
        if var is not None:
            units = getattr(var, "units", "unknown units")
            result.append((name, var, orientation, units, layertype))
    if len(result) == 0:
        return None, None, None, None, "sfc"
    if len(result) > 1:
        raise IOError("Identified more than one vertical axis: {}".format(result))
    return result[0]


def identify_CF_time(ncfile):
    """
    Identify the time variable from a CF-compliant NetCDF file.

    From the CF-conventions document: 'A time coordinate is identifiable
    from its units string alone'. This method tries to match identify the
    units string of the file variables.

    THE FIRST TIME DIMENSION THAT IS FOUND IS RETURNED.

    Returns: time_name, time_var
    """
    time_name, time_var = identify_variable(ncfile, "time", check=True)
    return time_name, time_var


def num2date(times, units, calendar='standard'):
    """
    Extension to the netCDF4.num2date() function to correctly handle
    time strings of format '2010-01-01T00:00:00Z', as used by netcdf-java.

    Refer to netCDF4.num2date() for further documentation.
    """
    return netCDF4.num2date(times, units, calendar=calendar)


def get_latlon_data(ncfile, autoreverse=True):
    """
    Get data arrays of latitude and longitude in a NetCDF file.

    ncfile needs to be an open netCDF4.Dataset.

    Returns: lat_data, lon_data, lat_order

    If lat_data is stored in decreasing order and autoreverse is True, it is
    reversed and returned in increasing order. The return argument lat_order
    will be -1 in this case (otherwise 1), so it can be used to automatically
    reverse record variables (e.g. temperature[:,:,::lat_order,:]).
    """
    # Get coordinate dimensions.
    lat_name, lat_var, lon_name, lon_var = identify_CF_lonlat(ncfile)

    # Get lat and lon data. NOTE that MARS stores longitude from 0 to 360,
    # more common is the range -180 to 180. Hence shift ECMWF longitude
    # to -180..180. Latitude data is by default reversed if it is stored
    # in decreasing order, to make it strictly increasing (needed for the
    # interpolation routine below).
    lat_order = 1
    lat_data = lat_var[:]
    if lat_data[0] > lat_data[1] and autoreverse:
        lat_data = lat_data[::-1]
        lat_order = -1

    # If longitudes are already stored in -180..180 the transformation won't
    # change anything.
    lon_data = ((lon_var[:] + 180) % 360) - 180

    return lat_data, lon_data, lat_order


class MFDatasetCommonDims(netCDF4.MFDataset):
    """MFDatasetCommonDims(self, files, exclude=[], requireDimNum=False)

    Class for reading multi-file netCDF Datasets with common dimensions,
    making variables in different files appear as if they were in one file.

    Datasets must be in C{NETCDF4_CLASSIC, NETCDF3_CLASSIC or NETCDF3_64BIT}
    format (C{NETCDF4} Datasets won't work).

    Inherits MFDataset from the U{netcdf4-python
    <http://netcdf4-python.googlecode.com/>} library by Jeffrey Whitaker.
    """

    def __init__(self, files, exclude=None, skipDimCheck=None,
                 requireDimNum=False):
        """
        Open a Dataset spanning multiple files sharing common dimensions but
        containing different record variables, making it look as if it was a
        single file.

        Inherits MFDataset from the U{netcdf4-python
        <http://netcdf4-python.googlecode.com/>} library by Jeffrey Whitaker.

        Usage:

        nc = MFDatasetCommonDims(files, exclude=[], skipDimCheck=[],
                                 requireDimNum=False)

        @param files: either a sequence of netCDF files or a string with a
        wildcard (converted to a sorted list of files using glob)  The first file
        in the list will become the 'master' file, defining all the record
        variables (variables with an unlimited dimension) which may span
        subsequent files. Attribute access returns attributes only from 'master'
        file. The files are always opened in read-only mode.

        NOTE: Files may contain only a subset of the dimensions contained in
        the 'master' file (e.g. a file with only surface and no upper air
        fields). They may *not* contain any other dimension as the master.
        Exactly the same dimensions in every file can be forced by setting
        requireDimNum to True.

        @param exclude: A list of variable names to exclude from aggregation.
        Default is an empty list.
        @param skipDimCheck: Only use this parameter if you know what you are
        doing. Each dimension in this list of dimension names is not checked
        against the master dimension. Use this parameter as a workaround for
        numerical inaccuracies when opening NetCDF files converted from mixed
        GRIB1/2 files. (mr 03Aug2012)
        @param requireDimNum: see above.
        """
        # Open the master file in the base class, so that the CDFMF instance
        # can be used like a CDF instance.

        exclude = exclude or []
        skipDimCheck = skipDimCheck or []
        if isinstance(files, str):
            files = sorted(glob.glob(files))

        master = files[0]

        # Open the master again, this time as a classic CDF instance. This will avoid
        # calling methods of the CDFMF subclass when querying the master file.
        cdfm = netCDF4.Dataset(master)
        # copy attributes from master.
        self.__dict__.update(cdfm.__dict__)

        # Get names of master dimensions.
        masterDims = list(cdfm.dimensions.keys())
        # Check that each dimension has a coordinate dimension
        for dimName in masterDims:
            if dimName not in cdfm.variables:
                raise IOError(u"dimension '{}' has no coordinate variable in master '{}'".format(dimName, master))

        # Create the following:
        #   cdf       list of Dataset instances
        #   cdfVar    dictionnary indexed by the variable names
        cdf = [cdfm]
        self._cdf = cdf  # Store this now, because dim() method needs it
        cdfVar = {}
        cdfOrigin = {}
        for vName, v in cdfm.variables.items():
            if vName in exclude:
                continue
            cdfVar[vName] = v
            cdfOrigin[vName] = (master, cdfm)
        if len(cdfVar) == 0:
            raise IOError(u"master dataset '{}' does not have any variable".format(master))

        # Open each remaining file in read-only mode.
        # Make sure each file defines the same record variables as the master
        # and that the variables are defined in the same way (name, shape and type)
        for f in files[1:]:
            part = netCDF4.Dataset(f)
            # Make sure dimension of new dataset are contained in the master.
            for dimName in part.dimensions:
                # (..except those that shall not be tested..)
                if dimName not in skipDimCheck:
                    if dimName not in masterDims:
                        raise IOError(u"dimension '{}' not defined in master '{}'".format(dimName, master))
                    if dimName not in part.variables:
                        raise IOError(u"dimension '{}' has no coordinate variable in file '{}'".format(dimName, f))
                    if len(part.dimensions[dimName]) != len(cdfm.dimensions[dimName]) or \
                            (part.variables[dimName][:] != cdfm.variables[dimName][:]).any():
                        raise IOError(u"dimension '{}' differs in master '{}' and "
                                      u"file '{}'".format(dimName, master, f))

            if requireDimNum:
                if len(part.dimensions) != len(masterDims):
                    raise IOError(u"number of dimensions not consistent in master "
                                  u"'{}' and '{}'".format(master, f))

            for vName, v in part.variables.items():
                # Exclude dimension variables.
                if (vName in exclude) or (vName in masterDims):
                    continue
                cdfVar[vName] = v
                cdfOrigin[vName] = (f, part)

            cdf.append(part)

        # Attach attributes to the MFDataset instance.
        # A local __setattr__() method is required for them.
        self._files = files  # list of cdf file names in the set
        self._dims = cdfm.dimensions
        self._vars = cdfVar
        self._cdfOrigin = cdfOrigin

        self._file_format = []
        for dset in self._cdf:
            if dset.file_format == "NETCDF4":
                raise ValueError("MFNetCDF4 only works with NETCDF3_CLASSIC, "
                                 "NETCDF3_64BIT and NETCDF4_CLASSIC "
                                 "formatted files, not NETCDF4")
            self._file_format.append(dset.file_format)

    def getOriginFile(self, varname):
        """Returns filename and NetCDF4.Dataset-instance of the file that
           contains <varname>.
        """
        return self._cdfOrigin[varname]
