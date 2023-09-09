import sys
import inspect
import logging


class Log:
    def __init__(self, debug=True):
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
        else:
            self.logger.handlers[0].setLevel(logging.DEBUG if debug else logging.INFO)

    def set_debug(self, debug):
        log_level = logging.DEBUG if debug else logging.INFO
        self.logger.setLevel(log_level)

    def debug(self, message):
        frame = inspect.currentframe().f_back
        file_name = frame.f_code.co_filename
        method_name = frame.f_code.co_name
        self.logger.debug(f"{file_name} - {method_name} - {message}")

    def info(self, message):
        frame = inspect.currentframe().f_back
        file_name = frame.f_code.co_filename
        method_name = frame.f_code.co_name
        self.logger.info(f"{file_name} - {method_name} - {message}")

    def warning(self, message):
        frame = inspect.currentframe().f_back
        file_name = frame.f_code.co_filename
        method_name = frame.f_code.co_name
        self.logger.warning(f"{file_name} - {method_name} - {message}")

    def error(self, message):
        frame = inspect.currentframe().f_back
        file_name = frame.f_code.co_filename
        method_name = frame.f_code.co_name
        self.logger.error(f"{file_name} - {method_name} - {message}")
