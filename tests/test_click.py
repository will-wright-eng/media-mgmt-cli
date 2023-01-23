from click.testing import CliRunner

from mmgmt.cli import cli


def test_hello_world():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["hello", "--opt", "An Option", "An Arg"])
        assert result.exit_code == 0
        assert result.output == "Opt: An Option  Arg: An Arg\n"

        result = runner.invoke(cli, ["hello", "An Arg"])
        assert result.exit_code == 0
        assert result.output == "Opt: None  Arg: An Arg\n"
