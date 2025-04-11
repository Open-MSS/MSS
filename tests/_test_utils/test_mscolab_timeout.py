import pytest
from mslib.utils.config import (
    MSUIDefaultConfig,
    config_loader,
    modify_config_file,
    merge_dict,
    default_options
)

class Test_mscolab_timeout_part:
    def test_default_config(self):
        assert hasattr(MSUIDefaultConfig, "MSCOLAB_timeout")
        assert isinstance(MSUIDefaultConfig.MSCOLAB_timeout, tuple)
        assert MSUIDefaultConfig.MSCOLAB_timeout == (2, 10)

    def test_config_loader(self):
        timeout = config_loader(dataset="MSCOLAB_timeout")
        assert isinstance(timeout, tuple)
        assert timeout == (2, 10)
        timeout = config_loader(dataset="MSCOLAB_timeout", default=False)
        assert isinstance(timeout, tuple)
        assert timeout == (2, 10)

    def test_default_options(self):
        config = default_options
        assert isinstance(config, dict)
        assert "MSCOLAB_timeout" in config
        assert config["MSCOLAB_timeout"] == (2, 10)
        
    # def test_merge_dict(self):
    #     current ={"MSCOLAB_timeout": (2,10)}
    #     new = {"MSCOLAB_timeout": [5,15]}
    #     merged = merge_dict(current, new)
    #     assert isinstance(merged["MSCOLAB_timeout"], tuple)
    #     assert len(merged["MSCOLAB_timeout"]) == 2
    #     assert merged["MSCOLAB_timeout"] == (5,15)

    def test_merge_dict_overwrite(self):
        result = merge_dict({"MSCOLAB_timeout": (1, 2)}, {"MSCOLAB_timeout": (3, 4)})
        assert tuple(result["MSCOLAB_timeout"]) == (3, 4)

    def test_merge_dict_valid_tuple(self):
        result = merge_dict({}, {"MSCOLAB_timeout": (8, 12)})
        assert tuple(result["MSCOLAB_timeout"]) == (8, 12)

    def test_merge_dict_invalid_type(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": {3, 4}})

    def test_merge_dict_invalid_length(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": [5]})
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": [5, 10, 15]})

    def test_merge_dict_invalid_elements(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": ["a", "b"]})
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": (2, "a")})

    def test_merge_dict_string_input_valid(self):
        result = merge_dict({}, {"MSCOLAB_timeout": "5, 15"})
        assert tuple(result["MSCOLAB_timeout"]) == (5, 15)

    def test_merge_dict_string_input_invalid(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": "sample,string"})
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": "abc"})

    def test_merge_dict_ignore_invalid_values(self):
        current = {"MSCOLAB_timeout": (1, 5)}
        for invalid in [None, "", [], {}]:
            merged = merge_dict(current.copy(), {"MSCOLAB_timeout": invalid})
            assert tuple(merged["MSCOLAB_timeout"]) == (1, 5)

    def test_merge_dict_float_tuple(self):
        current ={}
        new = {"MSCOLAB_timeout": (8.5, 12.5)}
        result = merge_dict(current, new)
        assert tuple(result["MSCOLAB_timeout"]) == (8, 12)

    def test_merge_dict_too_long_tuple(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": (1, 2, 3, 4)})

    def test_merge_dict_negative_value(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": (-1, 5)})

    def test_merge_dict_order_invalid(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": (10, 2)})

    def test_merge_dict_same_int(self):
        result = merge_dict({}, {"MSCOLAB_timeout": 7})
        assert tuple(result["MSCOLAB_timeout"]) == (7, 7)
