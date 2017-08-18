LOGGING_PATH = './logs'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'file_formatter': {
            'format': '%(asctime)s [%(levelname)4s] [%(threadName)s] %(module)s %(message)s'
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
            'filename': LOGGING_PATH + '/mess.log',
            'formatter': 'file_formatter'
        },
        'debug_console_handler': {
            'class':'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'console_formater'
        },

    },
    'loggers': {
    },
    'root': {
            'handlers': ['debug_console_handler', 'base_handler'],
            'level':'INFO',
    },
}
