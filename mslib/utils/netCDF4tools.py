# -*- coding: utf-8 -*-
"""

    mslib.utils.netCDF4tools
    ~~~~~~~~~~~~~~~~~~

    Some useful functions for handling NetCDF files with the xarray library.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import numpy as np
import netCDF4
import xarray as xr


VERTICAL_AXIS = {
    "al": "atmosphere_altitude_coordinate",
    "ml": "atmosphere_hybrid_sigma_pressure_coordinate",
    "pl": "atmosphere_pressure_coordinate",
    "pv": "atmosphere_ertel_potential_vorticity_coordinate",
    "tl": "atmosphere_potential_temperature_coordinate",
    "fl": "flight_level_coordinate",
}

# NETCDF FILE TOOLS


def identify_variable(ncfile, standard_names, check=False):
    """
    Identify the variable in ncfile that is described by specified rules.

    Arguments:
    ncfile -- Handle to an open xarray.Dataset().

    check (default False) -- Throw an exception if variable has not been
                             found. If False, return None.

    Returns: var_name, variable (as xarray.DataArray)
    """
    if not isinstance(standard_names, list):
        standard_names = [standard_names]

    for var_name, variable in ncfile.variables.items():
        if variable.attrs.get("standard_name") in standard_names:
            return var_name, ncfile[var_name]
    if check:
        raise IOError("cannot identify NetCDF variable "
                      f"specified by {standard_names}")
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
    hybrid_levels = np.asarray(hybrid_var)
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
            units = var.attrs.get("units", "dimensionless")
            result.append((name, var, orientation, units, layertype))
    if len(result) == 0:
        return None, None, None, None, "sfc"
    if len(result) > 1:
        raise IOError(f"Identified more than one vertical axis: {result}")
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
    # Patch to address the problem of netCDF4.num2date not being able
    # to handle masked array without a mask.
    if hasattr(times, "mask") and times.mask is np.ma.nomask:
        times = times.data
    return netCDF4.num2date(times, units, calendar=calendar)


def get_latlon_data(ncfile, autoreverse=True):
    """
    Get data arrays of latitude and longitude in a NetCDF file.

    ncfile needs to be an open xarray.Dataset.

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
    lat_data = np.asarray(lat_var)
    if lat_data[0] > lat_data[1] and autoreverse:
        lat_data = lat_data[::-1]
        lat_order = -1

    # If longitudes are already stored in -180..180 the transformation won't
    # change anything. It is done in double precision, as a modulo on single
    # precision longitudes would lose accuracy.
    lon_data = ((np.asarray(lon_var, dtype=np.float64) + 180) % 360) - 180

    return lat_data, lon_data, lat_order


def open_mfdataset_commondims(files, skip_dim_check=None):
    """
    Open several NetCDF files that share common dimensions as a single dataset,
    making the variables of all files appear as if they were in one file.

    Arguments:
    files -- either a sequence of NetCDF files or a string with a wildcard
    (converted to a sorted list of files using glob). The files are opened in
    read-only mode. The first file in the list acts as the 'master' file: global
    attributes, coordinate variables and, in case a variable is present in
    several files, the variable data are taken from it.

    skip_dim_check -- Only use this parameter if you know what you are doing.
    The dimensions in this list of dimension names are not compared between the
    files; everything depending on them is taken from the 'master' file only.
    Use this parameter as a workaround for numerical inaccuracies when opening
    NetCDF files converted from mixed GRIB1/2 files. (mr 03Aug2012)

    Returns an xarray.Dataset. The files are only read when the data is
    accessed; closing the returned dataset closes all of them.

    The dimensions of the files need to agree, but they may contain different
    subsets of the dimensions (e.g. a file with only surface and no upper air
    fields), and dimensions without a coordinate variable are only checked for
    their length. Note that this does not concatenate along any dimension; use
    xarray.open_mfdataset() (which requires dask) for that.
    """
    skip_dim_check = set(skip_dim_check or [])
    if isinstance(files, str):
        files = sorted(glob.glob(files))
    if len(files) == 0:
        raise IOError("no NetCDF files to open")

    datasets = []

    def close_all():
        for opened in datasets:
            opened.close()

    try:
        for _file in files:
            datasets.append(xr.open_dataset(_file, decode_times=False))
        # Dimensions excluded from the consistency check may differ between the
        # files, so all variables depending on them are taken from the master.
        to_merge = [datasets[0]] + [
            dataset.drop_vars([name for name, variable in dataset.variables.items()
                               if not skip_dim_check.isdisjoint(variable.dims)])
            for dataset in datasets[1:]]
        dataset = xr.merge(to_merge, join="exact", compat="override",
                           combine_attrs="override")
    except xr.AlignmentError as ex:
        close_all()
        raise IOError(f"dimensions of the files {files} do not match: {ex}") from ex
    except Exception:
        close_all()
        raise

    dataset.set_close(close_all)
    return dataset
