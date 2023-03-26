import logging
from logging.handlers import RotatingFileHandler

import colorlog


class Logger(object):
    loggers = set()

    def __init__(self, name, format="s%(asctime)s | %(levelname)s | %(filename)s | %(message)s", level=logging.INFO,
                 colors=True):
        try:
            # Construct Logger
            self.name = name
            self.format = format
            self.level = level

            # Config Logger
            self.sh = logging.StreamHandler()
            self.standard_formatter = logging.Formatter(self.format)
            if colors:
                self.color_formatter = colorlog.ColoredFormatter(f'%(log_color){format}')
                self.sh.setFormatter(self.color_formatter)
            else:
                self.sh.setFormatter(self.standard_formatter)

            self.logger = logging.getLogger(name)

            # Prevent duplicate loggers
            if name not in self.loggers:
                self.loggers.add(name)
                self.logger.setLevel(self.level)
                self.logger.addHandler(self.sh)
        except Exception as e:
            raise ValueError(f"Error creating logger: {e}")

    def get_logger(self):
        return self.logger

    def add_file_handler(self, file_path):
        """
        Adds a thread-safe file handler to the logger instance.
        :param file_path: absolute path to destination log file
        :return:
        """
        try:
            fh = RotatingFileHandler(filename=file_path)
            fh.setFormatter(self.standard_formatter)
            fh.setLevel(self.level)
            self.logger.addHandler(fh)
        except Exception as e:
            raise ValueError(f"Failed to add file handler: {e}")
