"""mmgmt cli docstring"""
import os
import json
from pathlib import Path
from typing import List

import click
import boto3

from .aws import aws
from .config import config_handler
import media_mgmt_cli.utils as utils


option_location = click.option("-l", "--location", "location", required=False, default="global")
option_bucket = click.option("-b", "--bucket-name","bucket_name", required=False, default=None)
option_filename = click.option("-f", "--filename", "filename", required=True)


@click.group()
@click.version_option()
def cli():
    "A simple CLI to search and manage media assets in S3 and locally"


# TODO: add check to see if zip file exists <-- this one
# or add flag that tells the control flow to skip the zip_process
# add clean_string method to zip_process method
# add filter to localfiles to exclude .DS_Store (all systems files)
@cli.command()
@option_filename
@click.option("-c", "--compression", "compression", required=False, default="gzip")
def upload(file_or_dir, compression):
    p = Path(".")
    localfiles = os.listdir(p)
    files_created = []
    try:
        if file_or_dir:
            if file_or_dir == "all":
                click.echo(f"uploading all media objects to S3")
                for _file_or_dir in localfiles:
                    click.echo(f"{_file_or_dir}, compressing...")
                    files_created.append(utils.upload_file_or_dir(_file_or_dir, compression))
            elif file_or_dir in localfiles:
                click.echo("file found, compressing...")
                files_created.append(utils.upload_file_or_dir(file_or_dir, compression))
            else:
                click.echo(f"invalid file or directory")
                return False
        else:
            click.echo("invalid file_or_dir command")
    except Exception as e:
        click.echo(e)
    finally:
        # remove all created files from dir
        if files_created:
            for file in files_created:
                os.remove(file)


@cli.command()
@click.option("-k", "--keyword", "keyword", required=True)
@option_location
# add verbose flag that outputs details on size, location, and full_path
# turn `matches` list into `output` list of dicts, appending info dict for each file
def search(keyword, location):
    files = utils.get_files(location=location)

    click.echo(f"Searching {location} for {keyword}...")
    matches = []
    for file in files:
        if utils.keyword_in_string(keyword, file):
            matches.append(file)

    if len(matches) >= 1:
        click.echo("at least one match found\n")
        click.echo("\n".join(matches))
        utils.get_storage_tier(matches)
        return True
    else:
        click.echo("no matches found\n")
        return False


@cli.command()
@option_filename
@option_bucket
def download(filename, bucket_name):
    click.echo(f"Downloading {filename} from S3...")
    aws.download_file(object_name=filename, bucket_name=bucket_name)


@cli.command()
@option_filename
def get_status(filename):
    aws.get_obj_head(object_name=filename)
    click.echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))


@cli.command()
@option_filename
@click.option(
    "--yes",
    is_flag=True,
    callback=utils.abort_if_false,
    expose_value=False,
    prompt=f"Are you sure you want to delete?",
)
def delete(filename):
    # use as test: media_uploads/Tron_Legacy_(2010)_BRRip_XvidHD_720p-NPW.zip
    click.echo(f"{filename} dropped from S3")
    click.echo("jk, command not yet complete")


@cli.command()
@option_location
@option_bucket
def ls(location, bucket_name):
    if bucket_name:
        files = aws.get_bucket_object_keys(bucket_name=bucket_name)
    else:
        if location in ("local", "s3", "global"):
            files = utils.get_files(location=location)
        elif location=="here":
            p = Path(".")
            files = os.listdir(p)
        else:
            click.echo(f"invalid location input: {location}")

    for file in files:
        click.echo(file)


# @cli.command()
# def configure():
#     if location == "local":
#         # grab values from ~/.config/media_mgmt_cli/config file
#         config = config_handler
#         config_dict = config.get_configs()
#         if config_dict is None:
#             current_values = [None] * int(len(config_list))
#         else:
#             current_values = [val for key, val in config_dict.items()]
#             config_list = [key.upper() for key, val in config_dict.items()]
#     elif location == "aws":
#         # grab values from projects/dev/media_mgmt_cli secrets string
#         pass
#     else:
#         config_list = [
#             "AWS_MEDIA_BUCKET",
#             "AWS_BUCKET_PATH",
#             "LOCAL_MEDIA_DIR",
#         ]
#         current_values = [None] * int(len(config_list))

#     res = {}
#     for config, current_value in zip(config_list, current_values):
#         value = click.prompt(f"{config} ", type=str, default=current_value)
#         res[config] = value

#     # value = click.prompt("kernal language? ", type=str, default='zsh')
#     # if value=='zsh':
#     #     subprocess.run(f'echo "" >> ~/.{value}rc')
#     #     subprocess.run(f'echo "source ~/.config/media_mgmt_cli/export.sh" >> ~/.{value}rc')
#     value = click.prompt("export to AWS Secrets Manager? [Y/n]", type=str)
#     if value.lower() == "y":
#         # export to AWS
#         pass
