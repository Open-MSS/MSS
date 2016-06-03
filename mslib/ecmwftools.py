"""This module provides functions to process ECMWF forecast data.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus

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

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# related third party imports
import numpy

"""
EXCEPTION CLASSES
"""


class ECMWFInvalidNetCDFVariableError(Exception):
    """Exception class to handle invalid or non-CF-compliant NetCDF variables.
    """
    pass


class ECMWFMissingValueError(Exception):
    """Exception class to handle missing values in an ECMWF field.
    """
    pass


"""
Pressure on model levels

The pressure on ECMWF model levels can be computed from the surface
pressure field.

The underlying equation is p_k = a_k + b_k * p_surface

References:
  http://www.ecmwf.int/products/data/technical/model_levels/model_def_91.html
  and
  Section 2.2.1 of the IFS Documentation Cy31r1 Part III: Dynamics and
  Numerical Procedures.

Define coefficients a_k and b_k for what is called "half-levels" in the IFS
documentation. These values can be found on the webpage listed above.
NOTE that they are in reverse order, i.e. the first coefficient here
corresponds to the bottom layer.
"""
# Coefficients for 91 model levels. The following values for ak and bk have been
# taken from
# http://www.ecmwf.int/products/data/technical/model_levels/model_def_91.html
# NOTE: The ak coefficients are defined in [hPa]!

ak_halflevel_91 = numpy.array([
    0.003160, 6.575628, 54.208336, 162.043427, 336.772369,
    576.314148, 895.193542, 1297.656128, 1784.854614, 2356.202637,
    3010.146973, 3743.464355, 4550.215820, 5422.802734, 6353.920898,
    7335.164551, 8356.252930, 9405.222656, 10471.310547, 11543.166992,
    12608.383789, 13653.219727, 14665.645508, 15633.566406, 16544.585938,
    17385.595703, 18141.296875, 18798.822266, 19348.775391, 19785.357422,
    20107.031250, 20319.011719, 20426.218750, 20434.158203, 20348.916016,
    20175.394531, 19919.796875, 19587.513672, 19184.544922, 18716.968750,
    18191.029297, 17613.281250, 16990.623047, 16329.560547, 15638.053711,
    14922.685547, 14192.009766, 13453.225586, 12713.897461, 11982.662109,
    11262.484375, 10558.881836, 9873.560547, 9208.305664, 8564.624023,
    7942.926270, 7341.469727, 6759.727051, 6199.839355, 5663.156250,
    5150.859863, 4663.776367, 4202.416504, 3767.196045, 3358.425781,
    2976.302246, 2620.898438, 2292.155518, 1989.874390, 1713.709595,
    1463.163940, 1237.585449, 1036.166504, 857.945801, 701.813354,
    566.519226, 450.685791, 352.824493, 271.356506, 204.637451,
    150.986023, 108.715561, 76.167656, 51.746601, 33.952858,
    21.413612, 12.908319, 7.387186, 3.980832, 2.000040,
    0.000000
]) / 100.  # convert from Pa to hPa

bk_halflevel_91 = numpy.array([
    0.997630, 0.994204, 0.989153, 0.982238, 0.973466,
    0.963007, 0.950274, 0.935157, 0.917651, 0.897767,
    0.875518, 0.850950, 0.824185, 0.795385, 0.764679,
    0.732224, 0.698224, 0.662934, 0.626559, 0.589317,
    0.551458, 0.513280, 0.475016, 0.436906, 0.399205,
    0.362203, 0.326329, 0.291993, 0.259554, 0.229315,
    0.201520, 0.176091, 0.152934, 0.131935, 0.112979,
    0.095964, 0.080777, 0.067316, 0.055474, 0.045146,
    0.036227, 0.028610, 0.022189, 0.016860, 0.012508,
    0.009035, 0.006322, 0.004267, 0.002765, 0.001701,
    0.001000, 0.000548, 0.000279, 0.000131, 0.000055,
    0.000014, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000
])


# Define interpolated coefficients a_k and b_k for what is called "full-levels"
# in the IFS documentation. These values cannot be found on the ECMWF pages,
# they are computed with the following function.
# (ak_fulllevel[i] = ak_halflevel[i-1] + (ak_half[i]-ak_half[i-1])/2.)
def compute_full_level_akbk(numlevel, ak_half, bk_half):
    """Compute full level coefficients from half level coefficients. Pass the
       number of levels and the corresponding half level coefficients as numpy
       arrays.
    """
    ak_half2 = numpy.zeros(numlevel + 1)
    ak_half2[1:] = ak_half
    bk_half2 = numpy.ones(numlevel + 1)
    bk_half2[1:] = bk_half
    ak_full = ak_half2[:numlevel] + (ak_half2[1:] - ak_half2[:numlevel]) / 2.
    bk_full = bk_half2[:numlevel] + (bk_half2[1:] - bk_half2[:numlevel]) / 2.
    return ak_full, bk_full


ak_fulllevel_91, bk_fulllevel_91 = \
    compute_full_level_akbk(91, ak_halflevel_91, bk_halflevel_91)

# Coefficients for 62 model levels. The following values for ak and bk have been
# taken from
# http://www.ecmwf.int/products/data/technical/model_levels/model_def_62.html
# NOTE: The ak coefficients are defined in [hPa]!
ak_halflevel_62 = numpy.array([
    0.003160, 6.575628, 54.208336, 162.043427, 336.772369,
    576.314148, 895.193542, 1297.656128, 1784.854614, 2356.202637,
    3010.146973, 3743.464355, 4550.215820, 5422.802734, 6353.920898,
    7335.164551, 8356.252930, 9405.222656, 10471.310547, 11543.166992,
    12608.383789, 13653.219727, 14665.645508, 15633.566406, 16544.585938,
    17385.595703, 18141.296875, 18798.822266, 19348.775391, 19785.357422,
    20107.031250, 20319.011719, 20426.218750, 20434.158203, 20348.916016,
    20175.394531, 19919.796875, 19587.513672, 19184.544922, 18716.968750,
    18191.029297, 17613.281250, 16990.623047, 16329.560547, 15638.053711,
    14922.685547, 14192.009766, 13419.463867, 12595.006836, 11722.749023,
    10807.783203, 9860.528320, 8890.707031, 7909.441406, 6921.870117,
    5933.037598, 4944.197266, 3955.356934, 2966.516602, 1977.676270,
    988.835876, 0.000000
]) / 100.  # convert from Pa to hPa

bk_halflevel_62 = numpy.array([
    0.997630, 0.994204, 0.989153, 0.982238, 0.973466,
    0.963007, 0.950274, 0.935157, 0.917651, 0.897767,
    0.875518, 0.850950, 0.824185, 0.795385, 0.764679,
    0.732224, 0.698224, 0.662934, 0.626559, 0.589317,
    0.551458, 0.513280, 0.475016, 0.436906, 0.399205,
    0.362203, 0.326329, 0.291993, 0.259554, 0.229315,
    0.201520, 0.176091, 0.152934, 0.131935, 0.112979,
    0.095964, 0.080777, 0.067316, 0.055474, 0.045146,
    0.036227, 0.028610, 0.022189, 0.016860, 0.012508,
    0.009035, 0.006322, 0.004187, 0.002565, 0.001415,
    0.000685, 0.000275, 0.000087, 0.000013, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000
])

ak_fulllevel_62, bk_fulllevel_62 = \
    compute_full_level_akbk(62, ak_halflevel_62, bk_halflevel_62)

# Coefficients for 31 model levels. The following values for ak and bk have been
# taken from
# http://www.ecmwf.int/products/data/technical/model_levels/model_def_31.html
# NOTE: The ak coefficients are defined in [hPa]!
ak_halflevel_31 = numpy.array([
    0.000000, 0.000000, 72.063577, 271.626545, 638.148911,
    1195.889791, 1954.805296, 2911.569385, 4050.717678, 5345.914240,
    6761.341326, 8253.212096, 9771.406290, 11261.228878, 12665.291662,
    13925.517858, 14985.269630, 15791.598604, 16297.619332, 16465.005734,
    16266.610500, 15689.207458, 14736.356909, 13431.393926, 11820.539617,
    9976.135361, 8000.000000, 6000.000000, 4000.000000, 2000.000000,
    0.000000
]) / 100.  # convert from Pa to hPa

bk_halflevel_31 = numpy.array([
    0.9922814815, 0.9729851852, 0.9442132326, 0.9077158297, 0.8649558510,
    0.8171669567, 0.7654052430, 0.7105944258, 0.6535645569, 0.5950842740,
    0.5358865832, 0.4766881754, 0.4182022749, 0.3611450218, 0.3062353873,
    0.2541886223, 0.2057032385, 0.1614415235, 0.1220035886, 0.0878949492,
    0.0594876397, 0.0369748598, 0.0203191555, 0.0091941320, 0.0029197006,
    0.0003908582, 0.0000000000, 0.0000000000, 0.0000000000, 0.0000000000,
    0.0000000000
])

ak_fulllevel_31, bk_fulllevel_31 = \
    compute_full_level_akbk(31, ak_halflevel_31, bk_halflevel_31)

# Coefficients for 137 model levels. The following values for ak and bk have been
# taken from
# http://www.ecmwf.int/products/data/technical/model_levels/model_def_137.html
# NOTE: The ak coefficients are defined in [hPa]!
ak_halflevel_137 = numpy.array([
    0.0, 3.757813, 22.835938, 62.78125, 122.101562,
    202.484375, 302.476562, 424.414062, 568.0625, 734.992188,
    926.507812, 1143.25, 1387.546875, 1659.476562, 1961.5,
    2294.242188, 2659.140625, 3057.265625, 3489.234375, 3955.960938,
    4457.375, 4993.796875, 5564.382812, 6168.53125, 6804.421875,
    7470.34375, 8163.375, 8880.453125, 9617.515625, 10370.175781,
    11133.304688, 11901.339844, 12668.257812, 13427.769531, 14173.324219,
    14898.453125, 15596.695312, 16262.046875, 16888.6875, 17471.839844,
    18006.925781, 18489.707031, 18917.460938, 19290.226562, 19608.572266,
    19874.025391, 20087.085938, 20249.511719, 20361.816406, 20425.71875,
    20442.078125, 20412.308594, 20337.863281, 20219.664062, 20059.931641,
    19859.390625, 19620.042969, 19343.511719, 19031.289062, 18685.71875,
    18308.433594, 17901.621094, 17467.613281, 17008.789062, 16527.322266,
    16026.115234, 15508.256836, 14975.615234, 14432.139648, 13881.331055,
    13324.668945, 12766.873047, 12211.547852, 11660.067383, 11116.662109,
    10584.631836, 10065.978516, 9562.682617, 9076.400391, 8608.525391,
    8159.354004, 7727.412109, 7311.869141, 6911.870605, 6526.946777,
    6156.074219, 5798.344727, 5452.990723, 5119.89502, 4799.149414,
    4490.817383, 4194.930664, 3911.490479, 3640.468262, 3381.743652,
    3135.119385, 2900.391357, 2677.348145, 2465.770508, 2265.431641,
    2076.095947, 1897.519287, 1729.448975, 1571.622925, 1423.770142,
    1285.610352, 1156.853638, 1037.201172, 926.34491, 823.967834,
    729.744141, 643.339905, 564.413452, 492.616028, 427.592499,
    368.982361, 316.420746, 269.539581, 227.968948, 191.338562,
    159.279404, 131.425507, 107.415741, 86.895882, 69.520576,
    54.955463, 42.879242, 32.98571, 24.985718, 18.608931,
    13.605424, 9.746966, 6.827977, 4.666084, 3.102241,
    2.000365, 0.0
]) / 100.  # convert from Pa to hPa

bk_halflevel_137 = numpy.array([
    0.99763, 0.995003, 0.991984, 0.9885, 0.984542,
    0.980072, 0.975078, 0.969513, 0.963352, 0.95655,
    0.949064, 0.94086, 0.931881, 0.922096, 0.911448,
    0.8999, 0.887408, 0.873929, 0.859432, 0.843881,
    0.827256, 0.809536, 0.790717, 0.770798, 0.749797,
    0.727739, 0.704669, 0.680643, 0.655736, 0.630036,
    0.603648, 0.576692, 0.549301, 0.521619, 0.4938,
    0.466003, 0.438391, 0.411125, 0.384363, 0.358254,
    0.332939, 0.308598, 0.285354, 0.263242, 0.242244,
    0.222333, 0.203491, 0.185689, 0.16891, 0.153125,
    0.138313, 0.124448, 0.111505, 0.099462, 0.088286,
    0.077958, 0.068448, 0.059728, 0.051773, 0.044548,
    0.038026, 0.032176, 0.026964, 0.022355, 0.018318,
    0.014816, 0.011806, 0.009261, 0.007133, 0.005378,
    0.003971, 0.002857, 0.001992, 0.001353, 0.00089,
    0.000562, 0.00034, 0.000199, 0.000112, 5.9e-05,
    2.4e-05, 7e-06, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0
])

ak_fulllevel_137, bk_fulllevel_137 = \
    compute_full_level_akbk(137, ak_halflevel_137, bk_halflevel_137)


def half_level_pressure(surface_pressure, num_levels=91):
    """Compute the half-level pressure in [Pa] after equation (2.11) in the
       IFS documentation << NOTE THE UNITS! [Pa, NOT hPa] >> :
                  p_(k+1/2) = a_(k+1/2) + b_(k+1/2) * p_sfc

    This method is valid for the 91(137,62,31) level version of the ECMWF
    model. Note, however, that an array of length 92(138,63,32) is returned
    (correspondig to the list on the ECMWF webpage at
    www.ecmwf.int/products/data/technical/model_levels/model_def_91.html), with
    surface pressure being the 92nd(63rd,32nd) value.

    Arguments:
    surface_pressure -- self explaining scalar in [Pa]. ;-) This is
                        NOT mean sea level pressure! (ECMWF 'sp' field,
                        not 'msl' field).
    num_levels -- number of ECMWF model levels, currently the only valid
                  values for this argument are 137,91,62,31.

    Returns: 
    A numpy array of length num_levels+1, at index [0] the pressure of the
    uppermost model half-level can be found, at index [num_levels] the surface
    pressure.

    NOTE: This method can only handle scalars as input, see
          full_level_pressure_fast() on how to implement array support.
    """
    if num_levels not in [31, 62, 91, 137]:
        raise ValueError("num_levels must be one of 31, 62, 91, 137, not %i" % num_levels)
    # NOTE that the ak/bk coefficients are defined for units [hPa], hence
    # the internal pressure units in this function are hPa.
    surface_pressure /= 100.
    half_level_pressure = numpy.zeros(num_levels + 1)
    half_level_pressure[0] = surface_pressure
    if num_levels == 137:
        half_level_pressure[1:] = ak_halflevel_137 + \
                                  surface_pressure * bk_halflevel_137
    elif num_levels == 91:
        half_level_pressure[1:] = ak_halflevel_91 + \
                                  surface_pressure * bk_halflevel_91
    elif num_levels == 62:
        half_level_pressure[1:] = ak_halflevel_62 + \
                                  surface_pressure * bk_halflevel_62
    elif num_levels == 31:
        half_level_pressure[1:] = ak_halflevel_31 + \
                                  surface_pressure * bk_halflevel_31
    return half_level_pressure[::-1] * 100.


def full_level_pressure(surface_pressure, num_levels=91):
    """Compute the full-level pressure (i.e. the pressure at the model
       levels) in [Pa] from the half-level pressure via
                  p_k = 0.5 * (p_(k-1/2) + p_(k+1/2))

    See also half_level_pressure().

    Argument:
    surface_pressure -- self explaining scalar in [Pa]. ;-) This is
                        NOT mean sea level pressure! (ECMWF 'sp' field,
                        not 'msl' field).
    num_levels -- number of ECMWF model levels, currently the only valid
                  values for this argument are 137, 91, 62, 31.

    Returns:
    A numpy array of length 91(62,31) at index [0] the pressure of the
    uppermost model level can be found, at index [90(61,30)] the
    pressure of the lowest level.       

    NOTE: This method can only handle scalars as input, see
          full_level_pressure_fast() on how to implement array support.
    """
    half_level_pressure_ = half_level_pressure(surface_pressure, num_levels)
    return 0.5 * (half_level_pressure_[0:-1] + half_level_pressure_[1:])


def full_level_pressure_fast(surface_pressure, levelaxis=-1, num_levels=91):
    """Compute the full-level pressure, i.e. the pressure at the model
       levels, in [Pa]. << NOTE THE UNITS! [Pa, NOT hPa] >>

    Results are the same as from full_level_pressure(), but the pressure is
    computed with precomputed coefficients from compute_full_level_akbk(). Also,
    this funtion can handle numpy arrays of arbitrary size and dimension as
    input surface pressure.

    See also half_level_pressure(), full_level_pressure().

    Argument:
    surface_pressure -- surface pressure in [Pa] as either a scalar or an
                        N-D numpy array (e.g. 1D for a flight track,
                        2D for a lat/lon grid, 3D for a lat/lon grid and
                        time) This is NOT mean sea level pressure! (ECMWF
                        'sp' field, not 'msl' field).
    levelaxis -- specify at which axis in the return array the level
                 information is stored (values >= 0 are allowed). By
                 default, this will be the last axis (i.e., a 2D input
                 array [lat, lon] will yield a 3D output array [lat,
                 lon, level]). See example below. 
    num_levels -- number of ECMWF model levels, currently the only valid
                  values for this argument are 137,91,62,31.

    Returns:
    A numpy array of of dimension dim(surface_pressure)+1, where the axis of the
    additional dimension is specified by 'levelaxis'. The new dimension if of
    length 91(137,62,31). At index [0] the pressure of the uppermost model level can
    be found, at index [90(136,61,30)] the pressure of the lowest level.

    Example: Consider a time-dependent lat/lon field of surface pressure,
             as can be found in an ECMWF NetCDF file containing several
             time steps. The input variable would have dimensions
             (time, lat, lon). Calling full_level_pressure_fast() without
             the levelaxis argument results in an array with dimensions
             (time, lat, lon, levelist). However, all 4D fields in the
             ECMWF files are stored in the order (time, levelist, lat, lon).
             Thus we call full_level_pressure_fast() with the argument
             levelaxis=1.
    """
    if num_levels not in [137, 91, 62, 31]:
        raise ValueError("num_levels must be one of 31, 62, 91, 137, not %i" % num_levels)

    # Make sure that the input parameter 'surface pressure' is a NumPy array
    # and store its shape in order to restore it below.
    # NOTE that the ak/bk coefficients are defined for units [hPa], hence
    # the internal pressure units in this function are hPa.
    surface_pressure = numpy.array(surface_pressure) / 100.
    spshape = surface_pressure.shape

    # Compute the full level pressures via p_(k) = a_(k) + b_(k) * p_sfc.
    # outer() flattens 'surface_pressure' to a 1D array, then adds a
    # dimension and multiplies each element of surface_pressure by each
    # element of bk. This always results in a 2D array, hence the correct
    # shape of the results needs to be restored with reshape().
    if num_levels == 137:
        data = ak_fulllevel_137[::-1] + numpy.outer(surface_pressure,
                                                    bk_fulllevel_137[::-1])
        data = data.reshape(spshape + (137,))
    elif num_levels == 91:
        data = ak_fulllevel_91[::-1] + numpy.outer(surface_pressure,
                                                   bk_fulllevel_91[::-1])
        data = data.reshape(spshape + (91,))
    elif num_levels == 62:
        data = ak_fulllevel_62[::-1] + numpy.outer(surface_pressure,
                                                   bk_fulllevel_62[::-1])
        data = data.reshape(spshape + (62,))
    elif num_levels == 31:
        data = ak_fulllevel_31[::-1] + numpy.outer(surface_pressure,
                                                   bk_fulllevel_31[::-1])
        data = data.reshape(spshape + (31,))

        # If the levelaxis argument is given, move the axis to the specified
    # position. Since the order of the remaining axes has to be kept, this
    # has to be done iteratively by exchanging the level axis (initially the
    # last one) with the preceding one -- until the desired position has
    # been reached.
    if levelaxis >= 0:
        for i in range(data.ndim - 1, levelaxis, -1):
            data = data.swapaxes(i, i - 1)

    return data * 100.


"""
Mask and Scale Functions
"""


def scale_variable(nc_var):
    """Scale the data of a packed NetCDF variable and return the result as
       a NumPy array.

    Arguments:
    nc_var -- Scientific.IO.NetCDF variable object

    Returns:
    numpy.ndarray with scaled data.

    An exception is raised if either the input argument does not represent
    a valid CF-compliant NetCDF variable, or if the data field contains
    missing values (which should be handled appropriately by a masked array;
    see the NumPy documentation for further details).
    """
    # Test if all attributes required by the CF-conventions are present.
    test = [b in dir(nc_var) for b in ['long_name', 'units']]
    if not numpy.array(test).all():
        raise ECMWFInvalidNetCDFVariableError, "NetCDF variable %s does not " \
                                               "represent a valid CF-compliant data field." % nc_var.long_name

    # Get the data array of the variable object and test if missing
    # values are present in the field (values that correspond to the _FillValue
    # attribute). If this is the case, the data should be converted to
    # a masked array instead of a regular numpy.array (NOT IMPLEMENTED YET).
    # For further information about missing values, see
    #    http://cf-pcmdi.llnl.gov/documents/cf-conventions/1.4/
    #                                       cf-conventions.html#missing-data
    try:
        data = nc_var.getValue()  # Scientific.IO.NetCDF version
    except:
        data = nc_var[:]  # netCDF4 version
    if '_FillValue' in dir(nc_var):
        if not (data - nc_var._FillValue).all():
            raise ECMWFMissingValueError, "NetCDF variable %s contains " \
                                          "mssing values. Please implement a method using masked " \
                                          "arrays for this kind of data." % nc_var.long_name

    # If the above tests succeeded, check if scale and offset attributes
    # are specified -- if not, return the data as-is as a numpy.ndarray
    # object, otherwise scale and offset the data.
    if not ('add_offset' in dir(nc_var) and 'scale_factor' in dir(nc_var)):
        return data
    else:
        return data * nc_var.scale_factor + nc_var.add_offset


"""
Data processing
"""


def omega_to_w(data_omega, data_sfc_pressure, data_temperature, levelaxis=-1,
               return_rho_pressure=False):
    """Convert pressure vertical velocity to geometric vertical velocity at
       all model levels.

    Arguments:
    data_omega -- 1D to 4D field of pressure vertical velocity [Pa/s]
    data_sfc_pressure -- [dim(data_omega)-1]D field of surface pressure [Pa]
    data_temperature -- dim(data_omega)D field of temperature [K]
    levelaxis -- optional parameter to specify the axis at which the
                 vertical coordinate is stored in data_omega, data_temperature,
                 and the output array. By default, the vertical axis is
                 assumed to be the only axis for 1D arrays, the second
                 axis for 2D arrays (e.g. [time, levelist]), the first
                 axis for 3D arrays (e.g. [levelist, lat, lon]), and
                 the second axis for 4D arrays (e.g. [time, levelist, lat, lon])
    return_rho_pressure -- if True, arrays containing the air density rho,
                           as well as the pressure p are also returned.
                           Default is False

    data_omega and data_temperature can be 1D (one point, all model levels)
    to 4D (3D plus time fields) fields from ECMWF forecasts or analyses.
    data_sfc_pressure is a field with one dimension less (i.e. a single
    point to a 2D surface field plus time), from which the full field
    of pressure values on the model surfaces is reconstructed with
    full_level_pressure_fast().

    For all grid points, the pressure vertical velocity in Pa/s is converted
    to m/s via
                    w[m/s] =(approx) omega[Pa/s] / (-g*rho)
                       rho = p / R*T
    (see p.13 of 'Introduction to circulating atmospheres' by Ian N. James).

    Returns:
    NumPy array of the same dimension as data_omega, containing the geometric
    vertical velocity in [m/s]. If return_rho_pressure is set to True,
    two additional arrays containg air density and pressure are also returned
    (same dimensions).

    NOTE: Please check the resulting values, especially in the upper atmosphere!
    """
    # Specify the default values for the vertical coordinate axis position
    # (dependent on dim(data_omega), see the comment above).
    if levelaxis < 0:
        levelaxis = [-1, -1, 1, 0, 1][data_omega.ndim]

    # Compute p from the surface pressure field.
    data_pressure = full_level_pressure_fast(data_sfc_pressure,
                                             levelaxis=levelaxis)
    # Compute rho = p / R*T.
    data_rho = data_pressure / (287.058 * data_temperature)

    # Return w[m/s] =(approx) omega / (-g*rho), if requested also return
    # data_rho and data_pressure.
    if return_rho_pressure:
        return data_omega / (-9.80665 * data_rho), data_rho, data_pressure
    else:
        return data_omega / (-9.80665 * data_rho)
