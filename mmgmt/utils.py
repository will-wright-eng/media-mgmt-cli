import os
import gzip
import shutil
import pathlib
import tarfile
from typing import List
from pathlib import Path
from zipfile import ZipFile


def zip_single_file(filename: str) -> str:
    pathname = str(Path.cwd())
    zip_file = filename.split(".")[0] + ".zip"
    with ZipFile(zip_file, "w") as zipf:
        zipf.write(os.path.join(pathname, filename), arcname=filename)
    return zip_file


def gzip_single_file(filename: str) -> str:
    pathname = str(Path.cwd())
    gzip_file = f"{filename}.gz"
    with open(os.path.join(pathname, filename), "rb") as f_in, gzip.open(
        os.path.join(pathname, gzip_file), "wb"
    ) as f_out:
        shutil.copyfileobj(f_in, f_out)
    return gzip_file


def zip_process(file_or_dir: str) -> str:
    p = Path.cwd()
    try:
        # if dir
        dir_name = str(p / file_or_dir)
        zip_path = shutil.make_archive(dir_name, "zip", dir_name)
        return zip_path.split("/")[-1]
    except NotADirectoryError as e:
        print(e)
        # if file
        return zip_single_file(file_or_dir)


def gzip_process(file_or_dir: str) -> str:
    p = Path.cwd()
    try:
        dir_path = str(p / file_or_dir)
        gzip_file = f"{file_or_dir}.tar.gz"
        tar = tarfile.open(f"{file_or_dir}.tar.gz", "w:gz")
        tar.add(dir_path, arcname=file_or_dir)
        tar.close()
        return gzip_file
    except NotADirectoryError as e:
        print(e)
        return gzip_single_file(file_or_dir)


def clean_string(string: str) -> str:
    string = "".join(e for e in string if e.isalnum() or e == " " or e == "/")
    string = string.replace("  ", " ").replace("  ", " ").replace(" ", "_")
    return string


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def keyword_in_string(keyword, file):
    return file.lower().find(keyword.lower()) != -1


def files_in_media_dir(local_path=None) -> List[str]:
    if local_path:
        media_dir = local_path
    else:
        media_dir = pathlib.Path.home() / "media"
        media_dir = media_dir.resolve()
    tmp = os.listdir(media_dir)
    tmp = [
        os.listdir(os.path.join(media_dir, folder)) if os.path.isdir(os.path.join(media_dir, folder)) else [folder]
        for folder in tmp
    ]
    return [item for sublist in tmp for item in sublist]
