import os
import gzip
import shutil
import tarfile
from typing import List
from pathlib import Path
from zipfile import ZipFile

import rarfile

from mgmt.log import Log
from mgmt.config import Config


class FileManager:
    def __init__(self, base_path=None):
        self.logger = Log()
        if base_path:
            self.base_path = Path(base_path)
        else:
            config = Config()
            self.base_path = Path(config.configs.get("MGMT_LOCAL_DIR"))
        if not self.base_path.exists():
            self.logger.error(f"-- ValueError -- Path {str(self.base_path)} is not a valid path from root")
            self.logger.error("rerun `mgmt config`")

    def zip_single_file(self, filename: str) -> str:
        zip_file = filename.split(".")[0] + ".zip"
        with ZipFile(zip_file, "w") as zipf:
            zipf.write(os.path.join(self.base_path, filename), arcname=filename)
        return zip_file

    def gzip_single_file(self, filename: str) -> str:
        gzip_file = f"{filename}.gz"
        with open(os.path.join(self.base_path, filename), "rb") as f_in, gzip.open(
            os.path.join(self.base_path, gzip_file), "wb"
        ) as f_out:
            shutil.copyfileobj(f_in, f_out)
        return gzip_file

    def zip_process(self, target_path: Path) -> str:
        try:
            # dir_name = str(self.base_path / target_path)
            dir_name = str(target_path)
            zip_path = shutil.make_archive(dir_name, "zip", dir_name)
            return zip_path.split("/")[-1]
        except NotADirectoryError as e:
            self.logger.error(e)
            return self.zip_single_file(target_path)

    def gzip_process(self, target_path: Path) -> str:
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
            self.logger.error(e)
            return self.gzip_single_file(target_path)

    def files_in_media_dir(self) -> List[str]:
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

    def list_all_files(self):
        for file in self.base_path.glob("**/*"):
            self.logger.info(file)

    def list_all_dirs(self):
        for directory in self.base_path.glob("**/"):
            self.logger.info(directory)

    @staticmethod
    def clean_string(string: str) -> str:
        string = "".join(e for e in string if e.isalnum() or e == " " or e == "/")
        string = string.replace("  ", " ").replace("  ", " ").replace(" ", "_")
        return string

    @staticmethod
    def keyword_in_string(keyword, file):
        return file.lower().find(keyword.lower()) != -1

    @staticmethod
    def abort_if_false(ctx, param, value):
        if not value:
            ctx.abort()


class RarHandler:
    def __init__(self, path):
        self.path = Path(path)
        if not self.path.exists():
            raise ValueError(f"Path {path} does not exist")

    def extract_all(self, destination):
        destination = Path(destination)
        if not destination.exists():
            destination.mkdir(parents=True)

        for rar_file in self.path.glob("**/*.rar"):
            with rarfile.RarFile(rar_file) as rf:
                rf.extractall(destination)

    def list_all(self):
        for rar_file in self.path.glob("**/*.rar"):
            with rarfile.RarFile(rar_file) as rf:
                self.logger.info(f"Contents of {rar_file}:")
                self.logger.info(rf.namelist())
