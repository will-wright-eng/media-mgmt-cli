import logging
import os
import re
from pathlib import Path
from typing import Optional


def load_dotenv(dotenv_path: Path) -> None:
    """Load environment variables from a .env file.

    This is a pure Python implementation that replaces python-dotenv.

    Args:
        dotenv_path: Path to the .env file
    """
    if not dotenv_path.exists():
        return

    with dotenv_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE format
            # Handle quoted values (single or double quotes)
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if match:
                key = match.group(1)
                value = match.group(2).strip()

                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                # Only set if not already in environment (don't override existing env vars)
                if key not in os.environ:
                    os.environ[key] = value


def set_key(dotenv_path: Path, key: str, value: str) -> None:
    """Set or update a key-value pair in a .env file.

    This is a pure Python implementation that replaces python-dotenv.

    Args:
        dotenv_path: Path to the .env file
        key: The key to set
        value: The value to set
    """
    lines: list[str] = []
    key_found = False

    # Read existing file if it exists
    if dotenv_path.exists():
        with dotenv_path.open(encoding="utf-8") as f:
            for line in f:
                # Check if this line contains the key we're updating
                match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line.strip())
                if match and match.group(1) == key:
                    # Replace the existing line
                    lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    # Keep the original line
                    lines.append(line)

    # If key wasn't found, append it
    if not key_found:
        lines.append(f"{key}={value}\n")

    # Write back to file
    with dotenv_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)


class Config:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the Config class.

        Args:
            logger: Optional logger instance. If None, uses module-level logger.
                   Allows dependency injection for testing.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.path = Path("~/.config/mgmt").expanduser()
        self.path.mkdir(parents=True, exist_ok=True)
        self.dotenv_path = self.path / "config"
        self.keys_dict = {
            "aws_bucket": {"name": "MGMT_BUCKET", "note": "storage bucket in aws"},
            "object_prefix": {
                "name": "MGMT_OBJECT_PREFIX",
                "note": "prefix added to storage blob",
            },
            "local_dir": {
                "name": "MGMT_LOCAL_DIR",
                "note": "full path to media dir on local machine",
            },
        }
        self.keys: list[str] = [
            ele.get("name") or "" for key, ele in self.keys_dict.items()
        ]
        if not self.check_exists():
            self.logger.error("config file not found")
            self.logger.info(f"check config file exists: {str(self.check_exists())}")
            self.logger.info(f"dotenv_path: {str(self.dotenv_path)}")
            self.configs = None
        else:
            self.configs = self.get_configs()

    def load_env(self) -> None:
        """Load environment variables from the config file."""
        load_dotenv(dotenv_path=self.dotenv_path)

    def log_current_config(self) -> None:
        """Log the current configuration to the logger."""
        if self.dotenv_path.is_file():
            with self.dotenv_path.open() as f:
                self.logger.info(f"Current configuration:\n{f.read()}")

    def print_current_config(self) -> None:
        """Print the current configuration to stdout."""
        if self.dotenv_path.is_file():
            with self.dotenv_path.open() as f:
                print(f"Current configuration:\n{f.read()}")

    def get_configs(self) -> Optional[dict[str, Optional[str]]]:
        """Get the current configuration as a dictionary"""
        if self.dotenv_path.is_file():
            self.load_env()
            configs = {key: os.getenv(key) for key in self.keys}
        return configs

    def set_key(self, key: str, value: str) -> None:
        """Set a configuration key-value pair"""
        set_key(self.dotenv_path, key, value)

    def update_config(self, atts_dict: dict[str, str]) -> None:
        """Update multiple configuration values"""
        for key, value in atts_dict.items():
            self.set_key(key, value)

    def check_exists(self) -> bool:
        """Check if the configuration file exists"""
        return self.dotenv_path.is_file()

    def write_env_vars(self, env_vars: dict[str, str]) -> None:
        """Write environment variables to the config file"""
        with self.dotenv_path.open(mode="a") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
