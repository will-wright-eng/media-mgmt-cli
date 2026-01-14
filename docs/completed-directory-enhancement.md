# Completed Directory Enhancement Proposal

## Overview

This document proposes an enhancement to move successfully uploaded files to a "completed" directory, providing a clear audit trail and preventing duplicate uploads.

## Proposal

After a successful upload, move the original file (or directory) to a "completed" directory. This provides a clear audit trail of what has been uploaded and helps prevent duplicate uploads.

## Requirements

### 1. Completed Directory Structure

- Create a `completed/` directory (or configurable via `MGMT_COMPLETED_DIR`)
- Move successfully uploaded files/directories to this location
- Preserve directory structure if needed, or flatten to a single directory

### 2. File Metadata Tracking

Assign a data structure to each uploaded file to track:

- Original file/directory path
- Upload timestamp
- Compression type used
- S3 object key/name
- File size (original and compressed)
- Checksum/hash (optional, for verification)
- Upload status (success/failed)

**Suggested Data Structure:**

```python
@dataclass
class UploadRecord:
    original_path: str
    upload_timestamp: datetime
    compression_type: str
    s3_object_key: str
    original_size: int
    compressed_size: int
    checksum: Optional[str] = None
    status: str = "completed"
```

### 3. Metadata Storage Options

- **Option A:** JSON file per upload (`completed/.uploads.json` or individual files)
- **Option B:** SQLite database for queryable metadata
- **Option C:** Metadata stored as S3 object tags/metadata
- **Option D:** Combination: JSON file + S3 metadata

### 4. Implementation Considerations

- Only move files after successful upload (after verifying upload succeeded)
- Handle errors gracefully - if move fails, log error but don't fail the upload
- Support for both file and directory moves
- Consider symlinks vs actual moves (symlinks preserve original location but may be fragile)
- Add configuration option to enable/disable this feature
- Add CLI command to query/list completed uploads

### 5. Integration Points

- Modify `upload()` function in `mgmt/app.py` to track uploads
- Modify `upload_target()` in `mgmt/aws.py` to return upload metadata
- Create new module `mgmt/completed.py` or extend `mgmt/files.py` for file movement logic
- Update configuration to include `MGMT_COMPLETED_DIR` setting

## Example Flow

```
1. User runs: mgmt upload myfile.mp4
2. File is compressed: myfile.mp4.tar.gz
3. Upload to S3 succeeds
4. Create UploadRecord with metadata
5. Move myfile.mp4 -> completed/myfile.mp4
6. Save metadata to completed/.uploads.json
7. Clean up compressed file
```

## Benefits

- Clear separation of uploaded vs pending files
- Prevents accidental re-uploads
- Provides audit trail and history
- Enables querying upload history
- Supports future features like retry logic, status checking

## Open Questions

- Should the completed directory be relative to current working directory or `MGMT_LOCAL_DIR`?
- How to handle duplicate filenames in completed directory? (timestamp prefix? subdirectories?)
- Should compressed files also be moved to completed, or only originals?
- Should this be opt-in (config flag) or always-on?
- How to handle directory uploads - move entire directory structure?

## Related Files

### Files to Modify

- `mgmt/app.py` - Upload command (add tracking and file movement)
- `mgmt/aws.py` - AWS S3 operations (return upload metadata)
- `mgmt/config.py` - Configuration management (add `MGMT_COMPLETED_DIR`)

### New Files to Create

- `mgmt/completed.py` - File movement and metadata tracking (or extend `mgmt/files.py`)
