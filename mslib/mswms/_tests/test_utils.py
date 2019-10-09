from mslib.mswms.utils import Targets


def test_targets():
    for standard_name in Targets.get_targets():
        Targets.get_unit(standard_name)
        Targets.get_range(standard_name)
        Targets.get_thresholds(standard_name)
        Targets.get_range(standard_name)
        Targets.UNITS[standard_name]
        Targets.TITLES[standard_name]
