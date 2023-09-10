import os
import json
from typing import Optional
from pathlib import Path

import toml
import typer
from rich import box
from typer import echo
from rich.table import Table
from rich.console import Console

from mgmt.aws import AwsStorageMgmt
from mgmt.files import FileManager
from mgmt.utils import check_selection, get_restore_status_short
from mgmt.config import Config

app = typer.Typer(add_completion=False)
aws = AwsStorageMgmt()


def get_version():
    pyproject = toml.load("pyproject.toml")
    return pyproject["tool"]["poetry"]["version"]


def version_callback(value: bool):
    if value:
        print(f"Media MGMT CLI Version: {get_version()}")
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", callback=version_callback, help="Show the version and exit.", is_eager=True
    ),
):
    pass


@app.command()
def upload(filename: str = "all", compression: Optional[str] = "gzip") -> None:
    """
    Uploads the specified file to S3

    Args:
        filename (str): The name of the file or directory to upload.
            Use 'all' to upload all files in the directory.
        compression (Optional[str]): The compression algorithm to use. Defaults to 'gzip'.
    """
    target = filename
    cwd = Path(".").resolve()
    target_path = cwd / target
    files_created = []
    skip_files = [".DS_Store"]

    try:
        if target == "all":
            echo("uploading all media objects to S3")
            for _file_or_dir in cwd.iterdir():
                if str(_file_or_dir) not in skip_files:
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
        echo(f"An error occurred while uploading: {e}", err=True)
    finally:
        if files_created:
            for file in files_created:
                os.remove(file)
    return


@app.command()
def search(keyword: str) -> None:
    """
    Searches for files that contain the specified keyword in their names

    Args:
        keyword (str): The keyword to search for in file names
    """
    location = "global"
    file_mgmt = FileManager()
    local_files, s3_keys = aws.get_files(location=location)
    echo(f"\nSearching `{location}` for keyword `{keyword}`...")
    local_matches = [file for file in local_files if file_mgmt.keyword_in_string(keyword, file)]
    s3_matches = [file for file in s3_keys if file_mgmt.keyword_in_string(keyword, file)]

    echo(f"total matches found = {str(len(local_matches)+len(s3_matches))}")
    if len(local_matches + s3_matches) >= 1:
        echo("at least one match found\n")
        echo("Local File Matches")
        echo("\n".join(local_matches))
        echo()
        console = Console()
        table = Table(title="AWS S3 Search Matches", box=box.SIMPLE)
        table.add_column("#", style="cyan")
        table.add_column("StorageClass", style="green")
        table.add_column("LastModified")
        table.add_column("Object Key", style="magenta")
        table.add_column("Restore")
        table.add_column("GBs")
        doptions = {}

        for i, file_name in enumerate(s3_matches):
            try:
                resp = aws.get_obj_head(file_name)
                storage_class = resp.get("StorageClass", "STANDARD")
                last_modified = resp.get("LastModified", "")
                restore_status = get_restore_status_short(resp.get("Restore"))
                content_length = resp.get("ContentLength")
                content_length_gb = round(int(content_length) / (1024**3), 2)

                table.add_row(
                    str(i),
                    storage_class,
                    str(last_modified).split(" ")[0],
                    file_name,
                    str(restore_status),
                    str(content_length_gb),
                )
                doptions[i] = file_name
            except Exception as e:
                echo(f"An error occurred while getting metadata: {e}", err=True)

        console.print(table)

        if not typer.confirm("Download?", default=False):
            echo("Aborted.")
        else:
            resp = typer.prompt("Which file? [option #]", type=int)

            if check_selection(resp, list(doptions)):
                aws.download(object_name=doptions[resp])
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
def download(filename: str) -> None:
    """
    Downloads the specified file from S3

    Args:
        filename (str): The name of the file to download.
    """
    # echo(f"Downloading {filename} from S3...")
    aws.download(object_name=filename)
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
            echo(f"An error occurred while deleting {filename}: {e}", err=True)
    return


@app.command()
def ls(location: Optional[str] = "global") -> None:
    """
    Lists the files in the specified location

    Args:
        location (Optional[str]): The location to list files in: 'local', 'gloabl', or 's3'.
        Defaults to 'global'.
    """
    if location == "global":
        local_files, s3_keys = aws.get_files(location=location)
    elif location == "local":
        local_files = aws.get_files(location=location)
        s3_keys = [""]
    elif location == "s3":
        s3_keys = aws.get_files(location=location)
        local_files = [""]

    echo()
    echo("Local Files...")

    for obj in local_files:
        echo(obj)

    echo()
    echo("Bucket Objects...")

    for obj in s3_keys:
        echo(obj)


def write_config(config):
    echo("aws buckets...")
    echo("\n".join(aws.get_bucket_list()))
    config.dotenv_path.unlink(missing_ok=True)
    config.dotenv_path.touch()
    echo()
    env_vars = {}
    config_dict = config.configs

    for _, val in config.keys_dict.items():
        key = val.get("name")

        if config_dict:
            res_default = config_dict.get(key)
        else:
            res_default = None

        res = typer.prompt(f"{key} ({val.get('note')})", type=str, default=res_default)
        env_vars[key] = res

    config.write_env_vars(env_vars)
    config.print_current_config()


@app.command()
def config() -> None:
    """
    Configures the application
    """
    config = Config()

    if config.check_exists():
        config.load_env()
        config.print_current_config()

        if typer.confirm("Would you like to overwrite these settings?", default=False):
            echo("Overwriting")
            write_config(config)
    else:
        write_config(config)

    echo("Configuration complete.")


def entry_point() -> None:
    app()


if __name__ == "__main__":
    entry_point()
