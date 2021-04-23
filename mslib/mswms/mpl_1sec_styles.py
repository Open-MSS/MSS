from mslib.mswms.mpl_1sec import Abstract1DSectionStyle
import mslib.thermolib as thermolib


class OS_TemperatureStyle_01(Abstract1DSectionStyle):
    """
    Temperature
    Vertical section of temperature.
    """

    name = "OS_T01"
    title = "Temperature (K) 1D Section"
    abstract = "Temperature (K) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])

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
    Vertical sections of relative humidity.
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
        Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes relative humdity.
        """
        self.data["relative_humidity"] = thermolib.rel_hum(
            self.data['air_pressure'], self.data["air_temperature"],
            self.data["specific_humidity"])

    def _plot_style(self):
        """
        Make a temperature 1D section.
        """
        ax = self.ax
        self.y_values = self.data["specific_humidity"]

        numpoints = len(self.lats)
        ax.plot(range(numpoints), self.y_values)
        self._latlon_setup()
