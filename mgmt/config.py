import os
from pathlib import Path
from typing import Dict, List, Optional

import dotenv

from mgmt.log import Log


class Config:
    def __init__(self) -> None:
        """Initialize the Config class."""
        self.path = Path("~/.config/mgmt").expanduser()
        self.path.mkdir(parents=True, exist_ok=True)
        self.dotenv_path = self.path / "config"
        self.logger = Log()
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
        self.keys: List[str] = [
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
        dotenv.load_dotenv(dotenv_path=self.dotenv_path)

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

    def get_configs(self) -> Optional[Dict[str, Optional[str]]]:
        """Get the current configuration as a dictionary"""
        if self.dotenv_path.is_file():
            self.load_env()
            configs = {key: os.getenv(key) for key in self.keys}
        return configs

    def set_key(self, key: str, value: str) -> None:
        """Set a configuration key-value pair"""
        dotenv.set_key(self.dotenv_path, key, value)

    def update_config(self, atts_dict: Dict[str, str]) -> None:
        """Update multiple configuration values"""
        for key, value in atts_dict.items():
            self.set_key(key, value)

    def check_exists(self) -> bool:
        """Check if the configuration file exists"""
        return self.dotenv_path.is_file()

    def write_env_vars(self, env_vars: Dict[str, str]) -> None:
        """Write environment variables to the config file"""
        with self.dotenv_path.open(mode="a") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
