# media-mgmt-cli

[![PyPI](https://img.shields.io/pypi/v/media-mgmt-cli.svg)](https://pypi.org/project/media-mgmt-cli/)
[![Changelog](https://img.shields.io/github/v/release/william-cass-wright/media-mgmt-cli?include_prereleases&label=changelog)](https://github.com/william-cass-wright/media-mgmt-cli/releases)
[![Tests](https://github.com/william-cass-wright/media-mgmt-cli/workflows/Test/badge.svg)](https://github.com/william-cass-wright/media-mgmt-cli/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/william-cass-wright/media-mgmt-cli/blob/master/LICENSE)

## Summary

**A simple CLI to search and manage media assets in S3 and locally**

- [PyPI project](https://pypi.org/project/media-mgmt-cli})
- Based on cookiecutter template [william-cass-wright/click-app](https://github.com/william-cass-wright/click-app)
- Rewrite of original project [william-cass-wright/media_mgmt_cli](https://github.com/william-cass-wright/media_mgmt_cli)

## Installation

Install this tool using `pip`:

```bash
pip install media-mgmt-cli
```

## Usage

For help, run:

```bash
mmgmt --help
```

You can also use:

```bash
python -m media_mgmt_cli --help
```

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:

```bash
cd media-mgmt-cli
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
