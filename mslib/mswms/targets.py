
TARGETS = [
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

UNITS = {
    "air_temperature": ("K", 1),
    "eastward_wind": ("ms$^{-1}$", 1),
    "equivalent_latitude": ("degree N", 1),
    "ertel_potential_vorticity": ("PVU", 1),
    "mean_age_of_air": ("month", 1),
    "northward_wind": ("ms$^{-1}$", 1),
    "square_of_brunt_vaisala_frequency_in_air": ("s${^-2}$", 1),
}

for ent in TARGETS:
    if ent.startswith("surface_origin_tracer_from_"):
        UNITS[ent] = ("%", 1)

for ent in [
        "mole_fraction_of_methane_in_air",
        "mole_fraction_of_ozone_in_air",
        "mole_fraction_of_water_vapor_in_air",
        ]:
    UNITS[ent] = ("$\mu$mol mol$^{-1}$", 1)

for ent in [
        "mole_fraction_of_cfc11_in_air",
        "mole_fraction_of_cfc12_vapor_in_air",
        ]:
    UNITS[ent] = ("pmol mol$^{-1}$", 1)


def get_unit(target):
    return UNITS.get(target, (None, 1))


def get_range(target, level=None, type="pl"):
    if target.startswith("surface_origin_tracer_from_"):
        return 0, 100
    return None, None
