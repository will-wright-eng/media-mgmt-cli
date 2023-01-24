# Media Management Command Line Interface

[![PyPI](https://img.shields.io/pypi/v/mmgmt)](https://pypi.org/project/mmgmt/)
[![Downloads](https://static.pepy.tech/badge/media-mgmt-cli/month)](https://pepy.tech/project/media-mgmt-cli)
[![Supported Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://pypi.org/project/mmgmt/)
[![Contributors](https://img.shields.io/github/contributors/will-wright-eng/media-mgmt-cli.svg)](https://github.com/will-wright-eng/media-mgmt-cli/graphs/contributors)
[![Tests](https://github.com/will-wright-eng/media-mgmt-cli/workflows/Test/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions?query=workflow%3ATest)
[![Codeball](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml)

## Summary

**An intuitive command line interface wrapper around boto3 to search and manage media assets**

## Installing `mmgmt` & Supported Versions

`mmgmt` is available on PyPI:

```bash
python -m pip install mmgmt
```

Media Management Command Line Interface officially supports Python 3.8+.

## Supported Features & Usage

For help, run:

```bash
mmgmt --help
```

You can also use:

```bash
python -m mmgmt --help
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

Why not use `awscli`?

You can, and I do, in tandem with `mmgmt` -- the purpose is to create an additional interface that minimized the lookup/copy/paste process I found myself frequently going through.

Another use case is for rapid prototyping applications that require an S3 interface.

For example:

```python
import pandas as pd
import mmgmt as mmgmt

aws = mmgmt.AwsStorageMgmt(project_name="mmgmt")
obj_list = aws.get_bucket_objs()

res = []
for s3_obj in obj_list:
    res.append(
      [
        str(s3_obj.key),
        str(s3_obj.key.split('/')[0]),
        s3_obj.last_modified,
        s3_obj.storage_class,
        s3_obj.size
      ]
    )

df = pd.DataFrame(res)
df.columns = [
  'key',
  'group',
  'last_modified',
  'storage_class',
  'size'
]
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

## References

- [PyPI Package](https://pypi.org/project/mmgmt)
- Based on cookiecutter template [will-wright-eng/click-app](https://github.com/will-wright-eng/click-app)
- Rewrite of original project [will-wright-eng/media_mgmt_cli](https://github.com/will-wright-eng/media_mgmt_cli)
