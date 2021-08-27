# -*- coding: utf-8 -*-
"""

    mslib.utils.units
    ~~~~~~~~~~~~~~

    Collection of unit conversion related routines for the Mission Support System.

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

import logging

from metpy.units import units, check_units  # noqa
import pint

units.define("PVU = m^2 s^-1 uK kg^-1")
units.define("degrees_south = -degrees = degrees_S = degreesS = degree_south = degree_S = degreeS")
units.define("degrees_west = -degrees = degrees_W = degreesW = degree_west = degree_W = degreeW")

# Follow metpy 1.0.1 style of defining dimensionless units
for _name, _factor in (("level", 1),
                       ("sigma", 1),
                       ("permille", 1e-3),
                       ("ppm", 1e-6),
                       ("ppmv", 1e-6),
                       ("ppb", 1e-9),
                       ("ppbv", 1e-9),
                       ("ppt", 1e-12),
                       ("pptv", 1e-12)):
    units.define(pint.unit.UnitDefinition(_name, '', (),
                 pint.converters.ScaleConverter(_factor)))


def convert_to(value, from_unit, to_unit, default=1.):
    try:
        value_unit = units.Quantity(value, from_unit)
        result = value_unit.to(to_unit).magnitude
    except pint.UndefinedUnitError:
        logging.error("Error in unit conversion (undefined) '%s'/'%s'", from_unit, to_unit)
        result = value * default
    except pint.DimensionalityError:
        if units(to_unit).to_base_units().units == units.m:
            try:
                result = (value_unit / units.Quantity(9.81, "m s^-2")).to(to_unit).magnitude
            except pint.DimensionalityError:
                logging.error("Error in unit conversion (dimensionality) %s/%s", from_unit, to_unit)
                result = value * default
        else:
            logging.error("Error in unit conversion (dimensionality) %s/%s", from_unit, to_unit)
            result = value * default
    return result
