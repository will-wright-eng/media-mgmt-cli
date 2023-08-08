# Media Management Command Line Interface

[![PyPI](https://img.shields.io/pypi/v/mgmt)](https://pypi.org/project/mgmt/)
[![Downloads](https://static.pepy.tech/badge/mgmt/month)](https://pepy.tech/project/mgmt)
[![Supported Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://pypi.org/project/mgmt/)
[![Contributors](https://img.shields.io/github/contributors/will-wright-eng/media-mgmt-cli.svg)](https://github.com/will-wright-eng/media-mgmt-cli/graphs/contributors)
[![Tests](https://github.com/will-wright-eng/media-mgmt-cli/workflows/Test/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions?query=workflow%3ATest)
[![Codeball](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml)


## Summary

**An intuitive command line interface that wraps boto3 to search and manage media assets**

## Installing `mgmt` & Supported Versions

`mgmt` is available on PyPI:

```bash
python -m pip install mgmt
```

Media Management Command Line Interface officially supports Python 3.8+.

## Supported Features & Usage

For help, run:

```bash
mgmt --help
```

Commands:

```bash
➜ mgmt --help

 Usage: mgmt [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version          Show the version and exit.                                                                   │
│ --help             Show this message and exit.                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ config        Configures the application                                                                        │
│ delete        Deletes the specified file from S3; requires confirmation                                         │
│ download      Downloads the specified file from S3                                                              │
│ ls            Lists the files in the specified location                                                         │
│ search        Searches for files that contain the specified keyword in their names                              │
│ status        Retrieves and prints the metadata of the specified file                                           │
│ upload        Uploads the specified file to S3                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Why not use `awscli`?

You can, and I do, in tandem with `mgmt` -- the purpose is to create an additional interface that minimized the lookup/copy/paste process I found myself frequently going through

## Development

To contribute to this tool, first checkout the code:

```bash
git clone https://github.com/will-wright-eng/media-mgmt-cli.git
cd media-mgmt-cli
```

Then create a new virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:

```bash
pip install -e '.[test]'
```

To run the tests:

```bash
pytest
```

Install pre-commit before submitting a PR:

```bash
brew install pre-commit
pre-commit install
```

## References

- [PyPI Package](https://pypi.org/project/mgmt)
- Based on cookiecutter template [will-wright-eng/click-app](https://github.com/will-wright-eng/click-app)
- Rewrite of original project [will-wright-eng/media_mgmt_cli](https://github.com/will-wright-eng/media_mgmt_cli)
