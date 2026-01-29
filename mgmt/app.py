import json
import logging
import os
import re
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from typer import echo

from mgmt.aws import AwsStorageMgmt
from mgmt.config import Config
from mgmt.files import FileManager
from mgmt.log import get_log_file_path, setup_logging
from mgmt.utils import check_selection, get_restore_status_short

# Initialize logging at application startup
setup_logging(debug=True)

# Create module-level logger for app.py
logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False)

# Create AWS instance with logger (will be passed to Config and FileManager)
aws_logger = logging.getLogger("mgmt.aws")
aws = AwsStorageMgmt(logger=aws_logger)


def get_version() -> str:
    """Get the version from installed package or pyproject.toml"""
    try:
        # Try to get version from installed package
        return version("mgmt")
    except PackageNotFoundError:
        # Fallback: parse version from pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            with pyproject_path.open(encoding="utf-8") as f:
                content = f.read()
                # Match version = "x.y.z" pattern
                match = re.search(
                    r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE
                )
                if match:
                    return match.group(1)
        return "unknown"


def version_callback(value: bool) -> None:
    """Callback function for version option"""
    if value:
        print(f"Media MGMT CLI Version: {get_version()}")
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        help="Show the version and exit.",
        is_eager=True,
    ),
) -> None:
    """Common callback for all commands."""
    pass


@app.command()
def upload(
    filename: Optional[str] = typer.Argument(
        None, help="File or directory path to upload"
    ),
    all: bool = typer.Option(
        False, "--all", "-a", help="Upload all files in the current directory"
    ),
) -> None:
    """
    Uploads the specified file or directory to S3 with gzip compression.

    Either provide a filename/path as an argument, or use --all to upload all files in the current directory.
    """
    cwd = Path(".").resolve()
    files_created = []  # Compressed files created
    files_uploaded_successfully = []  # Compressed files successfully uploaded
    original_files_uploaded = []  # Original files/directories successfully uploaded
    skip_files = [".DS_Store"]

    try:
        if all:
            if filename:
                echo("Error: Cannot specify both filename and --all option", err=True)
                return
            echo("uploading all media objects to S3")
            for _file_or_dir in cwd.iterdir():
                if _file_or_dir.name not in skip_files:
                    echo()
                    echo("compressing...")
                    echo(str(_file_or_dir))
                    try:
                        file_created = aws.upload_target(_file_or_dir)
                        files_created.append(file_created)
                        files_uploaded_successfully.append(file_created)
                        original_files_uploaded.append(_file_or_dir)
                    except Exception as e:
                        echo(
                            f"An error occurred while uploading {_file_or_dir}: {e}",
                            err=True,
                        )
                        # Keep the compressed file for potential retry
        elif filename:
            target_path = cwd / filename
            if target_path.exists():
                echo()
                echo("file found, compressing...")
                echo(str(filename))
                try:
                    file_created = aws.upload_target(target_path)
                    files_created.append(file_created)
                    files_uploaded_successfully.append(file_created)
                    original_files_uploaded.append(target_path)
                except Exception as e:
                    echo(f"An error occurred while uploading {filename}: {e}", err=True)
                    # Keep the compressed file for potential retry
            else:
                echo("invalid file or directory")
                return
        else:
            echo(
                "Error: Must specify either a filename/path or use --all option",
                err=True,
            )
            return
    except Exception as e:
        echo(f"An error occurred while uploading: {e}", err=True)
    finally:
        # Move original files to completed directory after successful upload
        if original_files_uploaded:
            for original_file in original_files_uploaded:
                try:
                    completed_path = aws.move_to_completed(original_file)
                    if completed_path:
                        echo(f"Moved {original_file.name} to completed directory")
                    else:
                        echo(
                            f"Warning: Could not move {original_file.name} to completed directory",
                            err=True,
                        )
                except Exception as e:
                    echo(
                        f"Warning: Error moving {original_file.name} to completed directory: {e}",
                        err=True,
                    )
        # Only delete compressed files that were successfully uploaded
        if files_uploaded_successfully:
            for file in files_uploaded_successfully:
                try:
                    os.remove(file)
                except Exception as e:
                    echo(f"Warning: Could not delete {file}: {e}", err=True)
        # Log files that failed to upload (kept for retry)
        failed_files = [
            f for f in files_created if f not in files_uploaded_successfully
        ]
        if failed_files:
            echo(
                f"Note: Compressed files kept for retry: {', '.join(failed_files)}",
                err=True,
            )
    return


