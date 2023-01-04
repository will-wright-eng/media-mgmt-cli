"""mmgmt cli docstring"""
import os
import json
from pathlib import Path

import click
from click import echo

import media_mgmt_cli.utils as utils
from media_mgmt_cli.aws import aws

option_location = click.option("-l", "--location", "location", required=False, default="global")
option_bucket = click.option("-b", "--bucket-name", "bucket_name", required=False, default=None)
arg_filename = click.argument("filename", required=True)

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def echo_dict(input_dict: dict) -> None:
    for key, val in input_dict.items():
        echo(f"{key[:18]+'..' if len(key)>17 else key}{(20-int(len(key)))*'.'}{val}")


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def cli():
    "A simple CLI to search and manage media assets in S3 and locally"


@cli.command()
@arg_filename
@click.option("-c", "--compression", "compression", required=False, default="gzip")
def upload(filename, compression):
    """
    standard usage: mmgmt upload -f all -c gzip
    """
    file_or_dir = filename
    p = Path(".")
    localfiles = os.listdir(p)
    files_created = []
    try:
        if file_or_dir:
            if file_or_dir == "all":
                echo(f"uploading all media objects to S3")
                for _file_or_dir in localfiles:
                    echo(f"{_file_or_dir}, compressing...")
                    files_created.append(aws.upload_file_or_dir(_file_or_dir, compression))
            elif file_or_dir in localfiles:
                echo("file found, compressing...")
                files_created.append(aws.upload_file_or_dir(file_or_dir, compression))
            else:
                echo(f"invalid file or directory")
                return False
        else:
            echo("invalid file_or_dir command")
    except Exception as e:
        echo(e)
    finally:
        # remove all created files from dir
        if files_created:
            for file in files_created:
                os.remove(file)


@cli.command()
@click.option("-k", "--keyword", "keyword", required=True)
@option_location
def search(keyword, location):
    """
    search files in local directory and cloud storage
    """
    files = aws.get_files(location=location)

    echo(f"Searching {location} for {keyword}...")
    matches = []
    for file in files:
        if utils.keyword_in_string(keyword, file):
            matches.append(file)

    if len(matches) >= 1:
        echo("at least one match found\n")
        echo("\n".join(matches))
        aws.get_storage_tier(matches)
        return True
    else:
        echo("no matches found\n")
        return False


@cli.command()
@arg_filename
@option_bucket
def download(filename, bucket_name):
    """
    search files in local directory and cloud storage
    """
    echo(f"Downloading {filename} from S3...")
    aws.download_file(object_name=filename, bucket_name=bucket_name)


@cli.command()
@arg_filename
def get_status(filename):
    """
    search files in local directory and cloud storage
    """
    aws.get_obj_head(object_name=filename)
    echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))


@cli.command()
@arg_filename
@click.option(
    "--yes",
    is_flag=True,
    callback=utils.abort_if_false,
    expose_value=False,
    prompt=f"Are you sure you want to delete?",
)
def delete(filename):
    """
    delete file from cloud storage
    """
    echo(f"{filename} dropped from S3")
    echo("jk, command not yet complete")


@cli.command()
@option_location
@option_bucket
def ls(location, bucket_name):
    """
    list files in location (local, s3, or global; defaults to global)
    """
    if bucket_name:
        files = aws.get_bucket_obj_keys(bucket_name=bucket_name)
    else:
        if location in ("local", "s3", "global"):
            files = aws.get_files(location=location)
        elif location == "here":
            p = Path(".")
            files = os.listdir(p)
        else:
            echo(f"invalid location input: {location}")

    for file in files:
        echo(file)


@cli.command()
def config():
    """
    print project configs
    """
    echo_dict(aws.configs)
    aws.set_config_manually()
