import logging
import tarfile
from pathlib import Path
from typing import Optional, Union

from mgmt.config import Config


class FileManager:
    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the FileManager.

        Args:
            base_path: Optional base path for file operations.
            logger: Optional logger instance. If None, uses module-level logger.
                   Allows dependency injection for testing.
        """
        self.logger = logger or logging.getLogger(__name__)
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Pass logger to Config so they share the same logger
            config = Config(logger=self.logger)
            if config.configs and config.configs.get("MGMT_LOCAL_DIR"):
                local_dir = config.configs.get("MGMT_LOCAL_DIR")
                if local_dir:
                    self.base_path = Path(local_dir)
            else:
                raise ValueError("MGMT_LOCAL_DIR not configured")
        if not self.base_path.exists():
            self.logger.error(
                f"-- ValueError -- Path {str(self.base_path)} is not a valid path from root"
            )
            self.logger.error("rerun `mgmt config`")

    def gzip_process(self, target_path: Path) -> str:
        """Create a gzip tar archive from a path (file or directory)"""
        self.logger.debug("gzip_process")
        dir_path = str(target_path)
        self.logger.debug(dir_path)
        gzip_file = f"{target_path}.tar.gz"
        self.logger.debug("tarfile open")
        tar = tarfile.open(gzip_file, "w:gz")
        self.logger.debug("tarfile add")
        # tarfile.add() works for both files and directories
        tar.add(dir_path, arcname=target_path.name)
        tar.close()
        return gzip_file

    def files_in_media_dir(self) -> list[str]:
        """Get list of media files in the configured directory"""
        file_list = []
        path = Path(self.base_path)
        for file in path.glob("**/*"):
            if (
                file.is_file()
                and file.suffix.lower() in [".rar", ".mkv", ".mp4"]
                and "subs" not in str(file).lower()
                and "sample" not in str(file).lower()
            ):
                # print(file)
                file_list.append(file)
        return ["/".join(str(file).split("/")[-2:]) for file in file_list]

    @staticmethod
    def keyword_in_string(keyword: str, file: str) -> bool:
        """Check if keyword is in file string (case insensitive)"""
        return file.lower().find(keyword.lower()) != -1
