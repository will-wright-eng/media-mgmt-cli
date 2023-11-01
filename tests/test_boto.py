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
