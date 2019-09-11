# -*- coding: utf-8 -*-
"""

    mslib.mswms.mss_2D_sections
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    2D cross-section style super classes for use with the
    MSSPlotDriver subclasses.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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
from abc import ABCMeta, abstractmethod


class Abstract2DSectionStyle(metaclass=ABCMeta):
    """
    Horizontal Section Styles
    Abstract 2D section super class. Use this class as a parent
    for classes implementing horizontal and vertical cross sections.
    """

    # Name and title of each derived style have to be defined if the style
    # should be used with the WMS WSGI module.
    name = None
    title = None
    abstract = None
    queryable = False
    styles = None

    # Define the datafields required by a style with this property.
    required_datafields = []

    def __init__(self, driver=None):
        self.set_driver(driver)
        self.required_datatypes()

    def required_datatypes(self):
        """Returns a list containing the datatypes required by the
           data fields requested by the style.
        """
        result = set([datafield[0] for datafield in self.required_datafields])
        if len(result) > 1 and "sfc" not in result:
            msg = "A Plot may contain only 'sfc' and *one* 4-D type! ({}: {})".format(type(self), result)
            logging.fatal(msg)
            raise RuntimeError(msg)
        elif len(result) == 2:
            self._vert_type = [_x for _x in result if _x != "sfc"][0]
        elif len(result) == 1:
            self._vert_type = list(result)[0]
        else:
            self._vert_type = None
        return result

    def _prepare_datafields(self):
        """Optional re-implementation: Use this function to process some
           input data before the plotting starts (e.g. to derive potential
           temperature from pressure and temperature).
        """
        pass

    def supported_epsg_codes(self):
        """Returns a list of supported EPSG codes, if available.
        """
        return []

    @abstractmethod
    def supported_crs(self):
        """Returns a list of the coordinate reference systems supported by
           this style.
        """
        pass

    def set_driver(self, driver):
        """Set the driver object for this layer.
        """
        self.driver = driver

    def get_init_times(self):
        """Returns a list of available forecast init times (base times).
        """
        if self.uses_inittime_dimension() and self.driver is not None:
            return self.driver.get_init_times()
        else:
            return []

    def get_all_valid_times(self):
        """Returns a list containing the combined forecast valid times of
           all available init times.
        """
        if self.uses_validtime_dimension() and self.driver is not None:
            valid_times = set()
            for vartype, varname, _ in self.required_datafields:
                vtimes = self.driver.get_all_valid_times(varname, vartype)
                if len(valid_times) == 0:
                    valid_times.update(vtimes)
                else:
                    valid_times.intersection_update(vtimes)
            valid_times = sorted(valid_times)
            return valid_times
        else:
            return []

    def uses_elevation_dimension(self):
        """Returns whether this layer uses the WMS elevation dimension. If False,
           elevation does not have to be specified to plot_hsection().
        """
        return self._vert_type != "sfc"

    def uses_inittime_dimension(self):
        """Returns whether this layer uses the WMS inittime dimension. If False,
           init_time does not have to be specified to plot_hsection().

        Currently redirected to check for valid_time.
        """
        return self.driver.uses_validtime_dimension() if self.driver is not None else False

    def uses_validtime_dimension(self):
        """Returns whether this layer uses the WMS time dimension. If False,
           valid_time does not have to be specified to
           plot_hsection().

        Currently implemented by testing whether the style requires data fields
        from the ECMWF forecast.
        """
        return self.driver.uses_inittime_dimension() if self.driver is not None else False

    def get_elevations(self):
        """Returns a list of available elevations for this layer.

        Assumes that the same elevation levels are available for all time
        steps.
        """
        logging.debug(u"checking vertical dimensions for layer '%s'.", self.name)
        if self.uses_elevation_dimension() and self.driver is not None:
            return [str(x) for x in self.driver.get_elevations(self._vert_type)]
        else:
            return []

    def get_elevation_units(self):
        """Returns the units of the elevation values.
        """
        if self.driver is not None:
            return self.driver.get_elevation_units(self._vert_type)
        else:
            return ""