@app.command()
def search(keyword: str) -> None:
    """
    Searches for files that contain the specified keyword in their names

    Args:
        keyword (str): The keyword to search for in file names
    """
    location = "global"
    # FileManager will use module-level logger if not provided
    file_mgmt = FileManager()
    files_result = aws.get_files(location=location)
    if isinstance(files_result, tuple):
        local_files, s3_keys = files_result
    else:
        local_files = []
        s3_keys = []
    echo(f"\nSearching `{location}` for keyword `{keyword}`...")
    local_matches = [
        file for file in local_files if file_mgmt.keyword_in_string(keyword, file)
    ]
    s3_matches = [
        file for file in s3_keys if file_mgmt.keyword_in_string(keyword, file)
    ]

    echo(f"total matches found = {str(len(local_matches) + len(s3_matches))}")
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
                content_length_gb = round(int(content_length or 0) / (1024**3), 2)

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
            download_resp: int = typer.prompt("Which file? [option #]", type=int)

            if check_selection(download_resp, list(doptions.keys())):
                aws.download(object_name=doptions[download_resp])
                return
            else:
                return

        if not typer.confirm("Check Status?", default=False):
            echo("Aborted.")
        else:
            status_resp: int = typer.prompt("Which file? [option #]", type=int)

            if check_selection(status_resp, list(doptions.keys())):
                aws.get_obj_head(object_name=doptions[status_resp])
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
        files_result = aws.get_files(location=location)
        if isinstance(files_result, tuple):
            local_files, s3_keys = files_result
        else:
            local_files = []
            s3_keys = []
    elif location == "local":
        files_result = aws.get_files(location=location)
        if isinstance(files_result, list):
            local_files = files_result
        else:
            local_files = []
        s3_keys = [""]
    elif location == "s3":
        files_result = aws.get_files(location=location)
        if isinstance(files_result, list):
            s3_keys = files_result
        else:
            s3_keys = []
        local_files = [""]

    echo()
    echo("Local Files...")

    for obj in local_files:
        echo(obj)

    echo()
    echo("Bucket Objects...")

    for obj in s3_keys:
        echo(obj)


def write_config(config: Any) -> None:
    """Write configuration interactively.

    Args:
        config: Config object
    """
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
    # Config will use module-level logger if not provided
    config_logger = logging.getLogger("mgmt.config")
    config = Config(logger=config_logger)

    if config.check_exists():
        config.load_env()
        config.print_current_config()

        if typer.confirm("Would you like to overwrite these settings?", default=False):
            echo("Overwriting")
            write_config(config)
    else:
        write_config(config)

    echo("Configuration complete.")


@app.command()
def log(
    tail: int = typer.Option(
        0,
        "--tail",
        "-n",
        help="Show only the last N lines of the log file",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow the log file (like tail -f)",
    ),
) -> None:
    """
    Display the log file contents.

    Args:
        tail: Show only the last N lines (0 = show all)
        follow: Follow the log file for new entries (like tail -f)
    """
    log_file = get_log_file_path()

    if not log_file.exists():
        echo(f"Log file not found: {log_file}", err=True)
        raise typer.Exit(1)

    try:
        if follow:
            # Follow mode - continuously read new lines
            echo(f"Following log file: {log_file}")
            echo("Press Ctrl+C to stop\n")
            try:
                with log_file.open(encoding="utf-8") as f:
                    # Go to end of file
                    f.seek(0, 2)
                    while True:
                        line = f.readline()
                        if line:
                            echo(line.rstrip())
                        else:
                            time.sleep(0.1)  # Small delay to avoid busy waiting
            except KeyboardInterrupt:
                echo("\nStopped following log file.")
        elif tail > 0:
            # Show last N lines
            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    echo(line.rstrip())
        else:
            # Show entire file
            with log_file.open(encoding="utf-8") as f:
                echo(f.read().rstrip())
    except Exception as e:
        echo(f"Error reading log file: {e}", err=True)
        raise typer.Exit(1) from None


def entry_point() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    entry_point()
