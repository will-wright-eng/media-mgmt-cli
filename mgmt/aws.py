import os
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Optional, Tuple, Union

import boto3
from botocore.exceptions import ClientError

from mgmt.config import Config
from mgmt.files import FileManager
from mgmt.log import Log
from mgmt.utils import get_restore_status_short


class AwsStorageMgmt:
    def __init__(self) -> None:
        """Initialize the AWS Storage Management class."""
        self.s3_resource = boto3.resource("s3")
        self.s3_client = boto3.client("s3")
        self.config = Config()
        self.logger = Log(debug=True)
        self.file_mgmt: Optional[FileManager] = None
        self.load_config_file()

    def load_config_file(self) -> None:
        """Load configuration file and set up AWS storage parameters."""
        if self.config.check_exists():
            self.configs = self.config.get_configs()
            if self.configs:
                self.bucket = self.configs.get("MGMT_BUCKET")
                self.object_prefix = self.configs.get("MGMT_OBJECT_PREFIX")
                self.local_dir = self.configs.get("MGMT_LOCAL_DIR")
                if self.local_dir:
                    self.file_mgmt = FileManager(self.local_dir)
                else:
                    self.file_mgmt = None
            else:
                self.bucket = None
                self.object_prefix = None
                self.local_dir = None
                self.file_mgmt = None
        else:
            self.logger.debug(
                "Config file not found. Please run `mgmt config` to set up the configuration."
            )

    def upload_file(self, file_name: Union[str, Path]) -> bool:
        """Upload a file to S3"""
        self.logger.debug("upload_file")
        file_name_str = str(file_name)
        object_name = file_name_str.split("/")[-1]
        if self.object_prefix:
            object_name = os.path.join(self.object_prefix, object_name)

        self.logger.info(f"File Upload: {file_name}")
        self.logger.info(f"S3 Location: {self.bucket}/{object_name}")
        try:
            with open(file_name_str, "rb") as data:
                self.s3_client.upload_fileobj(data, self.bucket, object_name)
        except ClientError as e:
            self.logger.error(e)
            return False
        return True

    def download_standard(
        self, object_name: str, bucket_name: Optional[str] = None
    ) -> bool:
        """Download a file from S3 using standard storage"""
        if not bucket_name:
            bucket_name = self.bucket
        self.logger.info(f"Downloading `{object_name}` from `{bucket_name}`")
        file_name = object_name.split("/")[-1]
        try:
            with open(file_name, "wb") as data:
                self.s3_client.download_fileobj(bucket_name, object_name, data)
        except ClientError as e:
            self.logger.error(f"-- ClientError -- {str(e)}")
            os.remove(file_name)
            return False
        return True

    def get_bucket_objs(self, bucket_name: Optional[str] = None) -> List[Any]:
        """Get all objects from a bucket"""
        if not bucket_name:
            bucket_name = self.bucket
        self.logger.debug(f"bucket = {bucket_name}")
        my_bucket = self.s3_resource.Bucket(bucket_name)
        self.logger.debug(my_bucket)
        return list(my_bucket.objects.all())

    def get_bucket_obj_keys(self) -> List[str]:
        """Get all object keys from the configured bucket"""
        return [obj.key for obj in self.get_bucket_objs()]

    def get_obj_head(self, object_name: str) -> Dict[str, Any]:
        """Get object metadata from S3"""
        response = self.s3_client.head_object(
            Bucket=self.bucket,
            Key=object_name,
        )
        self.obj_head = response
        return response  # type: ignore[no-any-return]

    def get_obj_restore_status(self, object_name: str) -> str:
        """Get the restore status of an object"""
        self.get_obj_head(object_name)
        try:
            restore_status = self.obj_head.get("Restore")
            self.logger.debug(restore_status)
            status = get_restore_status_short(restore_status)
        except Exception as e:
            status = str(e)
        self.logger.debug(status)
        return status

    def restore_from_glacier(
        self, object_name: str, restore_tier: str
    ) -> Dict[str, Any]:
        """Restore an object from Glacier storage"""
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
        return response  # type: ignore[no-any-return]

    def download(self, object_name: str) -> Optional[bool]:
        """Download an object from S3, handling different storage classes"""
        self.logger.debug("download")
        self.get_obj_head(object_name)
        try:
            tier = self.obj_head.get("StorageClass", "STANDARD")
            restore_status = self.obj_head.get("Restore", "None")
            if (tier == "STANDARD") or (
                "ongoing-request" in restore_status and "false" in restore_status
            ):
                return self.download_standard(object_name=object_name)
            elif "ongoing-request" in restore_status and "true" in restore_status:
                self.logger.info("RestoreAlreadyInProgress")
                return None
            elif tier == "DEEP_ARCHIVE":
                restore_tier = "Standard"
            elif tier == "GLACIER":
                restore_tier = "Expedited"
        except KeyError as e:
            self.logger.error(
                f"KeyError: {str(e)}, object tier {tier} invalid OR restore in progress; restore status = {str(restore_status)}"
            )
            return None

        self.logger.debug(f"restoring object from {tier}: {object_name}")
        self.restore_from_glacier(object_name=object_name, restore_tier=restore_tier)
        if tier == "GLACIER":
            restored = False
            while not restored:
                sleep(30)
                self.logger.debug("checking...")
                status = self.get_obj_restore_status(object_name)
                if status == "incomplete":
                    pass
                elif status == "complete":
                    self.logger.debug("restored = True")
                    restored = True
                else:
                    self.logger.debug(f"status: {status}, exiting...")
                    return None
            self.logger.debug("downloading restored file")
            return self.download_standard(object_name=object_name)
        else:
            self.logger.debug(
                f"object in {tier}, object will be restored in 12-24 hours"
            )
            return None

    def upload_target(
        self, target_path: Union[str, Path], compression: Optional[str]
    ) -> str:
        """Upload a target (file or directory) with compression"""
        self.logger.debug(f"upload_target: {str(target_path)} {compression}")
        target_path_obj = Path(target_path)
        if not self.file_mgmt:
            raise ValueError("File manager not initialized")
        if compression == "zip":
            file_created = self.file_mgmt.zip_process(target_path_obj)
        elif compression == "gzip":
            self.logger.debug("gzip")
            file_created = self.file_mgmt.gzip_process(target_path_obj)
        else:
            raise ValueError("Invalid compression type")
        self.upload_file(file_name=file_created)
        return file_created

    def get_files(
        self, location: str
    ) -> Union[List[str], Tuple[List[str], List[str]], bool]:
        """Get files from specified location"""
        if location == "local" and self.local_dir and self.file_mgmt:
            return self.file_mgmt.files_in_media_dir()
        elif location == "s3":
            return self.get_bucket_obj_keys()
        elif location == "global" and self.local_dir and self.file_mgmt:
            return self.file_mgmt.files_in_media_dir(), self.get_bucket_obj_keys()
        else:
            self.logger.error("invalid location")
            self.logger.error(str(self.local_dir or ""))
            return False

    def list_func(self, location: str) -> List[str]:
        """List files in specified location"""
        file_list: List[str] = []
        if location in ("local", "s3", "global"):
            if location == "global":
                files_result = self.get_files(location=location)
                if isinstance(files_result, tuple):
                    local_files, s3_keys = files_result
                    file_list = local_files + s3_keys
                elif isinstance(files_result, list):
                    file_list = files_result
        elif location == "here":
            p = Path(".")
            file_list = os.listdir(p)
        else:
            self.logger.error("invalid location input")
            self.logger.error(location)
        return file_list

    def get_bucket_list(self) -> List[str]:
        """Get list of all S3 buckets"""
        response = self.s3_client.list_buckets()
        buckets = [bucket["Name"] for bucket in response["Buckets"]]
        return buckets

    def delete_file(self, filename: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=filename)
            return True
        except ClientError as e:
            self.logger.error(f"Failed to delete {filename}: {e}")
            return False
