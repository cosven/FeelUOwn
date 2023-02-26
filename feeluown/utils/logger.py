import logging
import logging.config


dict_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': ("[%(asctime)s %(name)s:%(lineno)d] "
                       "[%(levelname)s]: %(message)s"),
        },
        'thread': {
            'format': ("[%(asctime)s %(name)s:%(lineno)d %(thread)d] "
                       "[%(levelname)s]: %(message)s"),
        },
    },
    'handlers': {},
    'loggers': {},
}


def configure_global_logger(verbose=1, to_file=None):
    """configure logger

    :param to_file: log filepath
    :param verbose: verbose level.
                    0: show all (>=)warning level log
                    1: show all info level log
                    2: show feeluown debug level log and all info log
                    3: show all debug log
    """
    handler = {'level': 'DEBUG', 'formatter': 'standard'}
    logger = {
        'handlers': [''],
        'propagate': True,
    }

    dict_config['handlers'][''] = handler
    dict_config['loggers'][''] = logger

    if to_file:
        handler.update({
            'class': 'logging.FileHandler',
            'filename': to_file,
            'mode': 'w'
        })
        verbose = max(1, verbose)
    else:
        handler.update({'class': 'logging.StreamHandler'})

    if verbose <= 0:
        handler['level'] = 'WARNING'
        logger['level'] = logging.WARNING
    elif verbose <= 1:
        handler['level'] = 'INFO'
        logger['level'] = logging.INFO
    else:
        handler['level'] = 'DEBUG'
        logger['level'] = logging.INFO
        if verbose >= 3:
            logger['level'] = logging.DEBUG
        else:
            # set logger for feeluown
            fuo_logger = {
                'handlers': [''],
                'level': logging.DEBUG,
                'propagate': False,
            }
            dict_config['loggers']['feeluown'] = fuo_logger

    logging.config.dictConfig(dict_config)
