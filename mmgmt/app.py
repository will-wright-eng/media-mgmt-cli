import os
import json
from typing import Optional
from pathlib import Path

import typer

from mmgmt.aws import AwsStorageMgmt
from mmgmt.files import FileManager
from mmgmt.config import (
    Config,  # This line assumes that Config class exists in the mmgmt.config module
)

PROJECT_NAME = "mmgmt"

app = typer.Typer()
file_mgmt = FileManager()
aws = AwsStorageMgmt(project_name=PROJECT_NAME)


def echo_dict(input_dict: dict) -> None:
    for key, val in input_dict.items():
        typer.echo(f"{key[:18]+'..' if len(key)>17 else key}{(20-int(len(key)))*'.'}{val}")


@app.command()
def upload(filename: str, compression: Optional[str] = "gzip"):
    file_or_dir = filename
    p = Path(".")
    localfiles = os.listdir(p)
    files_created = []
    try:
        if file_or_dir:
            if file_or_dir == "all":
                typer.echo("uploading all media objects to S3")
                for _file_or_dir in localfiles:
                    typer.echo(f"{_file_or_dir}, compressing...")
                    files_created.append(aws.upload_file_or_dir(_file_or_dir, compression))
            elif file_or_dir in localfiles:
                typer.echo("file found, compressing...")
                files_created.append(aws.upload_file_or_dir(file_or_dir, compression))
            else:
                typer.echo("invalid file or directory")
                return False
        else:
            typer.echo("invalid file_or_dir command")
    except Exception as e:
        typer.echo(e)
    finally:
        if files_created:
            for file in files_created:
                os.remove(file)


@app.command()
def search(keyword: str, location: Optional[str] = "global"):
    files = aws.get_files(location=location)

    typer.echo(f"Searching {location} for {keyword}...")
    matches = []
    for file in files:
        if file_mgmt.keyword_in_string(keyword, file):
            matches.append(file)

    if len(matches) >= 1:
        typer.echo("at least one match found\n")
        typer.echo("\n".join(matches))
        file_list = aws.search_flow(matches)
        if not typer.prompt("Download?", default=False, confirm=True):
            typer.echo("Aborted.")
            return
        else:
            resp = typer.prompt("Which file? [#]", type=int)
            aws.download_file(file_list[resp])
            return
    else:
        typer.echo("no matches found\n")
        return


@app.command()
def download(filename: str, bucket_name: Optional[str] = None):
    typer.echo(f"Downloading {filename} from S3...")
    aws.download_file(object_name=filename, bucket_name=bucket_name)


@app.command()
def get_status(filename: str):
    aws.get_obj_head(object_name=filename)
    typer.echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))


@app.command()
def delete(filename: str, confirm: bool = typer.Option(False, prompt="Are you sure you want to delete?")):
    if confirm:
        try:
            aws.delete_file(filename)
            typer.echo(f"{filename} successfully deleted from S3")
        except Exception as e:
            typer.echo(f"An error occurred while deleting {filename}: {e}")
    else:
        typer.echo("Deletion cancelled.")


@app.command()
def ls(location: Optional[str] = "global", bucket_name: Optional[str] = None):
    if bucket_name:
        files = aws.get_bucket_obj_keys(bucket_name=bucket_name)
    else:
        if location in ("local", "s3", "global"):
            files = aws.get_files(location=location)
        elif location == "here":
            p = Path(".")
            files = os.listdir(p)
        else:
            typer.echo(f"invalid location input: {location}")

    for file in files:
        typer.echo(file)


@app.command()
def configure():
    config = Config(Path("~/configs/mmgt"))
    config.load_env()
    config.print_current_config()
    if not config.ask_overwrite():
        return
    aws_access_key = typer.prompt("AWS Access Key", hide_input=True)
    aws_secret_key = typer.prompt("AWS Secret Key", hide_input=True)
    region = typer.prompt("AWS Region")

    config.set_key("AWS_ACCESS_KEY_ID", aws_access_key)
    config.set_key("AWS_SECRET_ACCESS_KEY", aws_secret_key)
    config.set_key("AWS_REGION", region)

    typer.echo("Configuration complete.")


def entry_point() -> None:
    app.run()


if __name__ == "__main__":
    entry_point()
