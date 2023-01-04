"""
aws.__dir__()

['s3_resour',
 's3_client',
 'config',
 'configs',
 'bucket',
 'object_prefix',
 'local_media_dir',
 'atts_list',
 'settings_list',
 '__module__',
 '__init__',
 'load_configs',
 'set_config_manually',
 'upload_file',
 'download_file',
 'get_bucket_objs',
 'get_bucket_obj_keys',
 'get_obj_head',
 'get_obj_restore_status',
 'restore_from_glacier',
 'download_from_glacier',
 'upload_file_or_dir',
 'get_files',
 'get_storage_tier']
"""

from media_mgmt_cli.aws import AwsStorageMgmt


def test_aws_config_flow():
    aws = AwsStorageMgmt()
    aws.set_config_manually(atts_dict={"key": "val"})
    result = aws.get_configs()
    assert isinstance(result, dict)
    assert result.get("key") == "val"
