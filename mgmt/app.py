import os
import json
from typing import List, Optional
from pathlib import Path

import typer
from typer import echo
from rich.table import Table
from rich.console import Console

from mgmt.aws import AwsStorageMgmt
from mgmt.log import Log
from mgmt.files import FileManager
from mgmt.utils import echo_dict, check_selection
from mgmt.config import Config

app = typer.Typer(add_completion=False)
aws = AwsStorageMgmt()
logger = Log(debug=False)
file_mgmt = FileManager()


@app.command()
def upload(filename: str, compression: Optional[str] = "gzip") -> None:
    """
    Uploads the specified file to S3

    Args:
        filename (str): The name of the file or directory to upload. Use 'all' to upload all files in the directory.
        compression (Optional[str]): The compression algorithm to use. Defaults to 'gzip'.
    """
    target = filename
    cwd = Path(".").resolve()
    target_path = cwd / target
    files_created = []

    try:
        if target == "all":
            echo("uploading all media objects to S3")
            for _file_or_dir in cwd.iterdir():
                echo()
                echo("compressing...")
                echo(str(_file_or_dir))
                files_created.append(aws.upload_target(_file_or_dir, compression))
        elif target in os.listdir(cwd):
            echo()
            echo("file found, compressing...")
            echo(str(target))
            files_created.append(aws.upload_target(target_path, compression))
        else:
            echo("invalid file or directory")
            return False
    except Exception as e:
        logger.error(f"An error occurred while uploading: {e}")
    finally:
        if files_created:
            for file in files_created:
                os.remove(file)
    return


@app.command()
def search(keyword: str, location: Optional[str] = "global") -> None:
    """
    Searches for files that contain the specified keyword in their names

    Args:
        keyword (str): The keyword to search for in file names.
        location (Optional[str]): The location to search in. Defaults to 'global'.
    """
    local_files, s3_keys = aws.get_files(location=location)

    echo(f"\nSearching `{location}` for keyword `{keyword}`...")
    local_matches = [file for file in local_files if file_mgmt.keyword_in_string(keyword, file)]
    s3_matches = [file for file in s3_keys if file_mgmt.keyword_in_string(keyword, file)]

    if len(local_matches + s3_matches) >= 1:
        echo("at least one match found\n")
        echo("Local File Matches")
        echo("\n".join(local_matches))

        console = Console()
        table = Table(title="AWS S3 Search Matches")
        table.add_column("Option #")
        table.add_column("Storage Tier")
        table.add_column("Last Modified")
        table.add_column("Object Key")
        table.add_column("Restored Status")
        doptions = {}
        for i, file_name in enumerate(s3_matches):
            try:
                resp = aws.get_obj_head(file_name)
                storage_class = resp.get("StorageClass", "STANDARD")
                last_modified = resp.get("LastModified", "")
                restored_status = resp.get("Restore")
                if restored_status:
                    restored_status = str(restored_status).split("expiry-date=")[-1].replace('"', "")
                table.add_row(str(i), storage_class, str(last_modified), file_name, str(restored_status))
                doptions[i] = file_name
            except Exception as e:
                logger.error(f"An error occurred while getting metadata: {e}")

        console.print(table)
        if not typer.confirm("Download?", default=False):
            echo("Aborted.")
        else:
            resp = typer.prompt("Which file? [option #]", type=int)
            if check_selection(resp, list(doptions)):
                aws.download_file(object_name=doptions[resp])
                return
            else:
                return

        if not typer.confirm("Check Status?", default=False):
            echo("Aborted.")
        else:
            resp = typer.prompt("Which file? [option #]", type=int)
            if check_selection(resp, list(doptions)):
                aws.get_obj_head(object_name=doptions[resp])
                echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))
                return
            else:
                return
    return


@app.command()
def download(filename: str, bucket_name: Optional[str] = None) -> None:
    """
    Downloads the specified file from S3

    Args:
        filename (str): The name of the file to download.
        bucket_name (Optional[str]): The name of the bucket from which to download the file. If not provided, the default bucket is used.
    """
    echo(f"Downloading {filename} from S3...")
    aws.download_file(object_name=filename, bucket_name=bucket_name)
    return


@app.command()
def status(filename: str) -> None:
    """
    Retrieves and prints the metadata of the specified file

    Args:
        filename (str): The name of the file to get the metadata for.
    """
    aws.get_obj_head(object_name=filename)
    echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))
    return


@app.command()
def delete(filename: str) -> None:
    """
    Deletes the specified file from S3; requires confirmation

    Args:
        filename (str): The name of the file to delete.
    """
    aws.get_obj_head(object_name=filename)
    echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))
    if not typer.confirm("Confirm deletion?", default=False):
        echo("Aborted.")
        return
    else:
        try:
            aws.delete_file(filename)
            echo(f"{filename} successfully deleted from S3")
        except Exception as e:
            logger.error(f"An error occurred while deleting {filename}: {e}")
    return


@app.command()
def ls(location: Optional[str] = "global") -> None:
    """
    Lists the files in the specified location

    Args:
        location (Optional[str]): The location to list files in. Defaults to 'global'.
        bucket_name (Optional[str]): The name of the bucket to list files in. If not provided, the default bucket is used.
    """
    local_files, s3_keys = aws.get_files(location=location)
    obj_list = local_files + s3_keys
    for obj in obj_list:
        echo(obj)
    return


@app.command()
def config() -> None:
    """
    Configures the application
    """
    config = Config()
    config.load_env()
    config.print_current_config()
    if not config.ask_overwrite():
        return

    echo("Configuration complete.")


def entry_point() -> None:
    app()


if __name__ == "__main__":
    entry_point()
