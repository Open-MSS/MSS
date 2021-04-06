#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

    mslib.mswms.demodata
    ~~~~~~~~~~~~~~~~~~~~

    creates netCDF test data files and also a mss_wms_settings for accessing this data

    This file is part of mss.

    :copyright: Copyright 2017 Jens-Uwe Grooss, Joern Ungermann, Reimar Bauer
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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

import argparse
import os
import sys
import netCDF4 as nc
import numpy as np
import fs
from mslib import __version__


_SURFACE_TEXT = """\
surface_geopotential
m^2.s^-2
  2.12e+03   4.74e+03
air_pressure_at_sea_level
Pa
  9.89e+04   5.30e+02
total_cloud_cover
dimensionless
  6.32e-01   3.93e-01
land_binary_mask
dimensionless
  4.20e-01   4.94e-01
low_cloud_area_fraction
dimensionless
  3.67e-01   3.91e-01
medium_cloud_area_fraction
dimensionless
  2.95e-01   3.77e-01
high_cloud_area_fraction
dimensionless
  4.07e-01   4.41e-01
surface_eastward_wind
m.s^-1
  0 50
surface_northward_wind
m.s^-1
  0 50
solar_elevation_angle
degree
  45 20
sea_ice_area_fraction
dimensionless
  0.5 0.3
msg_brightness_temperature_108
nW.cm.m^-2.sr^-1
  100 20
atmosphere_boundary_layer_thickness
m
  1000 400
emac_column_density
dimensionless
 0.25 0.2
vertically_integrated_probability_of_wcb_occurrence
dimensionless
 0.25 0.2"""

