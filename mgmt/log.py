import inspect
import logging
import sys


class Log:
    def __init__(self, debug: bool = True) -> None:
        """Initialize the Log class.

        Args:
            debug: Whether to enable debug logging
        """
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
        else:
            self.logger.handlers[0].setLevel(logging.DEBUG if debug else logging.INFO)

    def set_debug(self, debug: bool) -> None:
        """Set the debug level.

        Args:
            debug: Whether to enable debug logging
        """
        log_level = logging.DEBUG if debug else logging.INFO
        self.logger.setLevel(log_level)

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: The debug message to log
        """
        frame = inspect.currentframe()
        if frame and frame.f_back:
            file_name = frame.f_back.f_code.co_filename
            method_name = frame.f_back.f_code.co_name
            self.logger.debug(f"{file_name} - {method_name} - {message}")
        else:
            self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: The info message to log
        """
        frame = inspect.currentframe()
        if frame and frame.f_back:
            file_name = frame.f_back.f_code.co_filename
            method_name = frame.f_back.f_code.co_name
            self.logger.info(f"{file_name} - {method_name} - {message}")
        else:
            self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: The warning message to log
        """
        frame = inspect.currentframe()
        if frame and frame.f_back:
            file_name = frame.f_back.f_code.co_filename
            method_name = frame.f_back.f_code.co_name
            self.logger.warning(f"{file_name} - {method_name} - {message}")
        else:
            self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: The error message to log
        """
        frame = inspect.currentframe()
        if frame and frame.f_back:
            file_name = frame.f_back.f_code.co_filename
            method_name = frame.f_back.f_code.co_name
            self.logger.error(f"{file_name} - {method_name} - {message}")
        else:
            self.logger.error(message)
