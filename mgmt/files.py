import gzip
import os
import shutil
import tarfile
from pathlib import Path
from typing import Any, List, Optional, Union
from zipfile import ZipFile

import rarfile

from mgmt.config import Config
from mgmt.log import Log


class FileManager:
    def __init__(self, base_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize the FileManager"""
        self.logger = Log()
        if base_path:
            self.base_path = Path(base_path)
        else:
            config = Config()
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

    def zip_single_file(self, filename: str) -> str:
        """Create a zip file from a single file"""
        zip_file = filename.split(".")[0] + ".zip"
        with ZipFile(zip_file, "w") as zipf:
            zipf.write(os.path.join(self.base_path, filename), arcname=filename)
        return zip_file

    def gzip_single_file(self, filename: str) -> str:
        """Create a gzip file from a single file"""
        gzip_file = f"{filename}.gz"
        with open(os.path.join(self.base_path, filename), "rb") as f_in, gzip.open(
            os.path.join(self.base_path, gzip_file), "wb"
        ) as f_out:
            shutil.copyfileobj(f_in, f_out)
        return gzip_file

    def zip_process(self, target_path: Path) -> str:
        """Create a zip archive from a path (file or directory)"""
        try:
            # dir_name = str(self.base_path / target_path)
            dir_name = str(target_path)
            zip_path = shutil.make_archive(dir_name, "zip", dir_name)
            return zip_path.split("/")[-1]
        except NotADirectoryError as e:
            self.logger.error(str(e))
            return self.zip_single_file(str(target_path))

    def gzip_process(self, target_path: Path) -> str:
        """Create a gzip tar archive from a path (file or directory)"""
        self.logger.debug("gzip_process")
        try:
            # dir_path = str(self.base_path / target_path)
            dir_path = str(target_path)
            self.logger.debug(dir_path)
            gzip_file = f"{target_path}.tar.gz"
            self.logger.debug("tarfile open")
            tar = tarfile.open(gzip_file, "w:gz")
            self.logger.debug("tarfile add")
            tar.add(dir_path, arcname=target_path)
            tar.close()
            return gzip_file
        except NotADirectoryError as e:
            self.logger.error(str(e))
            return self.gzip_single_file(str(target_path))

    def files_in_media_dir(self) -> List[str]:
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

    def list_all_files(self) -> None:
        """List all files in the base directory."""
        for file in self.base_path.glob("**/*"):
            self.logger.info(str(file))

    def list_all_dirs(self) -> None:
        """List all directories in the base directory."""
        for directory in self.base_path.glob("**/"):
            self.logger.info(str(directory))

    @staticmethod
    def clean_string(string: str) -> str:
        """Clean a string by removing special characters"""
        string = "".join(e for e in string if e.isalnum() or e == " " or e == "/")
        string = string.replace("  ", " ").replace("  ", " ").replace(" ", "_")
        return string

    @staticmethod
    def keyword_in_string(keyword: str, file: str) -> bool:
        """Check if keyword is in file string (case insensitive)"""
        return file.lower().find(keyword.lower()) != -1

    @staticmethod
    def abort_if_false(ctx: Any, param: Any, value: bool) -> None:
        """Abort if value is False"""
        if not value:
            ctx.abort()


class RarHandler:
    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize the RarHandler"""
        self.path = Path(path)
        self.logger = Log()
        if not self.path.exists():
            raise ValueError(f"Path {path} does not exist")

    def extract_all(self, destination: Union[str, Path]) -> None:
        """Extract all RAR files to destination"""
        destination = Path(destination)
        if not destination.exists():
            destination.mkdir(parents=True)

        for rar_file in self.path.glob("**/*.rar"):
            with rarfile.RarFile(rar_file) as rf:
                rf.extractall(destination)

    def list_all(self) -> None:
        """List contents of all RAR files"""
        for rar_file in self.path.glob("**/*.rar"):
            with rarfile.RarFile(rar_file) as rf:
                self.logger.info(f"Contents of {rar_file}:")
                self.logger.info(rf.namelist())