_PROFILES_TEXT = """\
air_pressure
Pa
    20           2
    50           5
   100          10
   200          20
   500          50
  1000         100
  2000         200
  3000         300
  5000         500
  7000         700
  10000       1000
  15000       1500
  20000       2000
  25000       2500
  30000       3000
  40000       4000
  50000       5000
  60000       6000
  70000       7000
  80000       8000
  85000       8500
  90000       9000
  92500       9500
  95000       10000
ertel_potential_vorticity
PVU
  3.91e+04   1.13e+04
  1.23e+04   2.76e+03
  6.00e+03   7.97e+02
  2.33e+03   4.57e+02
  7.21e+02   1.49e+02
  2.76e+02   4.95e+01
  1.00e+02   1.70e+01
  6.14e+01   1.03e+01
  2.94e+01   4.86e-00
  1.88e+01   3.51e-00
  1.15e+01   3.26e-00
  6.53e-00   2.85e-00
  4.71e-00   3.21e-00
  2.78e-00   3.09e-00
  1.39e-00   2.23e-00
  5.58e-01   7.26e-01
  5.39e-01   4.40e-01
  5.30e-01   3.95e-01
  5.20e-01   9.73e-01
  5.11e-01   3.37e-00
  4.73e-01   3.62e-00
  3.96e-01   3.81e-00
  2.05e-01   3.94e-00
  1.95e-01   4.09e-00
geopotential_height
m
  5.95e+01   9.22e+01
  5.27e+01   9.22e+01
  4.73e+01   9.22e+01
  4.20e+01   9.22e+01
  3.55e+01   9.22e+01
  3.08e+01   9.22e+01
  2.57e+04   9.22e+01
  2.33e+04   6.80e+01
  2.01e+04   6.96e+01
  1.81e+04   9.61e+01
  1.59e+04   1.48e+02
  1.34e+04   2.17e+02
  1.17e+04   2.55e+02
  1.02e+04   2.63e+02
  9.07e+03   2.50e+02
  7.11e+03   2.09e+02
  5.51e+03   1.73e+02
  4.15e+03   1.43e+02
  2.97e+03   1.18e+02
  1.91e+03   9.65e+01
  1.43e+03   8.72e+01
  9.68e+02   7.96e+01
  7.46e+02   7.65e+01
  5.29e+02   7.40e+01
air_temperature
K
  2.39e+02   2.74e+00
  2.51e+02   3.59e+00
  2.54e+02   3.84e+00
  2.45e+02   4.40e+00
  2.32e+02   5.15e+00
  2.23e+02   3.03e+00
  2.15e+02   3.79e+00
  2.13e+02   2.07e+00
  2.12e+02   3.10e+00
  2.12e+02   4.82e+00
  2.12e+02   6.31e+00
  2.16e+02   5.91e+00
  2.18e+02   5.03e+00
  2.22e+02   3.86e+00
  2.29e+02   5.00e+00
  2.44e+02   6.20e+00
  2.55e+02   6.33e+00
  2.64e+02   6.30e+00
  2.71e+02   6.62e+00
  2.77e+02   7.36e+00
  2.79e+02   7.67e+00
  2.81e+02   7.91e+00
  2.82e+02   7.97e+00
  2.84e+02   7.93e+00
air_potential_temperature
K
  2.80e+03   4.59e+01
  2.26e+03   2.34e+01
  1.85e+03   2.32e+01
  1.45e+03   1.83e+01
  1.05e+03   2.14e+01
  8.29e+02   1.12e+01
  657.443538145 3.79
  580.079898831 2.07
  498.951941454 3.10
  453.218730010 4.82
  409.307918523 6.31
  371.412271319 5.91
  345.272674711 5.03
  329.890732188 3.86
  323.019997594 5.00
  317.020226317 6.20
  310.848481822 6.33
  305.484573481 6.30
  300.073050812 6.62
  295.235341640 7.36
  292.260568339 7.67
  289.587551318 7.91
  288.351954158 7.97
  288.192732138 7.93
eastward_wind
m.s^-1
  4.68e+01   1.36e+01
  4.57e+01   1.43e+01
  3.97e+01   1.42e+01
  2.96e+01   1.44e+01
  2.08e+01   1.31e+01
  1.70e+01   8.40e+00
  5.36e+00   7.99e+00
  3.69e+00   5.80e+00
  3.83e+00   4.66e+00
  5.62e+00   4.50e+00
  8.74e+00   5.80e+00
  1.27e+01   9.47e+00
  1.51e+01   1.29e+01
  1.52e+01   1.44e+01
  1.36e+01   1.37e+01
  1.07e+01   1.10e+01
  8.70e+00   9.16e+00
  6.98e+00   7.99e+00
  5.23e+00   7.42e+00
  3.48e+00   6.97e+00
  2.66e+00   6.85e+00
  1.76e+00   6.77e+00
  1.27e+00   6.65e+00
  7.67e-01   6.35e+00
northward_wind
m.s^-1
  7.03e-02   1.01e+01
 -1.88e-01   9.98e+00
  4.11e-01   8.97e+00
  2.13e-01   6.33e+00
  9.45e-02   5.67e+00
  2.35e-01   5.26e+00
 -1.19e+00   5.11e+00
 -9.02e-01   4.34e+00
 -1.01e+00   4.56e+00
 -1.07e+00   6.27e+00
 -1.47e+00   9.54e+00
 -2.11e+00   1.51e+01
 -1.92e+00   1.93e+01
 -8.76e-01   2.14e+01
 -1.18e-02   2.07e+01
  7.96e-01   1.64e+01
  1.14e+00   1.32e+01
  1.32e+00   1.13e+01
  1.41e+00   9.96e+00
  1.22e+00   8.97e+00
  1.11e+00   8.76e+00
  9.43e-01   8.81e+00
  8.61e-01   8.81e+00
  7.32e-01   8.64e+00
specific_humidity
kg.kg^-1
  4.60e-06   3.29e-08
  4.47e-06   2.90e-08
  4.12e-06   8.67e-08
  3.72e-06   1.92e-07
  3.48e-06   1.73e-07
  3.31e-06   1.44e-07
  2.94e-06   1.20e-07
  2.86e-06   1.10e-07
  2.68e-06   5.65e-08
  2.70e-06   6.27e-08
  2.90e-06   2.00e-07
  4.99e-06   3.43e-06
  1.78e-05   1.58e-05
  5.30e-05   4.71e-05
  1.27e-04   1.14e-04
  3.88e-04   3.59e-04
  8.00e-04   7.17e-04
  1.38e-03   1.16e-03
  2.25e-03   1.63e-03
  3.45e-03   2.02e-03
  4.24e-03   2.18e-03
  5.16e-03   2.37e-03
  5.64e-03   2.44e-03
  6.07e-03   2.55e-03
lagrangian_tendency_of_air_pressure
Pa.s^-1
 -4.38e-03   6.64e-02
 -7.20e-03   6.82e-02
 -5.57e-03   5.85e-02
 -1.87e-03   4.52e-02
 -3.46e-03   2.90e-02
 -5.96e-04   2.37e-02
 -2.45e-04   5.71e-03
 -4.91e-04   7.48e-03
 -9.50e-04   1.13e-02
 -1.49e-03   1.65e-02
 -2.27e-03   2.84e-02
 -3.66e-03   5.61e-02
 -5.70e-03   9.28e-02
 -6.75e-03   1.48e-01
 -8.09e-03   2.11e-01
 -9.84e-03   3.00e-01
 -1.00e-02   3.45e-01
 -8.50e-03   3.73e-01
 -6.03e-03   4.18e-01
  1.74e-03   4.44e-01
  7.14e-03   4.26e-01
  1.28e-02   3.90e-01
  1.57e-02   3.60e-01
  1.85e-02   3.18e-01
divergence_of_wind
s^-1
  2.66e-09   1.74e-05
  1.00e-06   2.00e-05
  4.04e-06   2.49e-05
  2.20e-06   2.36e-05
  3.60e-07   2.05e-05
  3.64e-07   2.07e-05
  2.19e-07   1.75e-05
  2.29e-07   1.73e-05
  2.93e-07   2.00e-05
  2.17e-07   2.65e-05
  2.76e-07   2.91e-05
  4.83e-07   3.13e-05
  2.32e-07   3.50e-05
  1.98e-07   3.45e-05
  2.86e-07   3.43e-05
  8.41e-08   3.28e-05
 -8.39e-08   3.42e-05
 -2.00e-07   3.79e-05
 -2.87e-07   4.33e-05
 -2.19e-07   5.11e-05
 -8.42e-08   5.39e-05
  1.39e-08   5.63e-05
  4.93e-08   5.71e-05
  8.47e-08   5.94e-05
mole_fraction_of_ozone_in_air
kg.kg^-1
  1.45e-06   7.50e-08
  2.95e-06   7.83e-08
  5.04e-06   1.71e-07
  8.78e-06   3.11e-07
  1.15e-05   4.18e-07
  1.22e-05   7.58e-07
  8.09e-06   1.21e-06
  5.70e-06   5.69e-07
  3.46e-06   4.69e-07
  2.41e-06   5.23e-07
  1.44e-06   4.97e-07
  6.27e-07   3.28e-07
  2.82e-07   2.03e-07
  1.37e-07   1.08e-07
  8.30e-08   4.80e-08
  6.40e-08   1.39e-08
  6.23e-08   8.08e-09
  6.18e-08   6.28e-09
  6.18e-08   5.47e-09
  6.17e-08   4.73e-09
  6.15e-08   4.57e-09
  6.14e-08   4.60e-09
  6.12e-08   4.64e-09
  6.09e-08   4.65e-09
mass_fraction_of_ozone_in_air
kg.kg^-1
  1.45e-06   7.50e-08
  2.95e-06   7.83e-08
  5.04e-06   1.71e-07
  8.78e-06   3.11e-07
  1.15e-05   4.18e-07
  1.22e-05   7.58e-07
  8.09e-06   1.21e-06
  5.70e-06   5.69e-07
  3.46e-06   4.69e-07
  2.41e-06   5.23e-07
  1.44e-06   4.97e-07
  6.27e-07   3.28e-07
  2.82e-07   2.03e-07
  1.37e-07   1.08e-07
  8.30e-08   4.80e-08
  6.40e-08   1.39e-08
  6.23e-08   8.08e-09
  6.18e-08   6.28e-09
  6.18e-08   5.47e-09
  6.17e-08   4.73e-09
  6.15e-08   4.57e-09
  6.14e-08   4.60e-09
  6.12e-08   4.64e-09
  6.09e-08   4.65e-09
equivalent_latitude
degree
  4.30e+01   1.05e+01
  4.48e+01   8.70e+00
  4.58e+01   5.58e+00
  4.21e+01   8.11e+00
  4.37e+01   7.42e+00
  4.57e+01   5.66e+00
  80.09   1.21
  50.70   5.69
  30.46   4.69
  20.41   5.23
  10.44   4.97
  60.27   3.28
  20.82   2.03
  10.37   1.08
  80.30   4.80
  60.40   1.39
  60.23   8.08
  60.18   6.28
  60.18   5.47
  60.17   4.73
  60.15   4.57
  60.14   4.60
  60.12   4.64
  60.09   4.65
cloud_area_fraction_in_atmosphere_layer
dimensionless
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  2.99e-06   4.96e-04
  1.89e-02   1.15e-01
  5.84e-02   1.99e-01
  1.60e-01   3.15e-01
  1.87e-01   3.34e-01
  1.34e-01   2.94e-01
  1.01e-01   2.57e-01
  9.27e-02   2.43e-01
  9.58e-02   2.38e-01
  1.29e-01   2.53e-01
  1.50e-01   2.72e-01
  1.58e-01   3.06e-01
  1.34e-01   3.03e-01
  9.84e-02   2.69e-01
atmosphere_hybrid_pressure_coordinate
Pa
     20.0000 0
     50.0000 0
    100.0000 0
    200.0000 0
    500.0000 0
   1000.0000 0
   2001.3900 0
   2997.9320 0
   4997.2623 0
   7000.5268 0
   9942.4557 0
  14336.9286 0
  17394.2910 0
  19250.0066 0
  20190.6354 0
  20085.4085 0
  18217.6976 0
  15216.7109 0
  11459.3119 0
   7208.6030 0
   4986.5092 0
   2813.2305 0
   1785.5353 0
    843.9551 0
atmosphere_hybrid_height_coordinate
1
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.0        0
  0.000328   0
  0.006963   0
  0.026479   0
  0.057930   0
  0.099104   0
  0.201532   0
  0.321698   0
  0.453253   0
  0.592051   0
  0.736368   0
  0.809785   0
  0.882253   0
  0.917775   0
  0.952463   0
hybrid
1
   0 0
   1 0
   2 0
   3 0
   4 0
   5 0
   6 0
   7 0
   8 0
   9 0
  10 0
  11 0
  12 0
  13 0
  14 0
  15 0
  16 0
  17 0
  18 0
  19 0
  20 0
  21 0
  22 0
  23 0
specific_cloud_ice_water_content
kg.kg^-1
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  2.94e-05   1.20e-05
  2.86e-05   1.10e-05
  2.68e-05   5.65e-05
  2.70e-05   6.27e-05
  2.90e-05   2.00e-05
  4.99e-05   3.43e-05
  1.78e-05   1.58e-05
  5.30e-05   4.71e-05
  1.27e-05   1.14e-05
  3.88e-05   3.59e-05
  8.00e-05   7.17e-05
  1.38e-05   1.16e-05
  2.25e-05   1.63e-05
  3.45e-05   2.02e-05
  4.24e-05   2.18e-05
  5.16e-05   2.37e-05
  5.64e-05   2.44e-05
  6.07e-05   2.55e-05
specific_cloud_liquid_water_content
kg.kg^-1
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  0.00e+00   0.00e+00
  4.99e-05   3.43e-05
  1.78e-05   1.58e-05
  5.30e-05   4.71e-05
  1.27e-05   1.14e-05
  3.88e-05   3.59e-05
  8.00e-05   7.17e-05
  1.38e-05   1.16e-05
  2.25e-05   1.63e-05
  3.45e-05   2.02e-05
  4.24e-05   2.18e-05
  5.16e-05   2.37e-05
  5.64e-05   2.44e-05
  6.07e-05   2.55e-05
  2.94e-05   1.20e-05
  2.86e-05   1.10e-05
  2.68e-05   5.65e-05
  2.70e-05   6.27e-05
  2.90e-05   2.00e-05
emac_R12
dimensionless
  12 20
  14 20
  16 20
  18 20
  20 20
  23 20
  25 20
  28 20
  31 20
  34 20
  37 20
  40 20
  43 20
  46 20
  49 20
  52 20
  55 20
  58 20
  61 20
  64 20
  67 20
  70 20
  73 20
  76 20
probability_of_wcb_occurrence
dimensionless
  0.0000 0.3
  0.0000 0.3
  0.0588 0.3
  0.1588 0.3
  0.2588 0.3
  0.3588 0.3
  0.4588 0.3
  0.2345 0.3
  0.5646 0.3
  0.7133 0.3
  0.4211 0.3
  0.0233 0.3
  0.9266 0.3
  0.1973 0.3
  0.7116 0.3
  0.6238 0.3
  0.4413 0.3
  0.4247 0.3
  0.4680 0.3
  0.8440 0.3
  0.1808 0.3
  0.3535 0.3
  0.3312 0.3
  0.9137 0.3
number_of_wcb_trajectories
dimensionless
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  9.83136620961e-06 3e-6
  8.10710322623e-06 3e-6
  5.03285054247e-06 3e-6
  9.75045639082e-06 3e-6
  8.78250966953e-06 3e-6
  6.42616522157e-06 3e-6
  3.65834566845e-06 3e-6
  7.31069995609e-06 3e-6
  6.5087658759e-06 3e-6
  5.12785114411e-06 3e-6
  4.3094956301e-06 3e-6
  2.74934238546e-06 3e-6
  3.61389941475e-06 3e-6
  7.85946671197e-07 3e-6
  3.54104461558e-06 3e-6
  2.65885314048e-07 3e-6
  5.17596006307e-06 3e-6
  8.12412830459e-06 3e-6
number_of_insitu_trajectories
dimensionless
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  1.4159717441e-06 3e-6
  7.62262321518e-06 3e-6
  8.76448539884e-06 3e-6
  9.01479034545e-06 3e-6
  8.11105807572e-06 3e-6
  5.90307777897e-06 3e-6
  6.10377189651e-06 3e-6
  4.20623841981e-06 3e-6
  6.21562130245e-07 3e-6
  2.03431966005e-06 3e-6
  9.9543462734e-06 3e-6
  7.83544282101e-06 3e-6
  9.53835890445e-06 3e-6
  4.43370076609e-06 3e-6
  5.04023963205e-06 3e-6
  3.72059751023e-06 3e-6
  6.0163792186e-06 3e-6
  3.866286373e-06 3e-6
number_of_mix_trajectories
dimensionless
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  0                 3e-6
  3.06481460477e-06 3e-6
  2.22900351535e-06 3e-6
  9.55973892153e-06 3e-6
  6.03223628958e-07 3e-6
  7.43475308453e-06 3e-6
  7.4955287792e-06 3e-6
  9.22484798348e-06 3e-6
  3.72235419397e-06 3e-6
  9.51703649579e-07 3e-6
  7.70187452058e-06 3e-6
  2.55378282787e-06 3e-6
  3.42367431894e-06 3e-6
  6.31294877753e-06 3e-6
  4.07098483236e-06 3e-6
  2.50960684064e-06 3e-6
  2.23637957702e-07 3e-6
  7.50906889384e-06 3e-6
  5.77393276332e-06 3e-6"""

