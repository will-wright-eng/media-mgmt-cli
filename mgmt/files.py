import os
import gzip
import shutil
import pathlib
import tarfile
from typing import List
from zipfile import ZipFile

from mgmt.log import Log


class FileManager:
    def __init__(self, base_path=None):
        self.logger = Log(debug=False)
        if base_path:
            self.base_path = pathlib.Path(base_path)
        else:
            self.base_path = pathlib.Path.home() / "media"
            self.base_path = self.base_path.resolve()

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

    def zip_process(self, target_path: pathlib.Path) -> str:
        try:
            # dir_name = str(self.base_path / target_path)
            dir_name = str(target_path)
            zip_path = shutil.make_archive(dir_name, "zip", dir_name)
            return zip_path.split("/")[-1]
        except NotADirectoryError as e:
            self.logger.error(e)
            return self.zip_single_file(target_path)

    def gzip_process(self, target_path: pathlib.Path) -> str:
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
        tmp = os.listdir(self.base_path)
        tmp = [
            os.listdir(os.path.join(self.base_path, folder))
            if os.path.isdir(os.path.join(self.base_path, folder))
            else [folder]
            for folder in tmp
        ]
        return [item for sublist in tmp for item in sublist]

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
