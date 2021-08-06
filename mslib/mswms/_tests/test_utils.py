from mslib.utils.units import units
from mslib.mswms.utils import Targets


def test_targets():
    for standard_name in Targets.get_targets():
        unit = Targets.get_unit(standard_name)
        units(unit[0])  # ensure that the unit may be parsed
        assert unit[1] == 1  # no conversion outside pint!
        Targets.get_range(standard_name)
        Targets.get_thresholds(standard_name)
        Targets.get_range(standard_name)
        Targets.UNITS[standard_name]
        Targets.TITLES[standard_name]