_ALLOW_NEGATIVE = ['surface_geopotential',
                   'ertel_potential_vorticity',
                   'eastward_wind',
                   'northward_wind',
                   'lagrangian_tendency_of_air_pressure',
                   'divergence_of_wind']


def _parse_text(text, entry_length):
    """
    This function converts the textual description of profile/surface data to a dictionary.
    :param text: String database
    :param entry_length: number of lines per entity entry
    :return: dictionary of information with one key per entity
    """
    result = {}
    lines = text.split("\n")
    for i in range(0, len(lines), entry_length):
        name = lines[i]
        unit = lines[i + 1]
        data = np.asarray([list(map(float, line.split())) for line in lines[i + 2:i + entry_length]])
        result[name] = {"unit": unit, "data": data}
    return result


_PROFILES = _parse_text(_PROFILES_TEXT, 26)
_SURFACE = _parse_text(_SURFACE_TEXT, 3)


def get_profile(coordinate, levels, standard_name):
    """
    Interpolates information of mean and variance in profile database according to the
    specified coordinate and levels.

    :param coordinate: key specifying the coordinate entity. Must be monotonous.
           (air_pressure, air_potential_temperature, geopotential_height, ertel_potential_vorticity are tested)
    :param levels: Numerical values of coordinate variable to interpolate at
    :param standard_name: CF standard name of entity to interpolate at specified points.
    :return: two array, one for mean, ond for variance at specified levels.
    """
    assert coordinate in _PROFILES, coordinate
    assert standard_name in _PROFILES, standard_name

    if _PROFILES[coordinate]["data"][0, 0] < _PROFILES[coordinate]["data"][1, 0]:
        mean = np.interp(levels, _PROFILES[coordinate]["data"][:, 0], _PROFILES[standard_name]["data"][:, 0])
        std = np.interp(levels, _PROFILES[coordinate]["data"][:, 0], _PROFILES[standard_name]["data"][:, 1])
    else:
        mean = np.interp(levels, _PROFILES[coordinate]["data"][::-1, 0], _PROFILES[standard_name]["data"][::-1, 0])
        std = np.interp(levels, _PROFILES[coordinate]["data"][::-1, 0], _PROFILES[standard_name]["data"][::-1, 1])
    return mean, std


