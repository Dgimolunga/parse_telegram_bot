# -*- coding: utf-8 -*-
import logging
import data_value as data_value


class SendMsgToAdminHandler(logging.Handler):
    def emit(self, record):
        if data_value.telegram_parse is None:
            return
        data_value.telegram_parse.send_bot_message_to(self.format(record))

    def __init__(self):
        logging.Handler.__init__(self)


# for color console
class CustomFormatter(logging.Formatter):

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'
    format = "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
