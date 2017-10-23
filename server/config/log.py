import copy
import os
from logging import config as logging_config


DEFAULT_LOGGING_PATH = './log'


logging_config_template = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'file_formatter': {
            'format': '%(asctime)s [%(levelname)4s] [%(threadName)s] [%(module)12s] %(message)s'
        },
        'console_formater': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'base_handler': {
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'backupCount': 5,
            'interval': 1,
            'filename': DEFAULT_LOGGING_PATH + '/mess.log',
            'formatter': 'file_formatter'
        },
        'debug_console_handler': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'console_formater'
        },

    },
    'loggers': {
    },
    'root': {
            'handlers': ['debug_console_handler', 'base_handler'],
            'level': 'INFO',
    },
}


def build_config_dict(log_file_path):
    config = copy.deepcopy(logging_config_template)
    config['handlers']['base_handler']['filename'] = log_file_path + '/mess.log'
    return config


def configure_logging(log_path=None):
    print("Log file path: {path}".format(path=log_path))
    if not log_path:
        log_path = DEFAULT_LOGGING_PATH
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    logging_config.dictConfig(build_config_dict(log_path))
