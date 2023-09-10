from unittest.mock import MagicMock

import pytest

from mgmt import AwsStorageMgmt


@pytest.fixture
def aws_storage_mgmt():
    return AwsStorageMgmt()


def test_load_config_file(aws_storage_mgmt):
    aws_storage_mgmt.config.check_exists = MagicMock(return_value=True)
    aws_storage_mgmt.config.get_configs = MagicMock(
        return_value={"MGMT_BUCKET": "test-bucket", "MGMT_OBJECT_PREFIX": "test-prefix", "MGMT_LOCAL_DIR": "test-dir"}
    )
    aws_storage_mgmt.load_config_file()
    assert aws_storage_mgmt.bucket == "test-bucket"
    assert aws_storage_mgmt.object_prefix == "test-prefix"
    assert aws_storage_mgmt.local_dir == "test-dir"


def test_load_config_file_not_found(aws_storage_mgmt):
    aws_storage_mgmt.config.check_exists = MagicMock(return_value=False)
    aws_storage_mgmt.logger.debug = MagicMock()
    aws_storage_mgmt.load_config_file()
    aws_storage_mgmt.logger.debug.assert_called_with(
        "Config file not found. Please run `mgmt config` to set up the configuration."
    )


def test_upload_file(aws_storage_mgmt):
    aws_storage_mgmt.logger.debug = MagicMock()
    aws_storage_mgmt.logger.info = MagicMock()
    aws_storage_mgmt.s3_client.upload_fileobj = MagicMock()
    aws_storage_mgmt.upload_file("tests/test-file.txt")
    aws_storage_mgmt.logger.debug.assert_called_with("upload_file")
    aws_storage_mgmt.logger.info.assert_called_with("File Upload: test-file.txt")
    aws_storage_mgmt.logger.info.assert_called_with("S3 Location: test-bucket/test-prefix/test-file.txt")
    aws_storage_mgmt.s3_client.upload_fileobj.assert_called_with(
        "test-file.txt", "test-bucket", "test-prefix/test-file.txt"
    )


"""
How to mock a boto3 client object/call
https://stackoverflow.com/a/37203856/14343465

Mocking boto3 S3 client method Python
https://stackoverflow.com/a/37144161/14343465
"""

# import boto3
# import pytest
# from botocore.stub import Stubber
# from botocore.exceptions import ParamValidationError


# def test_boto3_s3():
#     client = boto3.client("s3")
#     stubber = Stubber(client)
#     list_buckets_response = {
#         "Owner": {"DisplayName": "name", "ID": "EXAMPLE123"},
#         "Buckets": [{"CreationDate": "2016-05-25T16:55:48.000Z", "Name": "foo"}],
#     }
#     expected_params = {}
#     stubber.add_response("list_buckets", list_buckets_response, expected_params)
#     with stubber:
#         response = client.list_buckets()
#     assert response == list_buckets_response


# def test_boto3_error():
#     client = boto3.client("s3")
#     stubber = Stubber(client)
#     stubber.add_client_error("upload_part_copy")
#     stubber.activate()
#     try:
#         client.upload_part_copy()
#         pytest.fail("Should have raised ClietError")
#     except ParamValidationError:
#         assert 0 == 0
