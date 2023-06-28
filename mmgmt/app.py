import os
import json
from typing import Optional
from pathlib import Path

import typer
from rich.table import Table
from rich.console import Console

from mmgmt.aws import AwsStorageMgmt
from mmgmt.log import Log
from mmgmt.files import FileManager
from mmgmt.config import Config

app = typer.Typer()
aws = AwsStorageMgmt()
logger = Log(debug=True)
# file_mgmt = FileManager()


def echo_dict(input_dict: dict) -> None:
    """
    Prints a dictionary with its keys and values

    Args:
        input_dict (dict): The dictionary to be printed.
    """
    for key, val in input_dict.items():
        typer.echo(f"{key[:18]+'..' if len(key)>17 else key}{(20-int(len(key)))*'.'}{val}")


@app.command()
def upload(filename: str, compression: Optional[str] = "gzip"):
    """
    Uploads the specified file to S3. If 'all' is passed as a filename, all files in the current directory are uploaded.
    All uploaded files are compressed using the specified compression algorithm.

    Args:
        filename (str): The name of the file or directory to upload. Use 'all' to upload all files in the directory.
        compression (Optional[str]): The compression algorithm to use. Defaults to 'gzip'.
    """
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
        logger.error(e)
    finally:
        if files_created:
            for file in files_created:
                os.remove(file)


@app.command()
def search(keyword: str, location: Optional[str] = "global"):
    """
    Searches for files that contain the specified keyword in their names. The location to search in can be specified.

    Args:
        keyword (str): The keyword to search for in file names.
        location (Optional[str]): The location to search in. Defaults to 'global'.
    """
    local_files, s3_keys = aws.get_files(location=location)

    typer.echo(f"\nSearching `{location}` for keyword `{keyword}`...")
    file_mgmt = FileManager()
    local_matches = [file for file in local_files if file_mgmt.keyword_in_string(keyword, file)]
    s3_matches = [file for file in s3_keys if file_mgmt.keyword_in_string(keyword, file)]

    if len(local_matches + s3_matches) >= 1:
        typer.echo("at least one match found\n")
        typer.echo("Local File Matches")
        typer.echo("\n".join(local_matches))

        console = Console()
        table = Table(title="AWS S3 Search Matches")
        table.add_column("Option #")
        table.add_column("Storage Tier")
        table.add_column("Last Modified")
        table.add_column("Object Key")
        doptions = {}
        for i, file_name in enumerate(s3_matches):
            try:
                resp = aws.get_obj_head(file_name)
                storage_class = resp.get("StorageClass", "STANDARD")
                last_modified = resp.get("LastModified", "")
                table.add_row(storage_class, str(last_modified), file_name)
                doptions[i] = file_name
            except Exception as e:
                logger.error(f"skipping file: {file_name}")
                logger.error(e)

        console.print(table)
        if not typer.confirm("Download?", default=False):
            typer.echo("Aborted.")
            return
        else:
            resp = typer.prompt("Which file? [option #]", type=int)
            aws.download_file(doptions[resp])
            return
    else:
        typer.echo("no matches found\n")
        return


@app.command()
def download(filename: str, bucket_name: Optional[str] = None):
    """
    Downloads the specified file from S3.

    Args:
        filename (str): The name of the file to download.
        bucket_name (Optional[str]): The name of the bucket from which to download the file. If not provided, the default bucket is used.
    """
    typer.echo(f"Downloading {filename} from S3...")
    aws.download_file(object_name=filename, bucket_name=bucket_name)


@app.command()
def get_status(filename: str):
    """
    Retrieves and prints the metadata of the specified file.

    Args:
        filename (str): The name of the file to get the metadata for.
    """
    aws.get_obj_head(object_name=filename)
    typer.echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))


@app.command()
def delete(filename: str):
    """
    Deletes the specified file from S3. Requires confirmation.

    Args:
        filename (str): The name of the file to delete.
    """
    aws.get_obj_head(object_name=filename)
    typer.echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))
    if not typer.confirm("Confirm deletion?", default=False):
        typer.echo("Aborted.")
        return
    else:
        try:
            aws.delete_file(filename)
            typer.echo(f"{filename} successfully deleted from S3")
        except Exception as e:
            logger.error(f"An error occurred while deleting {filename}: {e}")


@app.command()
def ls(location: Optional[str] = "global", bucket_name: Optional[str] = None):
    """
    Lists the files in the specified location.

    Args:
        location (Optional[str]): The location to list files in. Defaults to 'global'.
        bucket_name (Optional[str]): The name of the bucket to list files in. If not provided, the default bucket is used.
    """
    if bucket_name:
        files = aws.get_bucket_obj_keys(bucket_name=bucket_name)
    else:
        if location in ("local", "s3", "global"):
            if location == "global":
                local_files, s3_keys = aws.get_files(location=location)
                files = local_files + s3_keys
        elif location == "here":
            p = Path(".")
            files = os.listdir(p)
        else:
            typer.echo(f"invalid location input: {location}")

    for file in files:
        typer.echo(file)


@app.command()
def config():
    """
    Configures the application by setting the AWS Access Key, Secret Key, and Region.
    These are prompted from the user interactively.
    """
    config = Config()
    config.load_env()
    config.print_current_config()
    if not config.ask_overwrite():
        return

    # TODO: fix this to include the values within the aws class

    # aws_access_key = typer.prompt("AWS Access Key", hide_input=True)
    # aws_secret_key = typer.prompt("AWS Secret Key", hide_input=True)
    # region = typer.prompt("AWS Region")

    # config.set_key("AWS_ACCESS_KEY_ID", aws_access_key)
    # config.set_key("AWS_SECRET_ACCESS_KEY", aws_secret_key)
    # config.set_key("AWS_REGION", region)

    typer.echo("Configuration complete.")


def entry_point() -> None:
    app()


if __name__ == "__main__":
    entry_point()
