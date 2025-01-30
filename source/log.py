import logging
import logging.config
import os
from source.config import Config


def setup_logging(log_filename: str):
    """
    Настройка логирования с использованием dictConfig.
    :param log_filename: Имя файла для записи логов.
    """
    log_dir = Config.LOGS_DIR

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = os.path.join(log_dir, log_filename)

    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'generic': {
                'format': '{asctime} [{levelname}] [{name:^16}] {message}',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'generic',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'generic',
                'filename': log_path,
                'mode': 'a',
                'maxBytes': 10485760,
                'backupCount': 5,
            },
        },
        'loggers': {
            'root': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
            },
        },
    }

    logging.config.dictConfig(log_config)