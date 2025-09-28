"""
How to mock a boto3 client object/call
https://stackoverflow.com/a/37203856/14343465

Mocking boto3 S3 client method Python
https://stackoverflow.com/a/37144161/14343465
"""

from typing import Any, Dict

import boto3
import pytest
from botocore.exceptions import ParamValidationError
from botocore.stub import Stubber


def test_boto3_s3() -> None:
    client = boto3.client("s3")
    stubber = Stubber(client)
    list_buckets_response: Dict[str, Any] = {
        "Owner": {"DisplayName": "name", "ID": "EXAMPLE123"},
        "Buckets": [{"CreationDate": "2016-05-25T16:55:48.000Z", "Name": "foo"}],
    }
    expected_params: Dict[str, Any] = {}
    stubber.add_response("list_buckets", list_buckets_response, expected_params)
    with stubber:
        response = client.list_buckets()
    assert response == list_buckets_response


def test_boto3_error() -> None:
    client = boto3.client("s3")
    stubber = Stubber(client)
    stubber.add_client_error("upload_part_copy")
    stubber.activate()
    try:
        client.upload_part_copy()
        pytest.fail("Should have raised ClietError")
    except ParamValidationError:
        assert 0 == 0
