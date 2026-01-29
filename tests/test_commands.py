from typing import Any

import pytest
from typer.testing import CliRunner

from mgmt.app import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_upload(mocker: Any) -> None:
    mock_aws = mocker.patch("mgmt.app.aws")
    # Now always returns .tar.gz files (consistent for both files and directories)
    mock_aws.upload_target.return_value = "test_file.tar.gz"
    # Mock move_to_completed to return a path
    mock_aws.move_to_completed.return_value = mocker.MagicMock()
    # Mock Path operations to avoid file system issues
    mock_path = mocker.patch("mgmt.app.Path")
    mock_cwd = mocker.MagicMock()
    mock_cwd.resolve.return_value = mock_cwd
    mock_target_path = mocker.MagicMock()
    mock_target_path.exists.return_value = True
    mock_cwd.__truediv__.return_value = mock_target_path
    mock_cwd.iterdir.return_value = []
    mock_path.return_value = mock_cwd
    # Mock os.remove to avoid file system issues
    mocker.patch("os.remove")
    runner = CliRunner()
    result = runner.invoke(app, ["upload", "test_file"])
    # Just check that upload_target was called once
    assert mock_aws.upload_target.call_count == 1
    # Check that move_to_completed was called once
    assert mock_aws.move_to_completed.call_count == 1
    assert result.exit_code == 0


def test_download(mocker: Any) -> None:
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.download.return_value = "test_file"
    runner = CliRunner()
    result = runner.invoke(app, ["download", "test_file"])
    mock_aws.download.assert_called_once_with(object_name="test_file")
    assert result.exit_code == 0


def test_search(mocker: Any) -> None:
    mock_file_mgmt = mocker.patch("mgmt.app.FileManager")
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.get_files.return_value = (["test_file"], ["s3_test_file"])
    mock_file_mgmt_instance = mock_file_mgmt.return_value
    mock_file_mgmt_instance.keyword_in_string.return_value = True
    # Mock typer.confirm to avoid interactive prompts
    mocker.patch("mgmt.app.typer.confirm", return_value=False)
    runner = CliRunner()
    result = runner.invoke(app, ["search", "test"])
    mock_aws.get_files.assert_called_once_with(location="global")
    mock_file_mgmt_instance.keyword_in_string.assert_called()
    assert result.exit_code == 0


def test_delete(mocker: Any) -> None:
    mock_aws = mocker.patch("mgmt.app.aws")
    mock_aws.delete_file.return_value = None
    mocker.patch("mgmt.app.typer.confirm", return_value=True)
    runner = CliRunner()
    result = runner.invoke(app, ["delete", "test_file"])
    mock_aws.delete_file.assert_called_once_with("test_file")
    assert result.exit_code == 0
