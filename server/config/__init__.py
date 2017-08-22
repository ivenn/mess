import os
from logging import config as logging_config
from .log import LOGGING, LOGGING_PATH


def configure_logging():
    if not os.path.exists(LOGGING_PATH):
        os.makedirs(LOGGING_PATH)
    logging_config.dictConfig(LOGGING)
