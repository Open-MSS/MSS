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
import re

# related third party imports
import netCDF4


class NetCDFVariableError(Exception):
    """Exception class to handle error concerning NetCDF variables.
    """
    pass


NO_FIELDS = 1

CHECK_NONE = 512
CHECK_LATLON = 1024
CHECK_LATLONHYB = 2048

# Regular expression to match a time units string of format
# "2010-02-01T00:00:00Z" (as used by netcdf-java).
re_datetime = re.compile("(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})Z")
# Expression used to identify the time variable by its units string.
re_timeunits = re.compile("\w+ since \d{4}-\d{1,2}-\d{1,2}.\d{1,2}")


# NETCDF FILE TOOLS


def identify_variable(ncfile, standard_name, check=False):
    """
    Identify the variable in ncfile that is described by specified rules.

    Arguments:
    ncfile -- Handle to open netCDF4.Dataset().

    check (default False) -- Throw an exception if variable has not been
                             found. If False, return None.

    """

    for var_name, variable in ncfile.variables.items():
        if "standard_name" in variable.ncattrs() and variable.standard_name == standard_name:
            return var_name, variable
    if check:
        raise NetCDFVariableError(u"cannot identify NetCDF variable "
                                  u"specified by <{}>".format(standard_name))
    return None, None


def identify_CF_coordhybrid(ncfile, check=CHECK_NONE):
    """
    Identify variables representing longitude, latitude, hybrid model levels
    in ECMWF files.


    Returns:
    lon_name, lon_var, lat_name, lat_var, hybrid_name, hybrid_var
    """
    lon_name, lon_var = identify_variable(ncfile, "longitude")
    lat_name, lat_var = identify_variable(ncfile, "latitude")
    hybrid_name, hybrid_var = identify_variable(ncfile, "atmosphere_hybrid_sigma_pressure_coordinate")

    if check == CHECK_LATLON:
        if not (lat_var and lon_var):
            raise NetCDFVariableError("Cannot identify lat/lon coordinate system "
                                      "in NetCDF-CF input.")
    elif check == CHECK_LATLONHYB:
        if not (lat_var and lon_var and hybrid_var):
            raise NetCDFVariableError("Cannot identify lat/lon/hybrid coordinate system "
                                      "in NetCDF-CF input.")

    return lat_name, lat_var, lon_name, lon_var, hybrid_name, hybrid_var


def hybrid_orientation(hybrid_var):
    """
    Returns -1 if orientation of hybrid_var is down (largest value first),
    otherwise 1.
    """
    hybrid_levels = hybrid_var[:]
    if hybrid_levels[0] > hybrid_levels[-1]:
        # Vertical axis INDEX orientation is down (largest value is the first,
        # for ECMWF data this is level closest to the surface).
        return -1
    else:
        # Vertical axis INDEX orientation is up (smallest value is the first,
        # for ECMWF data this level is the uppermost).
        return 1


def identify_CF_hybrid(ncfile):
    """
    Identify the vertical variable from a CF-compliant NetCDF file.

    Returns: hybrid_name, hybrid_var, hybrid_orientation
    """
    hybrid_name, hybrid_var = identify_variable(ncfile, "atmosphere_hybrid_sigma_pressure_coordinate")

    orientation = None
    if hybrid_var:
        orientation = hybrid_orientation(hybrid_var)
    return hybrid_name, hybrid_var, orientation


def identify_CF_isopressure(ncfile):
    """
    Identify the vertical variable from a CF-compliant NetCDF file.

    Returns: isopressure_name, isopressure_var, isopressure_orientation
    """

    isopressure_name, isopressure_var = identify_variable(ncfile, "atmosphere_pressure_coordinate")

    orientation = None
    if isopressure_var:
        orientation = hybrid_orientation(isopressure_var)
    return isopressure_name, isopressure_var, orientation


def identify_CF_isopotvort(ncfile, isopotvortname_override=None):
    """
    Identify the vertical variable from a CF-compliant NetCDF file.

    Returns: isopotvort_name, isopotvort_var, isopotvort_orientation
    """
    isopotvort_name, isopotvort_var = identify_variable(ncfile, "atmosphere_ertel_potential_vorticity_coordinate")

    orientation = None
    if isopotvort_var:
        orientation = hybrid_orientation(isopotvort_var)
    return isopotvort_name, isopotvort_var, orientation


