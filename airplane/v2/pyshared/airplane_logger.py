import os
import time
import logging
from logging import Formatter, Logger, StreamHandler
from v2.consts.airplane_env import AirplaneEnv


class _AirplaneLoggerFormatter(Formatter):

    def __init__(self, is_utc: bool):
        log_format = "%(levelname)-8s | %(filename)s:%(lineno)d | %(message)s"
        # Attach time information
        if AirplaneEnv.is_local_env():
            log_format = f"%(asctime)s | {log_format}"
        super().__init__(fmt=log_format, datefmt="%m-%d-%y %H:%M:%S%z %Z")
        self.converter = time.gmtime if is_utc else time.localtime

    # Overrides Formatter's method
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record)


class AirplaneLogger(Logger):

    def __init__(self, name: str = "airplane-logger", is_utc: bool = True, level: int or str = logging.INFO):
        super().__init__(name, self._get_level(level))
        self._formatter = _AirplaneLoggerFormatter(is_utc)
        self._add_default_handler()

    @staticmethod
    def _get_level(level: int or str) -> str:
        # Environemt variable LOG_LEVEL takes precedence over the parameter level
        return int(os.getenv("LOG_LEVEL", level))

    def _add_default_handler(self) -> None:
        stderr_handler = StreamHandler()
        stderr_handler.setFormatter(self._formatter)
        self.addHandler(stderr_handler)


logger = AirplaneLogger(is_utc=False)