def _generate_3d_data(ntimes, nlats, nlons, mean, std, ilev=0):
    xarr = np.linspace(0., 10. + (ilev / 3.), nlons)
    yarr = np.linspace(0., 5. + (ilev / 3.), nlats)
    tarr = np.linspace(0, 2., ntimes)
    datax = xarr[np.newaxis, np.newaxis, :] + tarr[:, np.newaxis, np.newaxis]
    datay = yarr[np.newaxis, :, np.newaxis] - tarr[:, np.newaxis, np.newaxis]
    return mean + std * (np.sin(datax) + np.cos(datay)) / 2


def _generate_4d_data(ntimes, nlats, nlons, means, stds):
    assert len(means) == len(stds)
    data = np.empty((ntimes, len(means), nlats, nlons))
    for ilev, (mean, std) in enumerate(zip(means, stds)):
        data[:, ilev, :, :] = _generate_3d_data(ntimes, nlats, nlons, mean, std, ilev=ilev)
    return data


def _correct_data(standard_name, unit, data):
    if standard_name not in _ALLOW_NEGATIVE:
        data[data < 0] = 0
    if standard_name == "land_binary_mask":
        data = data.round()
    if unit == "(0.-.1)":
        data[data < 0] = 0
        data[data > 1] = 1
    if unit == "(0.-.100)":
        data[data < 0] = 0
        data[data > 100] = 100
    return data


