from mmgmt.aws import AwsStorageMgmt as AwsStorageMgmt
from mmgmt.config import ConfigHandler as ConfigHandler

__docformat__ = "restructuredtext"

"""
As per PEP 287, example:

This is a reST style.

:param param1: this is a first param
:param param2: this is a second param
:returns: this is a description of what is returned
:raises keyError: raises an exception
"""

# module level doc-string
# https://stackoverflow.com/questions/3898572/what-are-the-most-common-python-docstring-formats
__doc__ = """
mmgmt - an intuitive cli wrapper around boto3 to search and manage media assets
=====================================================================
**mmgmt** (Media Management Command Line Interface) is a Python package for a unified interface
to assets and objects, both local and within cloud storage.
Features
-------------
- A central feature is the config handler that provides a gloabally aware interface
"""

# Use __all__ to let type checkers know what is part of the public API.
# Pandas is not (yet) a py.typed library: the public API is determined
# based on the documentation.
__all__ = [
    "AwsStorageMgmt",
    "ConfigHandler",
]
