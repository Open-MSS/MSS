# mslib/utils/view_restoration.py
import json
import logging
from pathlib import Path
from mslib.msui import constants

def save_view_settings(settings: dict):
    try:
        config_path = Path(constants.MSUI_CONFIG_PATH)
        config_path.mkdir(parents=True, exist_ok=True)
        save_path = config_path / "view_settings.json"
        with open(save_path, "w") as f:
            json.dump(settings, f, indent=4)
        logging.info("Saved top view settings to %s", save_path)
    except Exception as e:
        logging.error("Failed to save top view settings: %s", e)

