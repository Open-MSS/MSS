import numpy as np

from mslib.mswms.mpl_1sec import Abstract1DSectionStyle
import mslib.thermolib as thermolib
from mslib.utils import convert_to


class OS_TemperatureStyle_01(Abstract1DSectionStyle):
    """
    1D section of temperature.
    """

    name = "OS_T01"
    title = "Temperature (K) 1D Section"
    abstract = "Temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K")]

    def _plot_style(self):
        """
        Make a temperature 1D section.
        """
        ax = self.ax
        self.y_values = self.data["air_temperature"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()


class OS_RelativeHumdityStyle_01(Abstract1DSectionStyle):
    """
    1D section of relative humidity.
    """

    name = "OS_RH01"
    title = "Relative Humdity (%) 1D Section"
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

    def _plot_style(self):
        ax = self.ax
        self.y_values = self.data["specific_humidity"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()


class OS_CloudsStyle_01(Abstract1DSectionStyle):
    """
    1D section of cloud cover.
    """

    name = "OS_CC01"
    title = "Cloud Cover (0-1) 1D Section"
    abstract = "Cloud cover (0-1)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "cloud_area_fraction_in_atmosphere_layer", 'dimensionless')]

    def _plot_style(self):
        ax = self.ax
        self.y_values = self.data["cloud_area_fraction_in_atmosphere_layer"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()


class OS_SpecificHumdityStyle_01(Abstract1DSectionStyle):
    """
    1D section of specific humidity.
    """

    name = "OS_Q01"
    title = "Specific Humdity (g/kg) 1D Section"
    abstract = "Specific humdity (g/kg)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "specific_humidity", "g/kg")]

    def _plot_style(self):
        ax = self.ax
        self.y_values = self.data["specific_humidity"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()


class OS_VerticalVelocityStyle_01(Abstract1DSectionStyle):
    """
    1D section of vertical velocity.
    """

    name = "OS_W01"
    title = "Vertical Velocity (cm/s) 1D Section"
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

    def _plot_style(self):
        ax = self.ax
        self.y_values = self.data["upward_wind"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()


class OS_HorizontalVelocityStyle_01(Abstract1DSectionStyle):
    """
    1D section of horizontal velocity.
    """

    name = "OS_HV01"
    title = "Horizontal Wind (m/s) 1D Section"
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

    def _plot_style(self):
        ax = self.ax
        self.y_values = self.data["horizontal_wind"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()


class OS_PotentialVorticityStyle_01(Abstract1DSectionStyle):
    """
    1D section of potential vorticity.
    """

    name = "OS_PV01"
    title = "Potential Vorticity (PVU) 1D Section"
    abstract = "(Neg.) Potential vorticity (PVU)"
    styles = [
        ("default", "Northern Hemisphere"),
        ("NH", "Northern Hemisphere"),
        ("SH", "Southern Hemisphere, neg. PVU")]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "ertel_potential_vorticity", "PVU")]

    def _plot_style(self):
        ax = self.ax
        self.y_values = self.data["ertel_potential_vorticity"]

        # Change PV sign on southern hemisphere.
        if self.style.lower() == "default":
            self.style = "NH"
        if self.style.upper() == "SH":
            self.y_values = -self.y_values

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()
