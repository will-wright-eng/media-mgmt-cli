import pytest
from typer.testing import CliRunner

from mgmt.app import app


@pytest.fixture
def runner():
    return CliRunner()


def test_upload(mocker):
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.upload_target.return_value = "test_file.gz"
    runner = CliRunner()
    result = runner.invoke(
        app, ["upload", "--filename", "test_file", "--compression", "gzip"]
    )
    # Just check that upload_target was called once
    assert mock_aws.upload_target.call_count == 1
    assert result.exit_code == 0


def test_download(mocker):
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.download.return_value = "test_file"
    runner = CliRunner()
    result = runner.invoke(app, ["download", "test_file"])
    mock_aws.download.assert_called_once_with(object_name="test_file")
    assert result.exit_code == 0


def test_search(mocker):
    mock_file_mgmt = mocker.patch("mgmt.app.FileManager")
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.get_files.return_value = (["test_file"], ["s3_test_file"])
    mock_file_mgmt.keyword_in_string.return_value = True
    runner = CliRunner()
    result = runner.invoke(app, ["search", "test"])
    mock_aws.get_files.assert_called_once_with(location="global")
    mock_file_mgmt.keyword_in_string.assert_called()
    assert result.exit_code == 0


def test_delete(mocker):
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.delete_file.return_value = None
    mocker.patch("mgmt.app.typer.confirm", return_value=True)
    runner = CliRunner()
    result = runner.invoke(app, ["delete", "test_file"])
    mock_aws.delete_file.assert_called_once_with("test_file")
    assert result.exit_code == 0
