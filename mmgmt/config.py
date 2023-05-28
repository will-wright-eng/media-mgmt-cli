from pathlib import Path

import dotenv

from mmgmt.log import Log

logger = Log(debug=True)


class Config:
    def __init__(self, path: Path):
        self.path = path.expanduser()
        self.path.mkdir(parents=True, exist_ok=True)
        self.dotenv_path = self.path / ".env"

    def load_env(self):
        dotenv.load_dotenv(dotenv_path=self.dotenv_path)

    def log_current_config(self):
        if self.dotenv_path.is_file():
            with self.dotenv_path.open() as f:
                logger.info(f"Current configuration:\n{f.read()}")

    def ask_overwrite(self) -> bool:
        return input("Would you like to overwrite these settings? (y/n)").lower() == "y"

    def set_key(self, key: str, value: str):
        dotenv.set_key(self.dotenv_path, key, value)

    def update_config(self, atts_dict: dict):
        for key, value in atts_dict.items():
            self.set_key(key, value)
