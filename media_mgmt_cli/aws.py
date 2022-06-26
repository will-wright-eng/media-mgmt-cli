"""
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
"""

import os
import json
import base64
import pathlib
import configparser
from time import sleep

import boto3
from click import echo
from botocore.exceptions import ClientError

from .config import ConfigHandler


class AwsStorageMgmt:
    def __init__(self):
        self.s3_resour = boto3.resource("s3")
        self.s3_client = boto3.client("s3")
        self.config = ConfigHandler(project_name="media_mgmt_cli")
        if self.config.check_config_exists():
            self.configs = self.config.get_configs()
            self.bucket = self.configs.get("aws_bucket", None)
            self.object_prefix = self.configs.get("aws_bucket_path", None)
        else:
            echo("config file does not exist, run `mmgmt configure`")

    def upload_file(self, file_name, object_name=None):
        """Upload a file to an S3 bucket
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        echo(
            f"uploading: {file_name} \nto S3 bucket: {self.configs.get('aws_bucket')}/{self.configs.get('aws_bucket_path')}/{file_name}"
        )
        if not object_name:
            object_name = os.path.join(self.object_prefix, file_name)
        else:
            object_name = os.path.join(object_name, file_name)

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

        :param file_name: download to this file name
        :param bucket: Bucket to download from
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        if not bucket_name:
            bucket_name = self.bucket

        file_name = object_name.split("/")[-1]
        try:
            with open(file_name, "wb") as data:
                self.s3_client.download_fileobj(bucket_name, object_name, data)
        except ClientError as e:
            echo("success? False")
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

    def get_bucket_object_keys(self, bucket_name=None):
        if not bucket_name:
            bucket_name = self.configs.get("aws_media_bucket")
        echo(f"aws_media_bucket = {bucket_name}")
        my_bucket = self.s3_resour.Bucket(bucket_name)
        return [obj.key for obj in my_bucket.objects.all()]

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
            while restored == False:
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


aws = AwsStorageMgmt()
