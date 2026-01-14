# Upload Process Review

This document outlines the issues found in the upload process during code review.

## Overview

The upload process involves multiple components:

- `mgmt/app.py` - CLI command handler (`upload()` function)
- `mgmt/aws.py` - AWS S3 operations (`upload_target()`, `upload_file()`)
- `mgmt/files.py` - File compression operations (`zip_process()`, `gzip_process()`)

## Issues Found

### 1. Skip Files Logic Bug

**Location:** `mgmt/app.py:97`

**Issue:**
The code compares the full path string against the skip list, which will never match:

```python
if str(_file_or_dir) not in skip_files:
```

When `_file_or_dir` is a `Path` object, `str(_file_or_dir)` produces a full path like `/Users/will/repos/media-mgmt-cli/.DS_Store`, but `skip_files` contains just `.DS_Store`.

**Impact:**
`.DS_Store` files will not be skipped and will be uploaded.

**Fix:**
Use the filename property instead:

```python
if _file_or_dir.name not in skip_files:
```

---

### 2. Single File Compression Path Issue

**Location:** `mgmt/files.py:44-58, 69, 87`

**Issue:**
When `zip_process()` or `gzip_process()` fall back to `zip_single_file()`/`gzip_single_file()` for single files, these methods assume files are in `self.base_path`. However, the target file may be in the current working directory (as passed from `app.py`).

The problematic code:

```python
def zip_single_file(self, filename: str) -> str:
    zip_file = filename.split(".")[0] + ".zip"
    with ZipFile(zip_file, "w") as zipf:
        zipf.write(os.path.join(self.base_path, filename), arcname=filename)
    # ...
```

When `zip_process()` calls this with `str(target_path)`, `filename` is a full path, but the code treats it as a relative path in `base_path`.

**Impact:**
Single file compression will fail with `FileNotFoundError` when the file is not in `base_path`.

**Fix:**
Handle absolute paths correctly in `zip_single_file` and `gzip_single_file`, or pass relative paths only.

---

### 3. Error Handling Gap

**Location:** `mgmt/aws.py:201`

**Issue:**
The `upload_file()` method returns `False` on error, but `upload_target()` doesn't check the return value:

```python
def upload_target(self, target_path: Union[str, Path], compression: Optional[str]) -> str:
    # ... compression logic ...
    self.upload_file(file_name=file_created)  # No error checking!
    return file_created
```

**Impact:**
Upload failures are silently ignored. The compressed file is still returned and will be deleted, making it appear as if the upload succeeded.

**Fix:**
Check the return value and raise an exception or handle the error appropriately:

```python
if not self.upload_file(file_name=file_created):
    raise RuntimeError(f"Failed to upload {file_created}")
```

---

### 4. Missing Bucket Validation

**Location:** `mgmt/aws.py:65`

**Issue:**
The `upload_file()` method uses `self.bucket` without checking if it's `None`:

```python
self.s3_client.upload_fileobj(data, self.bucket, object_name)
```

If the configuration is missing or invalid, `self.bucket` could be `None`, causing a crash.

**Impact:**
Application will crash with a `TypeError` if bucket is not configured, rather than providing a clear error message.

**Fix:**
Add validation before using the bucket:

```python
if not self.bucket:
    raise ValueError("Bucket not configured. Please run 'mgmt config' to set up configuration.")
```

---

### 5. Error Recovery Issue

**Location:** `mgmt/app.py:112-115`

**Issue:**
The `finally` block always deletes compressed files, even if the upload failed:

```python
finally:
    if files_created:
        for file in files_created:
            os.remove(file)
```

**Impact:**
If an upload fails, the compressed file is immediately deleted, making it impossible to retry the upload without re-compressing. This is wasteful of CPU/time for large files.

**Fix:**
Only delete files on successful upload, or provide an option to keep failed uploads for retry.

---

## Proposed Enhancements

### 6. Move Successfully Uploaded Files to Completed Directory

**Location:** `mgmt/app.py` (upload command)

**Proposal:**
After a successful upload, move the original file (or directory) to a "completed" directory. This provides a clear audit trail of what has been uploaded and helps prevent duplicate uploads.