def generate_surface(standard_name, ntimes, nlats, nlons):
    """
    Generates a random surface field for given entity of specified size.

    :param standard_name: Entity to generate field for
    :param ntimes: number of times
    :param nlats: number of latitudes
    :param nlons: number of longitudes
    :return: tuple of 3-D array and unit of data
    """
    mean, std = _SURFACE[standard_name]["data"][0]
    data = _generate_3d_data(ntimes, nlats, nlons, mean, std)
    data = _correct_data(standard_name, _SURFACE[standard_name]["unit"], data)
    return data, _SURFACE[standard_name]["unit"]


def generate_field(coordinate, levels, standard_name, ntimes, nlats, nlons):
    """
    Generates a random 4-D field for given entity of specified size.

    :param coordinate: standard_name of coordinate axis
    :param levels: numerical values of coordinate axis to generate data on
    :param standard_name: Entity to generate field for
    :param ntimes: number of times
    :param nlats: number of latitudes
    :param nlons: number of longitudes
    :return: tuple of 4-D array and unit of data
    """
    means, stds = get_profile(coordinate, levels, standard_name)
    data = _generate_4d_data(ntimes, nlats, nlons, means, stds)
    data = _correct_data(standard_name, _PROFILES[standard_name]["unit"], data)
    return data, _PROFILES[standard_name]["unit"]


