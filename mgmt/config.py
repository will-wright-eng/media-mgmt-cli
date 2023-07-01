import os
from pathlib import Path

import dotenv

from mgmt.log import Log


class Config:
    def __init__(self):
        self.path = Path("~/.config/mmgmt").expanduser()
        self.path.mkdir(parents=True, exist_ok=True)
        self.dotenv_path = self.path / "config"
        self.logger = Log(debug=False)
        if not self.check_exists():
            self.logger.error("config file not found")
            self.logger.info(f"check config file exists: {str(self.check_exists())}")
            self.logger.info(f"dotenv_path: {str(self.dotenv_path)}")

    def load_env(self):
        dotenv.load_dotenv(dotenv_path=self.dotenv_path)

    def log_current_config(self):
        if self.dotenv_path.is_file():
            with self.dotenv_path.open() as f:
                self.logger.info(f"Current configuration:\n{f.read()}")

    def print_current_config(self):
        if self.dotenv_path.is_file():
            with self.dotenv_path.open() as f:
                print(f"Current configuration:\n{f.read()}")

    def get_configs(self):
        if self.dotenv_path.is_file():
            self.load_env()
            configs = {
                "BUCKET": os.getenv("BUCKET"),
                "OBJECT_PREFIX": os.getenv("OBJECT_PREFIX"),
                "LOCAL_DIR": os.getenv("LOCAL_DIR"),
            }
        return configs

    def ask_overwrite(self) -> bool:
        return input("Would you like to overwrite these settings? (y/n) ").lower() == "y"

    def set_key(self, key: str, value: str):
        dotenv.set_key(self.dotenv_path, key, value)

    def update_config(self, atts_dict: dict):
        for key, value in atts_dict.items():
            self.set_key(key, value)

    def check_exists(self):
        return self.dotenv_path.is_file()