**Requirements:**

1. **Completed Directory Structure:**
   - Create a `completed/` directory (or configurable via `MGMT_COMPLETED_DIR`)
   - Move successfully uploaded files/directories to this location
   - Preserve directory structure if needed, or flatten to a single directory

2. **File Metadata Tracking:**
   - Assign a data structure to each uploaded file to track:
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

3. **Metadata Storage Options:**
   - **Option A:** JSON file per upload (`completed/.uploads.json` or individual files)
   - **Option B:** SQLite database for queryable metadata
   - **Option C:** Metadata stored as S3 object tags/metadata
   - **Option D:** Combination: JSON file + S3 metadata

4. **Implementation Considerations:**
   - Only move files after successful upload (after verifying upload succeeded)
   - Handle errors gracefully - if move fails, log error but don't fail the upload
   - Support for both file and directory moves
   - Consider symlinks vs actual moves (symlinks preserve original location but may be fragile)
   - Add configuration option to enable/disable this feature
   - Add CLI command to query/list completed uploads

5. **Integration Points:**
   - Modify `upload()` function in `mgmt/app.py` to track uploads
   - Modify `upload_target()` in `mgmt/aws.py` to return upload metadata
   - Create new module `mgmt/completed.py` or extend `mgmt/files.py` for file movement logic
   - Update configuration to include `MGMT_COMPLETED_DIR` setting

**Example Flow:**

```
1. User runs: mgmt upload myfile.mp4
2. File is compressed: myfile.mp4.tar.gz
3. Upload to S3 succeeds
4. Create UploadRecord with metadata
5. Move myfile.mp4 -> completed/myfile.mp4
6. Save metadata to completed/.uploads.json
7. Clean up compressed file
```

**Benefits:**

- Clear separation of uploaded vs pending files
- Prevents accidental re-uploads
- Provides audit trail and history
- Enables querying upload history
- Supports future features like retry logic, status checking

**Open Questions:**

- Should the completed directory be relative to current working directory or `MGMT_LOCAL_DIR`?
- How to handle duplicate filenames in completed directory? (timestamp prefix? subdirectories?)
- Should compressed files also be moved to completed, or only originals?
- Should this be opt-in (config flag) or always-on?
- How to handle directory uploads - move entire directory structure?

---

## Summary

| Issue | Severity | Component | Impact |
|-------|----------|-----------|--------|
| Skip files logic bug | Medium | `app.py` | Unwanted files uploaded |
| Single file compression path | High | `files.py` | Uploads fail for single files outside base_path |
| Error handling gap | High | `aws.py` | Silent failures, misleading behavior |
| Missing bucket validation | Medium | `aws.py` | Poor error messages on configuration issues |
| Error recovery issue | Medium | `app.py` | Wasted resources on failed uploads |

## Recommendations

### Bug Fixes (High Priority)

1. **Fix the skip files logic** - Use `.name` property for comparison
2. **Fix path handling** - Ensure single file compression works with absolute paths
3. **Add error checking** - Verify upload success and propagate errors
4. **Add validation** - Check configuration before operations
5. **Improve cleanup** - Only delete files on successful upload, or keep for retry

### Feature Enhancements

6. **Implement completed directory feature** - Move successfully uploaded files and track metadata
   - Create `completed/` directory structure
   - Implement `UploadRecord` data structure
   - Add file movement logic after successful uploads
   - Choose and implement metadata storage solution (JSON/SQLite/S3 tags)
   - Add configuration option for completed directory
   - Consider adding CLI command to query completed uploads

## Related Files

### Current Implementation

- `mgmt/app.py` - Lines 77-116 (upload command)
- `mgmt/aws.py` - Lines 53-69 (upload_file), 186-202 (upload_target)
- `mgmt/files.py` - Lines 44-87 (compression methods)
- `mgmt/config.py` - Configuration management

### Potential New Files for Enhancement

- `mgmt/completed.py` - File movement and metadata tracking (or extend `mgmt/files.py`)
- Configuration updates - Add `MGMT_COMPLETED_DIR` to `mgmt/config.py`
