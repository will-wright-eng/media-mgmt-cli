import os
from time import sleep
from typing import List
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from mmgmt.log import Log
from mmgmt.files import FileManager
from mmgmt.config import Config

logger = Log(debug=True)


class AwsStorageMgmt:
    def __init__(self):
        self.s3_resource = boto3.resource("s3")
        self.s3_client = boto3.client("s3")
        self.config = Config()
        self.load_config_file()

    def load_config_file(self):
        if self.config.check_exists():
            configs = self.config.get_configs()
            self.bucket = configs.get("bucket")
            self.object_prefix = configs.get("object_prefix")
            self.local_dir = configs.get("local_dir")
            self.file_mgmt = FileManager(self.local_dir)
        else:
            logger.info("Config file not found. Please run `mmgmt config` to set up the configuration.")

    def upload_file(self, file_name, additional_prefix=None) -> bool:
        object_name = file_name
        if self.object_prefix:
            object_name = os.path.join(self.object_prefix, additional_prefix or "", file_name)

        logger.info(f"Uploading: {file_name} to S3 bucket: {self.bucket}/{object_name}")
        try:
            with open(file_name, "rb") as data:
                self.s3_client.upload_fileobj(data, self.bucket, object_name)
        except ClientError as e:
            logger.error(e)
            return False
        return True

    def download_file(self, object_name: str, bucket_name: str = None) -> bool:
        if not bucket_name:
            bucket_name = self.bucket
        logger.info(f"Downloading `{object_name}` from `{bucket_name}`")
        file_name = object_name.split("/")[-1]
        try:
            with open(file_name, "wb") as data:
                self.s3_client.download_fileobj(bucket_name, object_name, data)
        except ClientError as e:
            logger.error(f"-- ClientError --\n{str(e)}")
            os.remove(file_name)
            return False
        return True

    def get_bucket_objs(self, bucket_name=None):
        if not bucket_name:
            bucket_name = self.bucket
        logger.info(f"bucket = {bucket_name}")
        my_bucket = self.s3_resource.Bucket(bucket_name)
        logger.info(my_bucket)
        return [obj for obj in my_bucket.objects.all()]

    def get_bucket_obj_keys(self):
        return [obj.key for obj in self.get_bucket_objs()]

    def get_obj_head(self, object_name: str):
        response = self.s3_client.head_object(
            Bucket=self.bucket,
            Key=object_name,
        )
        return response

    def get_obj_restore_status(self, object_name):
        response = self.get_obj_head(object_name)
        try:
            resp_string = response["Restore"]
            logger.info(resp_string)
            if "ongoing-request" in resp_string and "true" in resp_string:
                status = "incomplete"
            elif "ongoing-request" in resp_string and "false" in resp_string:
                status = "complete"
            else:
                status = "unknown"
        except Exception as e:
            status = str(e)
        logger.info(status)
        return status

    def restore_from_glacier(self, object_name: str, restore_tier: str):
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
        self.get_obj_head(object_name)
        try:
            tier = self.obj_head["StorageClass"]
            if tier == "DEEP_ARCHIVE":
                restore_tier = "Standard"
            elif tier == "GLACIER":
                restore_tier = "Expedited"
        except KeyError as e:
            logger.error(f"KeyError: {str(e)}, object not in glacier storage -- check control flow")
            return

        logger.info(f"restoring object from {tier}: {object_name}")
        self.restore_from_glacier(object_name=object_name, restore_tier=restore_tier)
        if tier == "GLACIER":
            restored = False
            while not restored:
                sleep(30)
                logger.info("checking...")
                status = self.get_obj_restore_status(object_name)
                if status == "incomplete":
                    pass
                elif status == "complete":
                    logger.info("restored = True")
                    restored = True
                else:
                    logger.info(f"status: {status}, exiting...")
                    return
            logger.info("downloading restored file")
            return self.download_file(object_name=object_name)
        else:
            logger.info(f"object in {tier}, object will be restored in 12-24 hours")
            return

    def upload_file_or_dir(self, file_or_dir, compression):
        if compression == "zip":
            file_created = self.file_mgmt.zip_process(file_or_dir)
        elif compression == "gzip":
            file_created = self.file_mgmt.gzip_process(file_or_dir)
        self.upload_file(file_name=file_created)
        return file_created

    def get_files(self, location: str):
        if location == "local" and self.local_dir:
            return self.file_mgmt.files_in_media_dir()
        elif location == "s3":
            return self.get_bucket_obj_keys()
        elif location == "global" and self.local_dir:
            return self.file_mgmt.files_in_media_dir(), self.get_bucket_obj_keys()
        else:
            logger.error("invalid location")
            logger.error(self.local_dir)
            return False
