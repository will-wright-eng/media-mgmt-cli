# Upload Process

## Overview

This document describes the upload process for the media management CLI, including compression, S3 upload, and cleanup. The data structures provide a framework for tracking files through the upload lifecycle.

## Upload Process

The upload process consists of the following stages:

1. **File Selection & Validation** - Identify and validate the target file/directory
2. **Compression** - Create tar.gz archive of the file/directory
3. **S3 Upload** - Upload compressed file to S3
4. **Cleanup** - Remove temporary compressed files

## Data Structures

The upload process uses a hierarchical data structure that builds upon the `FileRecord` object:

### FileRecord (Base Structure)

The `FileRecord` represents a file or directory at any stage of its lifecycle:

```python
@dataclass
class FileRecord:
    """Represents a file or directory in the system."""
    # Identity
    name: str                    # File/directory name
    path: str                    # Full path (local or S3 key)
    location: str                # "local" or "s3"

    # File properties
    size: int                    # Size in bytes
    is_directory: bool           # True if directory, False if file

    # Status
    status: str                  # "pending", "completed", "failed", "deleted"
```

### OperationRecord (Base Operation)

The `OperationRecord` tracks any operation performed on a file:

```python
@dataclass
class OperationRecord:
    """Represents a single operation performed on a file."""
    # Identity
    operation_id: str            # Unique identifier (UUID)
    operation_type: str          # "upload", "download", "delete", etc.

    # Target
    target_path: str             # Original file/directory path

    # Operation details
    started_at: datetime         # When operation started
    status: str                  # "pending", "success", "failed"

    # Results
    result_path: Optional[str]    # Resulting path (e.g., S3 key)
    error_message: Optional[str] # Error details if failed
```

### UploadRecord (Upload-Specific)

The `UploadRecord` extends `OperationRecord` and references `FileRecord` objects:

```python
@dataclass
class UploadRecord(OperationRecord):
    """Represents an upload operation with specific metadata."""
    # Compression
    compression_type: str        # Always "gzip" (tar.gz format)
    compressed_file_path: str     # Path to compressed file

    # Destination
    s3_bucket: str               # S3 bucket name
    s3_object_key: str           # S3 object key/name

    # References to FileRecord objects
    source_file_record: Optional[FileRecord]      # Original file record
    compressed_file_record: Optional[FileRecord] # Compressed file record
    s3_file_record: Optional[FileRecord]         # S3 object record

    def __post_init__(self):
        """Initialize base OperationRecord fields."""
        self.operation_type = "upload"
```

## Detailed Upload Flow

### Stage 1: File Selection & Validation

**Input:** User provides filename or "all" to upload all files in directory

**Process:**

- Validate file/directory exists in current working directory
- Skip system files (e.g., `.DS_Store`)
- Determine if target is file or directory

**FileRecord Created:**

```python
source_file_record = FileRecord(
    name=target_path.name,
    path=str(target_path),
    location="local",
    size=target_path.stat().st_size if target_path.is_file() else 0,
    is_directory=target_path.is_dir(),
    status="pending",
)
```

### Stage 2: Compression

**Process:**

- Create tar.gz archive using `FileManager.gzip_process()`
- Archive is created in the same directory as the source file
- Archive name format: `{original_name}.tar.gz`

**FileRecord Created:**

```python
compressed_file_path = file_mgmt.gzip_process(target_path)
compressed_file_record = FileRecord(
    name=f"{target_path.name}.tar.gz",
    path=compressed_file_path,
    location="local",
    size=Path(compressed_file_path).stat().st_size,
    is_directory=False,
    status="pending",
)

upload_record.compressed_file_record = compressed_file_record
upload_record.compressed_file_path = compressed_file_path
```

### Stage 3: S3 Upload

**Process:**

- Upload compressed file to S3 using `AwsStorageMgmt.upload_file()`
- Construct S3 object key with prefix if configured (`MGMT_OBJECT_PREFIX`)
- Object key format: `{prefix}/{filename}.tar.gz` (if prefix exists) or `{filename}.tar.gz`

**FileRecord Created:**