def identify_CF_isoaltitude(ncfile):
    """
    Identify the vertical variable from a CF-compliant NetCDF file.

    Returns: isoaltitude_name, isoaltiude_var, isoalttiude_orientation
    """
    isoaltitude_name, isoaltitude_var = identify_variable(ncfile, "atmosphere_altitude_coordinate")
    orientation = None
    if isoaltitude_var:
        orientation = hybrid_orientation(isoaltitude_var)
    return isoaltitude_name, isoaltitude_var, orientation


def identify_CF_isopottemp(ncfile):
    """
    Identify the vertical variable from a CF-compliant NetCDF file.

    Returns: isoaltitude_name, isoaltiude_var, isoalttiude_orientation
    """
    isopottemp_name, isopottemp_var = identify_variable(ncfile, "atmosphere_potential_temperature_coordinate")

    orientation = None
    if isopottemp_var:
        orientation = hybrid_orientation(isopottemp_var)
    return isopottemp_name, isopottemp_var, orientation


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


def identify_CF_ensemble(ncfile, ensname_override=None):
    """
    Identify the ensemble dimension from a CF-compliant NetCDF file.

    Returns: ens_name, ens_var
    """
    ens_name, ens_var = identify_variable(ncfile, "ensemble")

    if ens_name not in ncfile.dimensions:
        # Make sure that the found variable is a dimension variable.
        return None, None
    else:
        return ens_name, ens_var


def num2date(times, units, calendar='standard'):
    """
    Extension to the netCDF4.num2date() function to correctly handle
    time strings of format '2010-01-01T00:00:00Z', as used by netcdf-java.

    Simply replaces an occurence of '2010-01-01T00:00:00Z' in units by
    '2010-01-01 00:00:00 0:00', which is the CF-compliant format.

    Refer to netCDF4.num2date() for further documentation.
    """
    # Replace any "2010-01-01T00:00:00Z" string by "2010-01-01 00:00:00 0:00"
    # (cut the 'T' and replace 'Z' by 0:00; cf. CF-conventions document).
    units_new = re_datetime.sub(r'\1-\2-\3 \4:\5:\6 0:00', units)
    return netCDF4.num2date(times, units_new, calendar=calendar)


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
    lat_name, lat_var, lon_name, lon_var, hybrid_name, hybrid_var = \
        identify_CF_coordhybrid(ncfile)

    # Get lat and lon data. NOTE that MARS stores longitude from 0 to 360,
    # more common is the range -180 to 180. Hence shift ECMWF longitude
    # to -180..180. Latitude data is by default reversed if it is stored
    # in decreasing order, to make it strictly increasing (needed for the
    # interpolation routine below).
    lat_order = 1
    if lat_var is None:
        raise ValueError("Cannot determine latitude variable")
    lat_data = lat_var[:]
    if lat_data[0] > lat_data[1]:
        if autoreverse:
            lat_data = lat_data[::-1]
        lat_order = -1

    # If longitudes are already stored in -180..180 the transformation won't
    # change anything.
    if lon_var is None:
        raise ValueError("Cannot determine longitude variable")
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

    def __init__(self, files, exclude=[], skipDimCheck=[],
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
        if isinstance(files, str):
            files = sorted(glob.glob(files))

        master = files[0]

        # Open the master again, this time as a classic CDF instance. This will avoid
        # calling methods of the CDFMF subclass when querying the master file.
        cdfm = netCDF4.Dataset(master)
        # copy attributes from master.
        self.__dict__.update(cdfm.__dict__)


        # Get names of master dimensions.
        masterDims = cdfm.dimensions.keys()

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# The following methods are inherited from MFDataset:

#     def __setattr__(self, name, value):
#         """override base class attribute creation"""
#         self.__dict__[name] = value

#     def __getattribute__(self, name):
#         if name in ['variables','dimensions','file_format']:
#             if name == 'dimensions': return self._dims
#             if name == 'variables': return self._vars
#             if name == 'file_format': return self._file_format
#         else:
#             return netCDF4.Dataset.__getattribute__(self, name)

#     def ncattrs(self):
#         return self._cdf[0].__dict__.keys()

#     def close(self):
#         for dset in self._cdf:
#             dset.close()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
