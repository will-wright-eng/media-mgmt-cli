import os
import gzip
import shutil
import tarfile
import pathlib
from pathlib import Path
from zipfile import ZipFile
from typing import List

from click import echo

from .aws import aws


def zip_single_file(filename: str) -> str:
    pathname = str(Path.cwd())
    zip_file = filename.split(".")[0] + ".zip"
    with ZipFile(zip_file, "w") as zipf:
        zipf.write(os.path.join(pathname, filename), arcname=filename)
    return zip_file


def gzip_single_file(filename: str) -> str:
    pathname = str(Path.cwd())
    gzip_file = f"{filename}.gz"
    with open(os.path.join(pathname, filename), "rb") as f_in:
        with gzip.open(os.path.join(pathname, gzip_file), "wb") as f_out:
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
        # if file
        return zip_single_file(file_or_dir)


def gzip_process(file_or_dir: str) -> str:
    p = Path.cwd()
    try:
        # # if dir
        dir_path = str(p / file_or_dir)
        gzip_file = f"{file_or_dir}.tar.gz"
        tar = tarfile.open(f"{file_or_dir}.tar.gz", "w:gz")
        tar.add(dir_path, arcname=file_or_dir)
        tar.close()
        return gzip_file
    except NotADirectoryError as e:
        # if file
        return gzip_single_file(file_or_dir)


def clean_string(string: str) -> str:
    string = "".join(e for e in string if e.isalnum() or e == " " or e == "/")
    string = string.replace("  ", " ").replace("  ", " ").replace(" ", "_")
    return string


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def keyword_in_string(keyword, file):
    if file.lower().find(keyword.lower()) != -1:
        # print ("Contains given substring ")
        return True
    else:
        # print ("Doesn't contains given substring")
        return False


def files_in_media_dir() -> List[str]:
    # TODO: insert "LOCAL_MEDIA_DIR" into configs
    media_dir = pathlib.Path.home() / "media"
    media_dir = media_dir.resolve()
    tmp = os.listdir(media_dir)
    tmp = [
        os.listdir(os.path.join(media_dir, folder)) if os.path.isdir(os.path.join(media_dir, folder)) else [folder]
        for folder in tmp
    ]
    return [item for sublist in tmp for item in sublist]


def click_echo(string):
    echo(string)


def upload_file_or_dir(file_or_dir, compression):
    if compression == "zip":
        file_created = zip_process(file_or_dir)
    elif compression == "gzip":
        file_created = gzip_process(file_or_dir)
    aws.upload_file(file_name=file_created)
    return file_created


def get_files(location: str):
    if location == "local":
        files = files_in_media_dir()
    elif location == "s3":
        # get objects from s3 bucket
        files = aws.get_bucket_object_keys()
    elif location == "global":
        # do both
        files = files_in_media_dir() + aws.get_bucket_object_keys()
    else:
        echo("invalid location")
        return False
    return files


def get_storage_tier(file_list: List[str]):
    check_status = str(input("display storage tier? [Y/n] "))
    if check_status in ("Y", "n"):
        if check_status == "Y":
            echo()
            for file_name in file_list:
                try:
                    resp = aws.get_obj_head(file_name)
                    try:
                        restored = resp["Restore"]
                        if restored:
                            restored = True
                    except KeyError as e:
                        restored = False
                    try:
                        echo(f"{resp['StorageClass']} \t {restored} \t {file_name}")
                    except KeyError as e:
                        echo(f"STANDARD \t {restored} \t {file_name}")
                except Exception as e:
                    # except ClientError as e:
                    echo(f"skipping: {file_name},\t {str(e)}")
