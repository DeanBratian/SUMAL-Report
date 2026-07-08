# CHECKED

import os
import logging
from core.config import APP_CONFIG

class Logger:
    def __init__(self, log_file_path: str, level: int = logging.DEBUG):
        os.makedirs(os.path.dirname(log_file_path), exist_ok = True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            # mode='w' truncates on every launch — keep the previous run's log
            # so a crash can still be investigated after the app is relaunched.
            if os.path.exists(log_file_path):
                try:
                    os.replace(log_file_path, log_file_path + ".prev")
                except OSError:
                    pass # previous log locked by another instance — keep going

            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s", datefmt = APP_CONFIG.TIME_FORMAT
            )

            file_handler = logging.FileHandler(log_file_path, mode = 'w', encoding = 'utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    # ---------------------------------------------------------------------- #

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)