```python
s3_object_key = object_prefix + "/" + filename if object_prefix else filename
aws.upload_file(compressed_file_path)

s3_file_record = FileRecord(
    name=s3_object_key.split("/")[-1],
    path=s3_object_key,
    location="s3",
    size=compressed_file_record.size,
    is_directory=False,
    status="completed",
)

upload_record.s3_file_record = s3_file_record
upload_record.s3_object_key = s3_object_key
upload_record.s3_bucket = aws.bucket
```

### Stage 4: Cleanup

**Process:**

- Remove temporary compressed file (`.tar.gz`) after successful upload
- Only delete files that were successfully uploaded
- Keep compressed files if upload fails (for potential retry)

**FileRecord Updated:**

```python
if upload_successful:
    os.remove(compressed_file_path)
    compressed_file_record.status = "deleted"
```

## Complete Example Flow

```
User Command: mgmt upload myfile.mp4

1. File Selection & Validation
   └─> Create FileRecord: name="myfile.mp4", location="local", status="pending"
   └─> Create UploadRecord: operation_id="uuid-123", status="pending"

2. Compression
   └─> Create: myfile.mp4.tar.gz
   └─> Create FileRecord: name="myfile.mp4.tar.gz", location="local", status="pending"
   └─> Update: upload_record.compressed_file_record, compressed_file_path

3. S3 Upload
   └─> Upload to: s3://bucket/prefix/myfile.mp4.tar.gz
   └─> Create FileRecord: name="myfile.mp4.tar.gz", location="s3", status="completed"
   └─> Update: upload_record.s3_file_record, s3_object_key, status="success"

4. Cleanup
   └─> Delete: myfile.mp4.tar.gz
   └─> Update: compressed_file_record.status="deleted"

Result:
- Original file: myfile.mp4 (unchanged, still in current directory)
- Compressed file: deleted after successful upload
- S3 object: myfile.mp4.tar.gz available in S3 bucket
- UploadRecord tracks the operation
- Three FileRecord objects track file at each stage
```

## Data Structure Relationships

```
UploadRecord (OperationRecord)
├── source_file_record: FileRecord (original file, location="local")
├── compressed_file_record: FileRecord (compressed file, location="local")
└── s3_file_record: FileRecord (S3 object, location="s3")

All FileRecord objects linked via:
- upload_record.operation_id
- FileRecord.path references
- FileRecord.status transitions: pending → completed/deleted
```

## Current Implementation

The current implementation follows this simplified flow:

- **File Selection**: Validates file/directory exists in current working directory
- **Compression**: Uses `FileManager.gzip_process()` to create tar.gz archive
- **S3 Upload**: Uses `AwsStorageMgmt.upload_file()` to upload compressed file
- **Cleanup**: Deletes compressed file only after successful upload

### Key Methods

- `AwsStorageMgmt.upload_target()` - Main upload method that handles compression and upload
- `FileManager.gzip_process()` - Creates tar.gz archive
- `AwsStorageMgmt.upload_file()` - Uploads file to S3

### Configuration

The upload process uses the following configuration variables (set via `mgmt config`):

- `MGMT_BUCKET`: S3 bucket name for uploads
- `MGMT_OBJECT_PREFIX`: Optional prefix added to S3 object keys
- `MGMT_LOCAL_DIR`: Base directory for file operations (used by FileManager)

### Error Handling

- **Upload failures**: Compressed file is kept for potential retry
- **Deletion failures**: Warning logged, operation continues
- **Missing configuration**: Error raised with instructions to run `mgmt config`
- **Invalid file/directory**: Error message displayed, operation aborted

## Future Enhancements

Potential improvements (not currently implemented):

- Track upload history and metadata using the data structures defined above
- Move original files to a completed directory after successful upload
- Verify uploads with checksums
- Calculate and display compression statistics
- Support for upload retry mechanisms
- Query upload history

See `docs/data-structures-and-commands-design.md` for design ideas for future enhancements.

## Related Documentation

- See `docs/data-structures-and-commands-design.md` for complete data structure definitions
- See `docs/improvement-suggestions.md` for additional enhancement ideas
