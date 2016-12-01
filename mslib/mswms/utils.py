import numpy as np

N_LEVELS = 16

class Targets(object):
    """This class defines the names, units, and ranges of supported generic physical
       quantities for vertical and horizontal plots.

       RANGES, UNITS, and THRESHOLDS can be overwritten from outside to determine ranges for plotting in settings.
    """

    """Dictionary containing valid value ranges for the different targes. The first level uses CF standard_name as key
       to determine the target. The second level uses either the level type
       ("pl", "ml", ...) as key or "total" for the level-overarching valid range. The level-type has a third level
       using the level altitude as key. The leafs are made of 2-tuples indicating the lowest and the highest valid
       value.
    """
    RANGES = {}

    """List of supported targets using the CF standard_name as unique identifier."""
    _TARGETS = [
        "air_temperature",
        "eastward_wind",
        "equivalent_latitude",
        "ertel_potential_vorticity",
        "mean_age_of_air",
        "mole_fraction_of_carbon_monoxide_in_air",
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_carbon_tetrachloride_in_air",
        "mole_fraction_of_chlorine_nitrate_in_air",
        "mole_fraction_of_cfc11_in_air",
        "mole_fraction_of_cfc113_in_air",
        "mole_fraction_of_cfc12_in_air",
        "mole_fraction_of_ethane_in_air",
        "mole_fraction_of_formaldehyde_in_air",
        "mole_fraction_of_hcfc22_in_air",
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
        "surface_origin_tracer_from_india_and_china",
        "surface_origin_tracer_from_southeast_asia",
        "surface_origin_tracer_from_east_china",
        "surface_origin_tracer_from_north_india",
        "surface_origin_tracer_from_south_india",
        "surface_origin_tracer_from_north_africa",
        "median_of_age_of_air_spectrum",
        "fraction_below_6months_of_age_of_air_spectrum",
        "fraction_above_24months_of_age_of_air_spectrum",
    ]

    UNITS = {
        "air_temperature": ("K", 1),
        "eastward_wind": ("ms$^{-1}$", 1),
        "equivalent_latitude": ("degree N", 1),
        "ertel_potential_vorticity": ("PVU", 1),
        "mean_age_of_air": ("month", 1),
        "northward_wind": ("ms$^{-1}$", 1),
        "square_of_brunt_vaisala_frequency_in_air": ("s${^-2}$", 1),
    }

    """The THRESHOLDS are used to determine a single colourmap suitable for all plotting purposes (that is vertical
       and horizontal on all levels. The given thresholds have been manually designed.
    """
    THRESHOLDS = {
        "ertel_potential_vorticity":
            (-1, 0, 1, 2, 4, 6, 9, 12, 15, 25, 40),
        "mole_fraction_of_carbon_monoxide_in_air":
            (10e-9, 20e-9, 30e-9, 40e-9, 50e-9, 60e-9, 70e-9, 80e-9, 90e-9, 100e-9, 300e-9),
        "mole_fraction_of_nitric_acid_in_air":
            (0e-9, 0.3e-9, 0.5e-9, 0.7e-9, 0.9e-9, 1.1e-9, 1.3e-9, 1.5e-9, 2e-9, 4e-9),
        "mole_fraction_of_ozone_in_air":
            (0e-6, 0.02e-6, 0.03e-6, 0.04e-6, 0.06e-6, 0.1e-6, 0.16e-6, 0.25e-6, 0.45e-6, 1e-6, 4e-6),
        "mole_fraction_of_peroxyacetyl_nitrate_in_air":
            (0, 50e-12, 70e-12, 100e-12, 150e-12, 200e-12, 250e-12, 300e-12, 350e-12, 400e-12, 450e-12, 500e-12),
        "mole_fraction_of_water_vapor_in_air":
            (0, 3e-6, 4e-6, 6e-6, 10e-6, 16e-6, 60e-6, 150e-6, 500e-6, 1000e-6),
    }

    for standard_name in _TARGETS:
        if standard_name.startswith("surface_origin_tracer_from_"):
            UNITS[standard_name] = ("%", 1)

    for standard_name in [
            "mole_fraction_of_methane_in_air",
            "mole_fraction_of_ozone_in_air",
            "mole_fraction_of_water_vapor_in_air",
    ]:
        UNITS[standard_name] = ("$\mu$mol mol$^{-1}$", 1e6)

    for standard_name in [
            "mole_fraction_of_carbon_monoxide_in_air",
            "mole_fraction_of_chlorine_nitrate_in_air",
            "mole_fraction_of_nitric_acid_in_air",
            "mole_fraction_of_nitrous_oxide_in_air",
    ]:
        UNITS[standard_name] = ("nmol mol$^{-1}$", 1e9)

    for standard_name in [
            "mole_fraction_of_carbon_tetrachloride_in_air",
            "mole_fraction_of_cfc11_in_air",
            "mole_fraction_of_cfc12_in_air",
            "mole_fraction_of_ethane_in_air",
            "mole_fraction_of_formaldehyde_in_air",
            "mole_fraction_of_nitrogen_dioxide_in_air",
            "mole_fraction_of_nitrogen_monoxide_in_air",
            "mole_fraction_of_peroxyacetyl_nitrate_in_air",
            "mole_fraction_of_sulfur_dioxide_in_air",
    ]:
        UNITS[standard_name] = ("pmol mol$^{-1}$", 1e12)

    for standard_name in [
            "fraction_below_6months_of_age_of_air_spectrum",
            "fraction_above_24months_of_age_of_air_spectrum",
    ]:
        UNITS[standard_name] = ("%", 100)

    @staticmethod
    def get_targets():
        """
        List to determine what targets are supported.
        Returns:
        list of supported targets
        """
        return Targets._TARGETS

    @staticmethod
    def get_unit(standard_name):
        """
        Returns unit type and scaling factor for target.
        Args:
            standard_name: string of CF standard_name

        Returns:
            Tuple of string describing the unit and scaling factor to apply on data.

        """
        return Targets.UNITS.get(standard_name, (None, 1))

    @staticmethod
    def get_range(standard_name, level="total", type=None):
        """
        Returns valid range of values for target at given level
        Args:
            standard_name: string of CF standard_name
            level (optional): horizontal level of data
            type (optional): type of data (pl, ml, tl, ...)

        Returns:
            Tuple of lowest and highest valid value
        """
        if standard_name in Targets.RANGES:
            if type in Targets.RANGES[standard_name]:
                if level in Targets.RANGES[standard_name][type]:
                    return [_x * Targets.get_unit(standard_name)[1]
                            for _x in Targets.RANGES[standard_name][type][level]]
                elif level is None:
                    return 0, 0
            if level == "total" and "total" in Targets.RANGES[standard_name]:
                return [_x * Targets.get_unit(standard_name)[1]
                        for _x in Targets.RANGES[standard_name]["total"]]
        if standard_name.startswith("surface_origin_tracer_from_"):
            return 0, 100
        return None, None

    @staticmethod
    def get_thresholds(standard_name, level=None, type=None):
        """
        Returns a list of meaningful values for a BoundaryNorm for plotting.
        Args:
            standard_name: string of CF standard_name
            level (optional): horizontal level of data
            type (optional): type of data (pl, ml, tl, ...)

        Returns:
            Tuple of threshold values to be supplied to a BoundaryNorm.
        """
        try:
            return [_x * Targets.get_unit(standard_name)[1] for _x in Targets.THRESHOLDS[standard_name]]
        except KeyError:
            return None


def get_log_levels(cmin, cmax, levels=N_LEVELS):
    """
    Returns 'levels' levels in a lgarithmic spacing. Takes care of ranges crossing zero and starting/ending at zero.
    Args:
        cmin: minimum value
        cmax: maximum value
        levels (optional): number of levels to be generated

    Returns:
        numpy array of values
    """
    assert cmin < cmax
    if cmin >= 0:
        if cmin == 0:
            cmin = 0.001 * cmax
        clev = np.exp(np.linspace(np.log(cmin), np.log(cmax), levels))
    elif cmax <= 0:
        if cmax == 0:
            cmax = 0.001 * cmin
        clev = -np.exp(np.linspace(np.log(-cmin), np.log(-cmax), levels))
    else:
        delta = cmax - cmin
        clevlo = -np.exp(
            np.linspace(np.log(-cmin), np.log(max(-cmin, cmax) * 0.001), max(2, 1 + int(levels * -cmin / delta))))
        clevhi = np.exp(np.linspace(np.log(max(-cmin, cmax) * 0.001), np.log(cmax), max(2, 1 + int(levels * cmax / delta))))
        clev = np.asarray(list(clevlo) + list(clevhi))

    return clev
