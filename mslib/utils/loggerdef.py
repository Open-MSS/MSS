# logging_config.py
import logging


def configure_mpl_logger():
    mpl_logger = logging.getLogger('matplotlib')
    mpl_logger.setLevel(logging.INFO)
    return mpl_logger
