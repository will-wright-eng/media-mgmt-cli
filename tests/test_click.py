from click.testing import CliRunner

from mmgmt.cli import cli


def test_hello_world():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["hello", "will"])
        assert result.exit_code == 0
        assert result.output == "Hello Will\n"


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")
