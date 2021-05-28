# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_lsec_styles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Matplotlib linear section styles.

    This file is part of mss.

    :copyright: Copyright 2021 May Baer
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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

import numpy as np

from mslib.mswms.mpl_lsec import AbstractLinearSectionStyle
import mslib.thermolib as thermolib
from mslib.utils import convert_to


class LS_DefaultStyle(AbstractLinearSectionStyle):
    """
    Style for single variables that require no further calculation
    """
    def __init__(self, driver, variable="air_temperature"):
        super(AbstractLinearSectionStyle, self).__init__(driver=driver)
        self.variable = variable
        self.required_datafields = [("ml", "air_pressure", "Pa"), ("ml", self.variable, None)]
        abbreviation = "".join([text[0] for text in self.variable.split("_")])
        self.name = f"LS_{str.upper(abbreviation)}"
        self.title = f"{self.variable} Linear Plot"
        self.abstract = f"{self.variable}"


class LS_RelativeHumdityStyle_01(AbstractLinearSectionStyle):
    """
    Linear plot of relative humidity.
    """

    name = "LS_RH01"
    title = "Relative Humdity (%) Linear Plot"
    abstract = "Relative humdity (%)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "specific_humidity", "kg/kg")]

    def _prepare_datafields(self):
        """
        Computes relative humdity.
        """
        self.data["relative_humidity"] = thermolib.rel_hum(
            self.data['air_pressure'], self.data["air_temperature"],
            self.data["specific_humidity"])
        self.variable = "relative_humidity"
        self.y_values = self.data[self.variable]
        self.unit = "%"


class LS_VerticalVelocityStyle_01(AbstractLinearSectionStyle):
    """
    Linear plot of vertical velocity.
    """

    name = "LS_W01"
    title = "Vertical Velocity (cm/s) Linear Plot"
    abstract = "Vertical velocity (cm/s)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "lagrangian_tendency_of_air_pressure", "Pa/s")]

    def _prepare_datafields(self):
        """
        Computes vertical velocity in cm/s.
        """
        self.data["upward_wind"] = convert_to(
            thermolib.omega_to_w(self.data["lagrangian_tendency_of_air_pressure"],
                                 self.data['air_pressure'], self.data["air_temperature"]),
            "m/s", "cm/s")
        self.variable = "upward_wind"
        self.y_values = self.data[self.variable]
        self.unit = "cm/s"


class LS_HorizontalVelocityStyle_01(AbstractLinearSectionStyle):
    """
    Linear plot of horizontal velocity.
    """

    name = "LS_HV01"
    title = "Horizontal Wind (m/s) Linear Plot"
    abstract = "Horizontal wind speed (m/s)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "eastward_wind", "m/s"),
        ("ml", "northward_wind", "m/s")]

    def _prepare_datafields(self):
        """
        Computes total horizontal wind speed.
        """
        self.data["horizontal_wind"] = np.hypot(
            self.data["eastward_wind"], self.data["northward_wind"])
        self.variable = "horizontal_wind"
        self.y_values = self.data[self.variable]
        self.unit = "m/s"
