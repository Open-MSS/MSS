import pytest
from mslib.utils.config import(
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
        assert MSUIDefaultConfig.MSCOLAB_timeout == (2,10)

    def test_config_loader(self):
        timeout = config_loader(dataset="MSCOLAB_timeout")
        assert isinstance(timeout, tuple)
        assert timeout == (2,10)
        timeout = config_loader(dataset="MSCOLAB_timeout", default=False)
        assert isinstance(timeout, tuple)
        assert timeout == (2,10)

    def test_default_options(self):
        config = default_options
        assert isinstance(config, dict)
        assert "MSCOLAB_timeout" in config
        assert config["MSCOLAB_timeout"] == (2,10)

    def test_merge_dict(self):
        current ={"MSCOLAB_timeout": (2,10)}
        new = {"MSCOLAB_timeout": [5,15]}
        merged = merge_dict(current, new)
        assert isinstance(merged["MSCOLAB_timeout"], tuple)
        assert len(merged["MSCOLAB_timeout"]) == 2
        assert merged["MSCOLAB_timeout"] == (5,15)

    def test_merge_dict_valid_tuple(self):
        current = {"MSCOLAB_timeout": (1, 5)}
        new = {"MSCOLAB_timeout": (8, 12)}
        merged = merge_dict(current, new)
        assert merged["MSCOLAB_timeout"] == (8, 12)

    def test_merge_dict_invalid_type(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": 5})

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

    def test_merge_dict_string_input(self):
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": "2,10"})
        with pytest.raises(ValueError):
            merge_dict({}, {"MSCOLAB_timeout": "5, 15"})
    
