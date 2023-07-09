from .app import entry_point as cli  # noqa: F401

__version__ = "0.6.2"
__docformat__ = "restructuredtext"

# module level doc-string
# https://stackoverflow.com/questions/3898572/what-are-the-most-common-python-docstring-formats
__doc__ = """
mgmt - an intuitive cli wrapper around boto3 to search and manage media assets
=====================================================================
**mgmt** (Media Management Command Line Interface) is a Python package for a unified interface
to assets and objects, both local and within cloud storage.
"""
