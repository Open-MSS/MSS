
class Targets(object):
    """This class defines the names, units, and ranges of supported generic physical
       quantities for vertical and horizontal plots.
    """

    _TARGETS = [
        "air_temperature",
        "eastward_wind",
        "equivalent_latitude",
        "ertel_potential_vorticity",
        "mean_age_of_air",
        "mole_fraction_of_carbon_monoxide_in_air",
        "mole_fraction_of_cfc11_in_air",
        "mole_fraction_of_cfc12_in_air",
        "mole_fraction_of_formaldehyde_in_air",
        "mole_fraction_of_methane_in_air",
        "mole_fraction_of_nitric_acid_in_air",
        "mole_fraction_of_nitrous_oxide_in_air",
        "mole_fraction_of_nitrogen_dioxide_in_air",
        "mole_fraction_of_nitrogen_monoxide_in_air",
        "mole_fraction_of_ozone_in_air",
        "mole_fraction_of_peroxyacetyl_nitrate_in_air",
        "mole_fraction_of_sulfur_dioxide_in_air",
        "mole_fraction_of_water_vapor_in_air",
        "northward_wind",
        "square_of_brunt_vaisala_frequency_in_air",
        "surface_origin_tracer_from_southeast_asia",
        "surface_origin_tracer_from_east_china",
        "surface_origin_tracer_from_north_india",
        "surface_origin_tracer_from_south_india",
        "surface_origin_tracer_from_india_and_china",
        ]

    _UNITS = {
        "air_temperature": ("K", 1),
        "eastward_wind": ("ms$^{-1}$", 1),
        "equivalent_latitude": ("degree N", 1),
        "ertel_potential_vorticity": ("PVU", 1),
        "mean_age_of_air": ("month", 1),
        "northward_wind": ("ms$^{-1}$", 1),
        "square_of_brunt_vaisala_frequency_in_air": ("s${^-2}$", 1),
    }

    _THRESHOLDS = {
        "mole_fraction_of_ozone_in_air":
            (0, 0.05, 0.1, 0.13, 0.15, 0.190, 0.23, 0.3, 0.4, 0.75, 2., 6.),
        "mole_fraction_of_water_vapor_in_air":
            (0, 3, 4, 5, 6, 8, 10, 14, 20, 40, 60, 100, 150, 250, 500),
        "mole_fraction_of_peroxyacetyl_nitrate_in_air":
            (0, 50, 70, 100, 150, 200, 250, 300, 350, 400, 450, 500),
        "mole_fraction_of_nitric_acid_in_air":
            (0.0, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 2, 4)
    }

    for ent in _TARGETS:
        if ent.startswith("surface_origin_tracer_from_"):
            _UNITS[ent] = ("%", 1)

    for ent in [
            "mole_fraction_of_methane_in_air",
            "mole_fraction_of_ozone_in_air",
            "mole_fraction_of_water_vapor_in_air",
            ]:
        _UNITS[ent] = ("$\mu$mol mol$^{-1}$", 1e6)

    for ent in [
            ]:
        _UNITS[ent] = ("nmol mol$^{-1}$", 1e9)

    for ent in [
            "mole_fraction_of_cfc11_in_air",
            "mole_fraction_of_cfc12_vapor_in_air",
            ]:
        _UNITS[ent] = ("pmol mol$^{-1}$", 1e12)

    @staticmethod
    def get_targets():
        """
        List to determine what targets are supported.
        Returns:
        list of supported targets
        """
        return Targets._TARGETS

    @staticmethod
    def get_unit(target):
        """
        Returns unit type and scaling factor for target.
        Args:
            target: string of CF standard_name

        Returns:
            Tuple of string descring the unit and scaling factor to apply on data.

        """
        return Targets._UNITS.get(target, (None, 1))

    @staticmethod
    def get_range(target, level=None, type=None):
        """
        Returns valid range of values for target at given level
        Args:
            target: string of CF standard_name
            level (optional): horizontal level of data
            type (optional): type of data (pl, ml, tl, ...)

        Returns:
            Tuple of lowest and highest valid value
        """
        if target.startswith("surface_origin_tracer_from_"):
            return 0, 100
        return None, None

    @staticmethod
    def get_thresholds(target, level=None, type=None):
        """
        Returns a list of meaningful values for a BoundaryNorm for plotting.
        Args:
            target: string of CF standard_name
            level (optional): horizontal level of data
            type (optional): type of data (pl, ml, tl, ...)

        Returns:
            Tuple of threshold values to be supplied to a BoundaryNorm.
        """
        return Targets._THRESHOLDS.get(target, None)
