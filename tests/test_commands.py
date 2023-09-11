import os

import pytest

# from pytest_mock import mocker
from typer.testing import CliRunner

from mgmt.app import app

runner = CliRunner()

# def test_upload_all():
#     with runner.isolated_filesystem():
#         # Create some test files
#         os.makedirs("test_dir")
#         with open("test_dir/file1.txt", "w") as f:
#             f.write("Test file 1")
#         with open("test_dir/file2.txt", "w") as f:
#             f.write("Test file 2")

#         # Run the upload command
#         result = runner.invoke(app, ["upload", "all"])

#         # Assert the expected output or behavior
#         assert result.exit_code == 0
#         assert "uploading all media objects to S3" in result.output
#         # Add more assertions as needed


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


# def test_upload(mocker):
#     mock_aws = mocker.patch("mgmt.aws.AwsStorageMgmt")
#     mock_aws.upload_target.return_value = "test_file.gz"
#     result = runner.invoke(app, ["upload", "test_file"])
#     mock_aws.upload_target.assert_called_once_with("test_file")
#     assert result.exit_code == 0

# def test_download(mocker):
#     mock_aws = mocker.patch("mgmt.aws.AwsStorageMgmt")
#     mock_aws.download.return_value = "test_file"
#     result = runner.invoke(app, ["download", "test_file"])
#     mock_aws.download.assert_called_once_with("test_file")
#     assert result.exit_code == 0
