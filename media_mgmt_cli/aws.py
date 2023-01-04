"""
boto3 wrapper around AWS S3

- boto3.resource("s3")
- boto3.client("s3")

https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html

TODO: split out base class and add GCP functionality
"""

import os
import json
from time import sleep
from typing import List

import boto3
import click
from click import echo
from botocore.exceptions import ClientError

from media_mgmt_cli.utils import zip_process, gzip_process, files_in_media_dir
from media_mgmt_cli.config import ConfigHandler

PROJECT_NAME = "media_mgmt_cli"


class AwsStorageMgmt:
    def __init__(self, project_name: str = PROJECT_NAME):
        self.s3_resour = boto3.resource("s3")
        self.s3_client = boto3.client("s3")

        self.config = ConfigHandler(project_name)
        self.configs = None
        self.bucket = None
        self.object_prefix = None
        self.local_dir = None

        self.atts_list = ["bucket", "object_prefix", "local_dir"]
        self.load_config_file()

    def load_config_file(self):
        if self.config.check_config_exists():
            self.configs = self.config.get_configs()
            atts_dict = {att: self.configs.get(att, None) for att in self.atts_list}
            self.__dict__.update(atts_dict)
            if self.bucket is None or self.object_prefix is None or self.local_dir is None:
                echo("at least one config not found, use self.set_config_manually()")
        else:
            echo("config file not found, run `mmgmt config` to set class attributes manually")

    def set_config_manually(self, atts_dict: dict = None) -> None:
        if not atts_dict:
            atts_dict = {}
            for att in self.atts_list:
                val = click.prompt(f"set {att}", type=str, default=self.__dict__.get(att))
                val = None if val == "None" else val
                atts_dict.update({att: val})

        self.__dict__.update(atts_dict)
        if self.configs:
            self.configs.update(atts_dict)
        else:
            self.configs = atts_dict

    def get_configs(self):
        return self.configs

    def upload_file(self, file_name, additional_prefix=None):
        """Upload a file to an S3 bucket
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param additional_prefix: additional prefix on top of config prefix
        :return: True if file was uploaded, else False
        """
        if additional_prefix and self.object_prefix:
            object_name = os.path.join(self.object_prefix, additional_prefix, file_name)
        elif self.object_prefix:
            object_name = os.path.join(self.object_prefix, file_name)
        else:
            object_name = file_name

        echo(f"uploading: {file_name} \nto S3 bucket: {self.bucket}/{object_name}")

        try:
            with open(file_name, "rb") as data:
                self.s3_client.upload_fileobj(data, self.bucket, object_name)
        except ClientError as e:
            echo(e)
            echo("success? False\n")
            return False
        echo("success? True\n")
        return True

    def download_file(self, object_name: str, bucket_name: str = None):
        """Download file from S3 to local
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-download-file.html

        :param bucket: Bucket to download from
        :param object_name:
        :return: True if file was uploaded, else False
        """
        if not bucket_name:
            bucket_name = self.bucket

        echo(f"download {object_name}\n from {bucket_name}")
        file_name = object_name.split("/")[-1]
        try:
            with open(file_name, "wb") as data:
                self.s3_client.download_fileobj(bucket_name, object_name, data)
        except ClientError as e:
            echo(e)
            echo("success? False --> ClietError")
            os.remove(file_name)
            status = self.get_obj_restore_status(object_name)
            if status == "incomplete":
                echo("restore in process")
                echo(json.dumps(aws.obj_head, indent=4, sort_keys=True, default=str))
            elif e.response["Error"]["Code"] == "InvalidObjectState":
                self.download_from_glacier(object_name=object_name)
                return True
            return False
        echo("success? True")
        return True

    def get_bucket_objs(self, bucket_name=None):
        if not bucket_name:
            bucket_name = self.bucket
        echo(f"bucket = {bucket_name}")
        my_bucket = self.s3_resour.Bucket(bucket_name)
        print(my_bucket)
        return [obj for obj in my_bucket.objects.all()]

    def get_bucket_obj_keys(self):
        return [obj.key for obj in self.get_bucket_objs()]

    def get_obj_head(self, object_name: str):
        response = self.s3_client.head_object(
            Bucket=self.bucket,
            Key=object_name,
        )
        self.obj_head = response
        return response

    def get_obj_restore_status(self, object_name):
        """check_obj_status docstring
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.head_object

        :param file_name: download to this file name
        :param bucket: Bucket to download from
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        response = self.get_obj_head(object_name)
        try:
            resp_string = response["Restore"]
            echo(resp_string)
            if ("ongoing-request" in resp_string) and ("true" in resp_string):
                status = "incomplete"
            elif ("ongoing-request" in resp_string) and ("false" in resp_string):
                status = "complete"
            else:
                status = "unknown"
        except Exception as e:
            status = str(e)
        echo(status)
        return status

    def restore_from_glacier(self, object_name: str, restore_tier: str):
        """Restore object from Glacier tier for download
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.restore_object

        :param bucket: Bucket to download from
        :param object_name: S3 object name
        :return:
        """
        response = self.s3_client.restore_object(
            Bucket=self.bucket,
            Key=object_name,
            RestoreRequest={
                "Days": 10,
                "GlacierJobParameters": {
                    "Tier": restore_tier,
                },
            },
        )
        return response

    def download_from_glacier(self, object_name: str):
        """download_from_glacier docstring"""
        self.get_obj_head(object_name)
        try:
            tier = self.obj_head["StorageClass"]
            if tier == "DEEP_ARCHIVE":
                restore_tier = "Standard"
            elif tier == "GLACIER":
                restore_tier = "Expedited"
        except KeyError as e:
            echo(f"KeyError: {str(e)}, object not in glacier storage -- check control flow")
            return

        echo(f"restoring object from {tier}: {object_name}")
        self.restore_from_glacier(object_name=object_name, restore_tier=restore_tier)
        if tier == "GLACIER":
            restored = False
            while restored is False:
                sleep(30)
                echo("checking...")
                status = self.get_obj_restore_status(object_name)
                if status == "incomplete":
                    pass
                elif status == "complete":
                    echo("restored = True")
                    restored = True
                else:
                    echo(f"status: {status}, exiting...")
                    return

            echo("downloading restored file")
            return self.download_file(object_name=object_name)
        else:
            echo(f"object in {tier}, object will be restored in 12-24 hours")
            return

    def upload_file_or_dir(self, file_or_dir, compression):
        if compression == "zip":
            file_created = zip_process(file_or_dir)
        elif compression == "gzip":
            file_created = gzip_process(file_or_dir)
        self.upload_file(file_name=file_created)
        return file_created

    def get_files(self, location: str):
        """
        location: local, s3, global
        [global] returns a combined list of files in local media dir and S3 media bucket
        """
        if location == "local" and self.local_dir:
            files = files_in_media_dir(local_path=self.local_dir)
        elif location == "s3":
            files = self.get_bucket_obj_keys()
        elif location == "global":
            files = files_in_media_dir(local_path=self.local_dir) + self.get_bucket_obj_keys()
        else:
            echo("invalid location")
            return False
        return files

    def search_flow(self, file_list: List[str]):
        if click.confirm("\nDisplay storage tier?"):
            echo("\nStorage Tier | Last Modfied | Object Key\n")
            for i, file_name in enumerate(file_list):
                try:
                    resp = self.get_obj_head(file_name)
                    try:
                        restored = resp["Restore"]
                        if restored:
                            restored = True
                    except KeyError:
                        restored = False
                    try:
                        echo(f"[{i}] {resp['StorageClass']} \t| {resp['LastModified']} \t| {file_name}")
                    except KeyError:
                        echo(f"[{i}] STANDARD \t| {resp['LastModified']} \t| {file_name}")
                except Exception:
                    echo(f"Exception getting object head for '{file_name}'; skipping")
        if click.confirm("\nDownload?"):
            resp = click.prompt("Which file? [#]", type=int)
            self.download_file(file_list[resp])


aws = AwsStorageMgmt()
