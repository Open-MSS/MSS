import numpy as np

from mslib.mswms.mpl_1sec import Abstract1DSectionStyle
import mslib.thermolib as thermolib
from mslib.utils import convert_to


class OS_DefaultStyle(Abstract1DSectionStyle):
    """
    Style for single variables that require no further calculation
    """
    def __init__(self, driver, variable="air_temperature"):
        super(Abstract1DSectionStyle, self).__init__(driver=driver)
        self.variable = variable
        self.required_datafields = [("ml", "air_pressure", "Pa"), ("ml", self.variable, "")]
        abbreviation = "".join([text[0] for text in self.variable.split("_")])
        self.name = f"OS_{str.upper(abbreviation)}"
        self.title = f"{self.variable} 1D Plot"
        self.abstract = f"{self.variable}"

    def _plot_style(self, color):
        """
        Make a simple 1D plot.
        """
        ax = self.ax
        self.y_values = self.data[self.variable]

        numpoints = len(self.lats)
        ax.set_ylabel(self.driver.data_units[self.variable])
        ax.plot(range(numpoints), self.y_values, color.replace("0x", "#"))
        self._latlon_setup()


class OS_RelativeHumdityStyle_01(Abstract1DSectionStyle):
    """
    1D section of relative humidity.
    """

    name = "OS_RH01"
    title = "Relative Humdity (%) 1D Plot"
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

    def _plot_style(self, color):
        ax = self.ax
        self.y_values = self.data["specific_humidity"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values, color.replace("0x", "#"))
        self._latlon_setup()


class OS_VerticalVelocityStyle_01(Abstract1DSectionStyle):
    """
    1D section of vertical velocity.
    """

    name = "OS_W01"
    title = "Vertical Velocity (cm/s) 1D Plot"
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

    def _plot_style(self, color):
        ax = self.ax
        self.y_values = self.data["upward_wind"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values, color.replace("0x", "#"))
        self._latlon_setup()


class OS_HorizontalVelocityStyle_01(Abstract1DSectionStyle):
    """
    1D section of horizontal velocity.
    """

    name = "OS_HV01"
    title = "Horizontal Wind (m/s) 1D Plot"
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

    def _plot_style(self, color):
        ax = self.ax
        self.y_values = self.data["horizontal_wind"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values, color.replace("0x", "#"))
        self._latlon_setup()


class OS_PotentialVorticityStyle_01(Abstract1DSectionStyle):
    """
    1D section of potential vorticity.
    """

    name = "OS_PV01"
    title = "Potential Vorticity (PVU) 1D Plot"
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

    def _plot_style(self, color):
        ax = self.ax
        self.y_values = self.data["ertel_potential_vorticity"]

        # Change PV sign on southern hemisphere.
        if self.style.lower() == "default":
            self.style = "NH"
        if self.style.upper() == "SH":
            self.y_values = -self.y_values

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values, color.replace("0x", "#"))
        self._latlon_setup()
