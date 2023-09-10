import os

import pytest
from typer.testing import CliRunner

from mgmt.app import app

runner = CliRunner()


def test_upload_all():
    with runner.isolated_filesystem():
        # Create some test files
        os.makedirs("test_dir")
        with open("test_dir/file1.txt", "w") as f:
            f.write("Test file 1")
        with open("test_dir/file2.txt", "w") as f:
            f.write("Test file 2")

        # Run the upload command
        result = runner.invoke(app, ["upload", "all"])

        # Assert the expected output or behavior
        assert result.exit_code == 0
        assert "uploading all media objects to S3" in result.output
        # Add more assertions as needed


def test_search():
    with runner.isolated_filesystem():
        # Create some test files
        with open("file1.txt", "w") as f:
            f.write("Test file 1")
        with open("file2.txt", "w") as f:
            f.write("Test file 2")

        # Run the search command
        result = runner.invoke(app, ["search", "file"])

        # Assert the expected output or behavior
        assert result.exit_code == 0
        assert "total matches found" in result.output
        # Add more assertions as needed


# @pytest.fixture
# def runner():
#     return CliRunner()


# def test_upload(mocker):
#     mock_aws = mocker.patch("mgmt.aws.AwsStorageMgmt")
#     mock_aws.upload_file_or_dir.return_value = "test_file.gz"
#     runner = CliRunner()
#     result = runner.invoke(app, ["upload", "test_file", "--compression", "gzip"])
#     mock_aws.upload_file_or_dir.assert_called_once_with("test_file", "gzip")
#     assert result.exit_code == 0


# def test_download(mocker):
#     mock_aws = mocker.patch("mgmt.aws.AwsStorageMgmt")
#     mock_aws.download_standard.return_value = "test_file"
#     runner = CliRunner()
#     result = runner.invoke(app, ["download", "test_file", "--bucket_name", "test_bucket"])
#     mock_aws.download_standard.assert_called_once_with("test_file", "test_bucket")
#     assert result.exit_code == 0


# def test_search(mocker):
#     mock_file_mgmt = mocker.patch("mgmt.files.FileManager")
#     mock_aws = mocker.patch("mgmt.aws.AwsStorageMgmt")
#     mock_aws.get_files.return_value = (["test_file"], ["s3_test_file"])
#     mock_file_mgmt.keyword_in_string.return_value = True
#     runner = CliRunner()
#     result = runner.invoke(app, ["search", "test", "--location", "global"])
#     mock_aws.get_files.assert_called_once_with(location="global")
#     mock_file_mgmt.keyword_in_string.assert_called()
#     assert result.exit_code == 0


# def test_delete(mocker):
#     mock_aws = mocker.patch("mgmt.aws.AwsStorageMgmt")
#     mock_aws.delete_file.return_value = None
#     with mocker.patch("mgmt.app.typer.confirm", return_value=True):
#         runner = CliRunner()
#         result = runner.invoke(app, ["delete", "test_file"])
#     mock_aws.delete_file.assert_called_once_with("test_file")
#     assert result.exit_code == 0
