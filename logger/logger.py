# -*- coding: utf-8 -*-
import logging
import logging.config
# for color console
import coloredlogs
# from . import custom_obj_for_logger

coloredlogs.install(isatty=True)
logging.config.fileConfig('logger/logging.conf')
logging.captureWarnings(True)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.ERROR)


def get_logger(name):
    logger = logging.getLogger(name)
    return logger

