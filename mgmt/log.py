import inspect
import logging
from pathlib import Path

_initialized = False
_log_file_path: Path | None = None


def get_log_file_path() -> Path:
    """Get the path to the log file.

    Returns:
        Path to the log file (defaults to ~/.config/mgmt/mgmt.log)
    """
    global _log_file_path
    if _log_file_path:
        return _log_file_path
    log_dir = Path("~/.config/mgmt").expanduser()
    return log_dir / "mgmt.log"


def setup_logging(debug: bool = True, log_file: Path | None = None) -> None:
    """Initialize logging configuration. Should be called once at application startup.

    Args:
        debug: If True, set log level to DEBUG, otherwise INFO
        log_file: Path to log file. If None, uses ~/.config/mgmt/mgmt.log
    """
    global _initialized, _log_file_path
    if _initialized:
        return

    # Get the root logger for the mgmt package
    logger = logging.getLogger("mgmt")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    # Prevent propagation to root logger to avoid interfering with terminal I/O
    logger.propagate = False

    # Only add handlers if they don't exist
    if not logger.handlers:
        try:
            # Determine log file path
            if log_file is None:
                log_dir = Path("~/.config/mgmt").expanduser()
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / "mgmt.log"
            else:
                log_file.parent.mkdir(parents=True, exist_ok=True)

            # Store the log file path for later retrieval
            _log_file_path = log_file

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            # Use FileHandler to write logs to a file
            # delay=True defers file opening until first log message to avoid terminal interference
            file_handler = logging.FileHandler(
                log_file, mode="a", encoding="utf-8", delay=True
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # If file logging fails, silently continue without logging
            # This prevents any terminal interference from file operations
            pass

    _initialized = True


class LogAdapter:
    """Adapter that adds custom formatting (file/method names) to a standard logger.

    This wraps a standard logging.Logger to add file and method name information
    to log messages, while maintaining compatibility with standard logging.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the LogAdapter with a standard logger.

        Args:
            logger: Standard logging.Logger instance to wrap
        """
        self.logger = logger

    def _format_message(self, message: str) -> str:
        """Add file and method name to log message."""
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            file_name = caller_frame.f_code.co_filename
            method_name = caller_frame.f_code.co_name
            return f"{file_name} - {method_name} - {message}"
        return message

    def debug(self, message: str) -> None:
        """Log a debug message"""
        self.logger.debug(self._format_message(message))

    def info(self, message: str) -> None:
        """Log an info message"""
        self.logger.info(self._format_message(message))

    def warning(self, message: str) -> None:
        """Log a warning message"""
        self.logger.warning(self._format_message(message))

    def error(self, message: str) -> None:
        """Log an error message"""
        self.logger.error(self._format_message(message))

    def setLevel(self, level: int) -> None:
        """Set the log level"""
        self.logger.setLevel(level)