class DataFiles(object):
    """
    Routine to write test data files for MSS using extracted
    variable ranges from ECMWF data
    Jens-Uwe Grooss, IEK-7, Forschungszentrum Juelich, Nov 2016

    """

    dimensions = {
        "latitude": ("lat", "degrees_north", ""),
        "longitude": ("lon", "degrees_north", ""),
        "hybrid": ("hybrid", None, None),
        "atmosphere_pressure_coordinate": ("isobaric", "hPa", "down"),
        "atmosphere_potential_temperature_coordinate": ("isentropic", "K", ""),
        "atmosphere_altitude_coordinate": ("height", "m", ""),
        "atmosphere_ertel_potential_vorticity_coordinate": ("isopv", "PVU", ""),
        "time": ("time", "hours since 2012-10-17T12:00:00.000Z", "")
    }

    def __init__(self, data_fs=None, server_config_fs=None):
        self.data_fs = data_fs
        self.server_config_fs = server_config_fs
        self.server_config_file = "mss_wms_settings.py"
        self.server_auth_config_file = "mss_wms_auth.py"
        # define file dimension / geographical  range

    def create_server_config(self, detailed_information=False):
        simple_auth_config = '''# -*- coding: utf-8 -*-
"""

    mss_wms_settings
    ~~~~~~~~~~~~~~~~

    Configuration module for programs accessing data on the MSS server.

    This file is part of mss.

    :copyright: 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: 2011-2014 Marc Rautenhaus
    :copyright: Copyright 2017 Jens-Uwe Grooss, Joern Ungermann, Reimar Bauer
    :copyright: Copyright 2017-2020 by the mss team, see AUTHORS.
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
#
# HTTP Authentication                               ###
#
#
# Use the following code to create a new md5 digest of a password (e.g. in
# ipython):
#     import hashlib; hashlib.md5("my_new_password").hexdigest()
allowed_users = [("mswms", "add_md5_digest_of_PASSWORD_here"),
                 ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]

'''
        if detailed_information:
            simple_server_config = '''# -*- coding: utf-8 -*-
"""

    mss_wms_settings
    ~~~~~~~~~~~~~~~~

    Configuration module for programs accessing data on the MSS server.

    This file is part of mss.

    :copyright: 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: 2011-2014 Marc Rautenhaus
    :copyright: Copyright 2017 Jens-Uwe Grooss, Joern Ungermann, Reimar Bauer
    :copyright: Copyright 2017-2020 by the mss team, see AUTHORS.
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

import os
import sys

# on a productions system you may want to limit the amout of tracebacks to 0
# sys.tracebacklimit = 0

# Configuration of Python's code search path
# If you already have set up the PYTHONPATH environment variable for the
# stuff you see below, you don't need to do a1) and a2).

# a1) Path of the directory where the mss code package is located.
# sys.path.insert(0, '/home/mss/miniconda3/lib/python3.7/site-packages')

# a2) Path of the directory where mss_wms_settings.py is located

#MSSCONFIGPATH = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
#sys.path.insert(0, MSSCONFIGPATH)
#os.chdir(MSSCONFIGPATH)

import mslib.mswms.dataaccess
from mslib.mswms import mpl_hsec_styles
from mslib.mswms import mpl_vsec_styles
import mslib.mswms


# Configuration for mss_wms_settings accessing data on the MSS server.
# This is the data organisation structure of demodata.


#service_name = "OGC:WMS"
#service_title = "Mission Support System Web Map Service"
#service_abstract = "Your Abstract"
#service_contact_person = "Your Name"
#service_contact_organisation = "Your Organization"
#service_address_type = "postal"
#service_address = "street"
#service_city = "Your City"
#service_state_or_province = ""
#service_post_code = "12345"
#service_country = "Germany"
#service_fees = "none"
#service_access_constraints = "This service is intended for research purposes only."


#
# HTTP Authentication
#
# If you require basic HTTP authentication, set the following variable
# to True. Add usernames in the list "allowed:users". Note that the
# passwords are not specified in plain text but by their md5 digest.
#enable_basic_http_authentication = False


#xml_template directory is a sub directory of mswms
#base_dir = os.path.abspath(os.path.dirname(mslib.mswms.__file__))
#xml_template_location = os.path.join(base_dir, "xml_templates")

_datapath = r"{data_dir}"

data = {{
    "ecmwf_EUR_LL015": mslib.mswms.dataaccess.DefaultDataAccess(_datapath, "EUR_LL015"),
}}


epsg_to_mpl_basemap_table = {{
    # EPSG:4326, the standard cylindrical lat/lon projection.
    4326: {{"projection": "cyl"}}
}}

basemap_use_cache = True

#
# Registration of horizontal layers.
#

# The following list contains tuples of the format (instance of
# visualisation classes, data set). The visualisation classes are
# defined in mpl_hsec.py and mpl_hsec_styles.py. Add only instances of
# visualisation products for which data files are available. The data
# sets must be defined in mss_config.py. The WMS will only offer
# products registered here.
register_horizontal_layers = None
if mpl_hsec_styles is not None:
    register_horizontal_layers = [
        # ECMWF standard pressure level products.
        (mpl_hsec_styles.HS_TemperatureStyle_PL_01, ["ecmwf_EUR_LL015"]),
        (mpl_hsec_styles.HS_GeopotentialWindStyle_PL, ["ecmwf_EUR_LL015"]),
        (mpl_hsec_styles.HS_RelativeHumidityStyle_PL_01, ["ecmwf_EUR_LL015"]),
        (mpl_hsec_styles.HS_EQPTStyle_PL_01, ["ecmwf_EUR_LL015"]),
        (mpl_hsec_styles.HS_WStyle_PL_01, ["ecmwf_EUR_LL015"]),
        (mpl_hsec_styles.HS_DivStyle_PL_01, ["ecmwf_EUR_LL015"]),
    ]


#
# Registration of vertical layers.
#
# The same as above, but for vertical cross-sections.
register_vertical_layers = None
if mpl_vsec_styles is not None:
    register_vertical_layers = [
        # ECMWF standard vertical section styles.
        (mpl_vsec_styles.VS_CloudsStyle_01, ["ecmwf_EUR_LL015"]),
        (mpl_vsec_styles.VS_HorizontalVelocityStyle_01, ["ecmwf_EUR_LL015"]),
        (mpl_vsec_styles.VS_VerticalVelocityStyle_01, ["ecmwf_EUR_LL015"]),
        (mpl_vsec_styles.VS_RelativeHumdityStyle_01, ["ecmwf_EUR_LL015"]),
        (mpl_vsec_styles.VS_SpecificHumdityStyle_01, ["ecmwf_EUR_LL015"]),
        (mpl_vsec_styles.VS_TemperatureStyle_01, ["ecmwf_EUR_LL015"])
    ]
'''
            simple_server_config = simple_server_config.format(data_dir=self.data_fs.root_path)
        else:
            simple_server_config = '''"""
simple server config for demodata
"""
from mslib.mswms.demodata import (data, epsg_to_mpl_basemap_table,
                                  register_horizontal_layers, register_vertical_layers)
'''

        if not self.server_config_fs.exists(self.server_config_file):
            fid = self.server_config_fs.open(self.server_config_file, 'w')
            fid.write(simple_server_config)
            fid.close()
        else:
            print(f'''
/!\\ existing server config: "{self.server_config_file}" for demodata not overwritten!
            ''')
        if not self.server_config_fs.exists(self.server_auth_config_file):
            fid = self.server_config_fs.open(self.server_auth_config_file, 'w')
            fid.write(simple_auth_config)
            fid.close()
        else:
            print(f'''
/!\\ existing server auth config: "{self.server_auth_config_file}" for demodata not overwritten!
                ''')

    def generate_file(self, coordinate, label, leveltype, dimvals, variables):
        """
        Routine to generate a NetCDF file containing randomly generated model data

        :param coordinate: standard_name of vertical axes
        :param label: label for filename generation
        :param leveltype: level type of file
        :param dimvals: numerical values of vertical axis
        :param variables: list of standard_names of variables to write into file
        """
        # ToDo nc.Dataset needs fileobject like access

        filename_out = os.path.join(
            self.data_fs.root_path, f"20121017_12_ecmwf_forecast.{label}.EUR_LL015.036.{leveltype}.nc")
        ecmwf = nc.Dataset(filename_out, 'w', format='NETCDF4_CLASSIC')

        for dim, values in dimvals:
            if dim != "hybrid":
                varname, unit, positive = self.dimensions[dim]
                ecmwf.createDimension(varname, len(values))
                newvar = ecmwf.createVariable(varname, 'f4', varname)
                newvar[:] = values
                newvar.units = unit
                newvar.standard_name = dim
                if positive:
                    newvar.positive = positive
            else:
                ecmwf.createDimension("hybrid", len(values))
                newvar = ecmwf.createVariable('hybrid', 'f4', 'hybrid')
                newvar.standard_name = "atmosphere_hybrid_sigma_pressure_coordinate"
                newvar[:] = values
                newvar.units = 'sigma'
                newvar.positive = 'down'
                newvar.formula = 'p(time,level,lat,lon) = ap(level) + b(level) * ps(time,lat,lon)'
                newvar.formula_terms = 'ap: hyam b: hybm ps: Surface_pressure_surface'
                newvar = ecmwf.createVariable('hyam', 'f4', 'hybrid')
                newvar[:] = get_profile("hybrid", values, "atmosphere_hybrid_pressure_coordinate")[0]
                newvar.units = 'Pa'
                newvar.standard_name = "atmosphere_hybrid_pressure_coordinate"
                newvar = ecmwf.createVariable('hybm', 'f4', 'hybrid')
                newvar[:] = get_profile("hybrid", values, "atmosphere_hybrid_height_coordinate")[0]
                newvar.units = '1'
                newvar.standard_name = "atmosphere_hybrid_height_coordinate"

        if len(dimvals) == 4:
            ntimes, nlev, nlats, nlons = [len(dimvals[i][1]) for i in range(4)]
            dims = [self.dimensions[dimvals[i][0]][0] for i in range(4)]
            levels = dimvals[1][1]
            if leveltype == "pl":
                levels *= 100
        elif len(dimvals) == 3:
            ntimes, nlats, nlons = [len(dimvals[i][1]) for i in range(3)]
            dims = [self.dimensions[dimvals[i][0]][0] for i in range(3)]
        else:
            raise RuntimeError

        for standard_name in variables:
            newvar = ecmwf.createVariable(standard_name, 'f4', dims)
            newvar.standard_name = standard_name
            if len(dimvals) == 4:
                test_data, unit = generate_field(coordinate, levels, standard_name, ntimes, nlats, nlons)
            elif coordinate is None:
                test_data, unit = generate_surface(standard_name, ntimes, nlats, nlons)
            else:
                test_data, unit = generate_field(coordinate[0], [coordinate[1]], standard_name, ntimes, nlats, nlons)
                test_data = test_data[:, 0, :, :]
            newvar.units = unit
            newvar[:] = test_data
            newvar.grid_mapping = 'LatLon_Projection'
            newvar.missing_value = float('nan')

        ecmwf.close()

    def create_data(self):
        """
        Method to generate all required model data for testing purposes.
        """
        times, lats, lons = np.arange(0, 39, 6), np.arange(70, 30, -1), np.arange(-50, 50)

        for coordinate, label, levtype, coord_levels, variables in (
                ("air_pressure", "PRESSURE_LEVELS", "pl",
                 ("atmosphere_pressure_coordinate",
                  np.array([30, 50, 70, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900])),
                 ["air_potential_temperature", "air_pressure", "air_temperature",
                  "eastward_wind", "ertel_potential_vorticity", "geopotential_height",
                  "northward_wind", "specific_humidity", "lagrangian_tendency_of_air_pressure", "divergence_of_wind",
                  "mass_fraction_of_ozone_in_air", "mole_fraction_of_ozone_in_air", "equivalent_latitude",
                  "number_of_wcb_trajectories", "number_of_insitu_trajectories", "number_of_mix_trajectories"]),

                ("ertel_potential_vorticity", "PVU", "pv",
                 ("atmosphere_ertel_potential_vorticity_coordinate", [2, 2.5, 3, 3.5, 4]),
                 ["air_potential_temperature", "geopotential_height", "air_pressure"]),

                ("geopotential_height", "ALTITUDE_LEVELS", "al",
                 ("atmosphere_altitude_coordinate", np.arange(5000, 15001, 500)),
                 ["air_pressure", "ertel_potential_vorticity", "mole_fraction_of_ozone_in_air"]),

                ("air_potential_temperature", "THETA_LEVELS", "tl",
                 ("atmosphere_potential_temperature_coordinate", np.arange(300, 460, 20)),
                 ["air_pressure", "ertel_potential_vorticity", "mole_fraction_of_ozone_in_air"])):
            self.generate_file(
                coordinate, label, levtype,
                (("time", times), coord_levels, ("latitude", lats), ("longitude", lons)), variables)

        for varname, standard_name in (
                ("P_derived", "air_pressure"),
                ("PV_derived", "ertel_potential_vorticity"),
                ("CC", "cloud_area_fraction_in_atmosphere_layer"),
                ("CLWC", "specific_cloud_liquid_water_content"),
                ("CIWC", "specific_cloud_ice_water_content"),
                ("EMAC", "emac_R12"),
                ("ProbWCB_LAGRANTO_derived", "probability_of_wcb_occurrence"),
                ("T", "air_temperature"),
                ("U", "eastward_wind"),
                ("V", "northward_wind"),
                ("W", "lagrangian_tendency_of_air_pressure"),
                ("Q", "specific_humidity")):
            self.generate_file(
                "hybrid", varname, "ml",
                (("time", times), ("hybrid", np.arange(0, 18)), ("latitude", lats), ("longitude", lons)),
                [standard_name])

        self.generate_file(
            None, "SFC", "sfc", (("time", times), ("latitude", lats), ("longitude", lons)),
            [_x for _x in _SURFACE.keys() if _x not in [
                "vertically_integrated_probability_of_wcb_occurrence", "solar_elevation_angle"]])
        self.generate_file(
            None, "ProbWCB_LAGRANTO_derived", "sfc", (("time", times), ("latitude", lats), ("longitude", lons)),
            ["vertically_integrated_probability_of_wcb_occurrence"])
        self.generate_file(
            None, "SEA", "sfc", (("time", times), ("latitude", lats), ("longitude", lons)), ["solar_elevation_angle"])


def main():
    """
    creates various test data files and also the server configuration
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)
    parser.add_argument("-s", "--seed", help="creates demodata for the mswms server",
                        action="store_true", default=False)
    args = parser.parse_args()
    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()
    if args.seed:
        root_fs = fs.open_fs("~/")
        if not root_fs.exists("mss/testdata"):
            root_fs.makedirs("mss/testdata")

        examples = DataFiles(data_fs=fs.open_fs("~/mss/testdata"),
                             server_config_fs=fs.open_fs("~/mss"))
        examples.create_server_config(detailed_information=True)
        examples.create_data()
        print("\nTo use this setup you need the mss_wms_settings.py in your python path e.g. \nexport PYTHONPATH=~/mss")


if __name__ == '__main__':
    main()
