import os

from setuptools import setup

VERSION = "0.3.3"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="mmgmt",
    description="A simple CLI to search and manage media assets in S3 and locally",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Will Wright",
    url="https://github.com/will-wright-eng/media-mgmt-cli",
    project_urls={
        "Issues": "https://github.com/will-wright-eng/media-mgmt-cli/issues",
        "CI": "https://github.com/will-wright-eng/media-mgmt-cli/actions",
        "Changelog": "https://github.com/will-wright-eng/media-mgmt-cli/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["mmgmt"],
    entry_points="""
        [console_scripts]
        mmgmt=mmgmt.cli:cli
    """,
    install_requires=["click", "boto3"],
    extras_require={"test": ["pytest"]},
    python_requires=">=3.7",
)
