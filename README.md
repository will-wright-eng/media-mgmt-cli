# Media MGMT CLI

[![PyPI](https://img.shields.io/pypi/v/media-mgmt-cli.svg)](https://pypi.org/project/media-mgmt-cli/)
[![Changelog](https://img.shields.io/github/v/release/william-cass-wright/media-mgmt-cli?include_prereleases&label=changelog)](https://github.com/william-cass-wright/media-mgmt-cli/releases)
[![Tests](https://github.com/william-cass-wright/media-mgmt-cli/workflows/Test/badge.svg)](https://github.com/william-cass-wright/media-mgmt-cli/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/william-cass-wright/media-mgmt-cli/blob/master/LICENSE)
[![Downloads](https://static.pepy.tech/badge/media-mgmt-cli/month)](https://pepy.tech/project/media-mgmt-cli)
[![Supported Versions](https://img.shields.io/pypi/pyversions/media-mgmt-cli.svg)](https://pypi.org/project/media-mgmt-cli)
[![Contributors](https://img.shields.io/github/contributors/will-wright-eng/media-mgmt-cli.svg)](https://github.com/will-wright-eng/media-mgmt-cli/graphs/contributors)
[![Codeball](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml)

## Summary

**A simple CLI to search and manage media asset locally and in S3**

- [PyPI project](https://pypi.org/project/media-mgmt-cli)
- Based on cookiecutter template [william-cass-wright/click-app](https://github.com/william-cass-wright/click-app)
- Rewrite of original project [william-cass-wright/media_mgmt_cli](https://github.com/william-cass-wright/media_mgmt_cli)

## Installing Media MGMT CLI and Supported Versions

mmgmt is available on PyPI:

```bash
python -m pip install media-mgmt-cli
```

Media MGMT CLI officially supports Python 3.8+.

## Supported Features & Best–Practices

For help, run:

```bash
mmgmt --help
```

You can also use:

```bash
python -m media_mgmt_cli --help
```

Commands:

```bash
Usage: mmgmt [OPTIONS] COMMAND [ARGS]...

  A simple CLI to search and manage media assets in S3 and locally. Setup with
  `mmgmt configure`

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  configure   print project configs & set configs manually
  delete      delete file from cloud storage - TODO -
  download    download object from cloud storage
  get-status  get object head from cloud storage
  hello       test endpoint
  ls          list files in location (local, s3, or global)
  search      search files in local directory and cloud storage
  upload      upload file to cloud storage
```

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
