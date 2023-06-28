import pytest
from mmgmt.app import app
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_upload(mocker):
    mock_aws = mocker.patch("mmgmt.aws.AwsStorageMgmt")
    mock_aws.upload_file_or_dir.return_value = "test_file.gz"
    runner = CliRunner()
    result = runner.invoke(app, ["upload", "test_file", "--compression", "gzip"])
    mock_aws.upload_file_or_dir.assert_called_once_with("test_file", "gzip")
    assert result.exit_code == 0


def test_download(mocker):
    mock_aws = mocker.patch("mmgmt.aws.AwsStorageMgmt")
    mock_aws.download_file.return_value = "test_file"
    runner = CliRunner()
    result = runner.invoke(app, ["download", "test_file", "--bucket_name", "test_bucket"])
    mock_aws.download_file.assert_called_once_with("test_file", "test_bucket")
    assert result.exit_code == 0


def test_search(mocker):
    mock_file_mgmt = mocker.patch("mmgmt.files.FileManager")
    mock_aws = mocker.patch("mmgmt.aws.AwsStorageMgmt")
    mock_aws.get_files.return_value = (["test_file"], ["s3_test_file"])
    mock_file_mgmt.keyword_in_string.return_value = True
    runner = CliRunner()
    result = runner.invoke(app, ["search", "test", "--location", "global"])
    mock_aws.get_files.assert_called_once_with(location="global")
    mock_file_mgmt.keyword_in_string.assert_called()
    assert result.exit_code == 0


def test_delete(mocker):
    mock_aws = mocker.patch("mmgmt.aws.AwsStorageMgmt")
    mock_aws.delete_file.return_value = None
    with mocker.patch("mmgmt.app.typer.confirm", return_value=True):
        runner = CliRunner()
        result = runner.invoke(app, ["delete", "test_file"])
    mock_aws.delete_file.assert_called_once_with("test_file")
    assert result.exit_code == 0
