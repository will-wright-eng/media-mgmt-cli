# Upload Process and Completed Directory Enhancement

## Overview

This document describes the complete upload process for the media management CLI, including file tracking, compression, S3 upload, verification, and movement to a completed directory. The data structures build upon the `FileRecord` object to provide comprehensive tracking throughout the entire upload lifecycle.

## Complete Upload Process

The upload process consists of the following stages:

1. **File Selection & Validation** - Identify and validate the target file/directory
2. **File Record Creation** - Create initial `FileRecord` for the source file
3. **Compression** - Create gzip/tar.gz archive of the file/directory
4. **S3 Upload** - Upload compressed file to S3
5. **Verification** - Verify upload success and retrieve S3 metadata
6. **Completed Directory Movement** - Move original file to completed directory
7. **Metadata Persistence** - Save operation and file records
8. **Cleanup** - Remove temporary compressed files

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
    location: str                # "local", "s3", or "completed"

    # File properties
    size: int                    # Size in bytes
    is_directory: bool           # True if directory, False if file
    mime_type: Optional[str]     # MIME type if known

    # Timestamps
    created_at: Optional[datetime]   # Creation time
    modified_at: Optional[datetime]   # Last modification time
    accessed_at: Optional[datetime]    # Last access time

    # Metadata
    checksum: Optional[str]      # Hash/checksum (MD5, SHA256, etc.)
    tags: dict[str, str]         # Key-value tags/metadata

    # Status
    status: str                  # "pending", "uploading", "completed", "failed", "deleted"
    error_message: Optional[str] # Error details if status is "failed"
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
    target_name: str             # File/directory name

    # Operation details
    started_at: datetime         # When operation started
    completed_at: Optional[datetime]  # When operation completed
    duration_seconds: Optional[float] # Operation duration

    # Results
    status: str                  # "success", "failed", "partial", "cancelled"
    result_path: Optional[str]   # Resulting path (e.g., S3 key, completed path)
    error_message: Optional[str] # Error details if failed

    # Operation-specific metadata
    metadata: dict[str, Any]     # Type-specific metadata

    # Context
    user: Optional[str]          # User who performed operation
    command_args: dict[str, Any]  # Original command arguments
```

### UploadRecord (Upload-Specific)

The `UploadRecord` extends `OperationRecord` and references `FileRecord` objects:

```python
@dataclass
class UploadRecord(OperationRecord):
    """Represents an upload operation with specific metadata."""
    # Compression
    compression_type: Optional[str]  # Always "gzip" (tar.gz format)
    original_size: int              # Size before compression
    compressed_size: Optional[int]   # Size after compression
    compression_ratio: Optional[float]  # Compression ratio

    # Destination
    s3_bucket: str                  # S3 bucket name
    s3_object_key: str              # S3 object key/name
    s3_storage_class: Optional[str] # S3 storage class

    # Verification
    checksum_original: Optional[str]    # Original file checksum
    checksum_compressed: Optional[str]   # Compressed file checksum
    checksum_s3_etag: Optional[str]     # S3 ETag for verification

    # Lifecycle
    completed_dir_path: Optional[str]   # Path in completed directory
    compressed_file_path: Optional[str] # Path to compressed file (if kept)

    # References to FileRecord objects
    source_file_record: Optional[FileRecord]      # Original file record
    compressed_file_record: Optional[FileRecord] # Compressed file record
    s3_file_record: Optional[FileRecord]          # S3 object record
    completed_file_record: Optional[FileRecord]  # Completed directory record

    def __post_init__(self):
        """Initialize base OperationRecord fields."""
        self.operation_type = "upload"
        if self.metadata is None:
            self.metadata = {}
        # Store upload-specific fields in metadata for serialization
        self.metadata.update({
            "compression_type": self.compression_type,
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "s3_bucket": self.s3_bucket,
            "s3_object_key": self.s3_object_key,
        })
```

## Detailed Upload Flow

### Stage 1: File Selection & Validation

**Input:** User provides filename or "all" to upload all files in directory

**Process:**

- Validate file/directory exists
- Check if file is already in completed directory (prevent duplicates)
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
    created_at=datetime.fromtimestamp(target_path.stat().st_ctime),
    modified_at=datetime.fromtimestamp(target_path.stat().st_mtime),
)
```

### Stage 2: Upload Record Initialization

**Process:**

- Create `UploadRecord` with initial state
- Link to source `FileRecord`
- Generate unique operation ID

**UploadRecord Created:**

```python
upload_record = UploadRecord(
    operation_id=str(uuid.uuid4()),
    operation_type="upload",
    target_path=str(target_path),
    target_name=target_path.name,
    started_at=datetime.now(),
    status="pending",
    compression_type="gzip",
    original_size=source_file_record.size,
    s3_bucket=aws.bucket,
    source_file_record=source_file_record,
    command_args={"filename": filename},
)
```

### Stage 3: Compression

**Process:**

- Create tar.gz archive using `FileManager.gzip_process()`
- Calculate compressed file size
- Generate checksum for compressed file

**FileRecord Created:**

```python
compressed_file_record = FileRecord(
    name=f"{target_path.name}.tar.gz",
    path=compressed_file_path,
    location="local",
    size=compressed_size,
    is_directory=False,
    mime_type="application/gzip",
    status="pending",
    checksum=calculate_checksum(compressed_file_path),
)

upload_record.compressed_file_record = compressed_file_record
upload_record.compressed_size = compressed_size
upload_record.compressed_file_path = compressed_file_path
```

### Stage 4: S3 Upload

**Process:**

- Upload compressed file to S3 using `AwsStorageMgmt.upload_file()`
- Construct S3 object key with prefix if configured
- Verify upload success

**FileRecord Created:**

```python
s3_file_record = FileRecord(
    name=s3_object_key.split("/")[-1],
    path=s3_object_key,
    location="s3",
    size=upload_record.compressed_size,
    is_directory=False,
    status="completed",
    modified_at=datetime.now(),
    tags={
        "original_path": upload_record.target_path,
        "original_size": str(upload_record.original_size),
        "compression_type": "gzip",
    },
)

upload_record.s3_file_record = s3_file_record
upload_record.s3_object_key = s3_object_key
```

### Stage 5: Verification

**Process:**

- Retrieve S3 object metadata using `AwsStorageMgmt.get_obj_head()`
- Verify file size matches
- Extract S3 ETag for checksum verification
- Get storage class information

**UploadRecord Updated:**

```python
s3_metadata = aws.get_obj_head(s3_object_key)
upload_record.s3_storage_class = s3_metadata.get("StorageClass")
upload_record.checksum_s3_etag = s3_metadata.get("ETag", "").strip('"')
upload_record.compressed_size = s3_metadata.get("ContentLength")

# Calculate compression ratio
if upload_record.compressed_size and upload_record.original_size:
    upload_record.compression_ratio = (
        upload_record.original_size / upload_record.compressed_size
    )
```

### Stage 6: Completed Directory Movement

**Process:**

- Create completed directory if it doesn't exist (configurable via `MGMT_COMPLETED_DIR`)
- Move original file/directory to completed location
- Preserve directory structure or flatten based on configuration
- Handle duplicate filenames (timestamp prefix or subdirectories)

**FileRecord Created:**

```python
completed_path = move_to_completed(target_path)
completed_file_record = FileRecord(
    name=target_path.name,
    path=str(completed_path),
    location="completed",
    size=upload_record.original_size,
    is_directory=target_path.is_dir(),
    status="completed",
    modified_at=datetime.now(),
    tags={
        "s3_bucket": upload_record.s3_bucket,
        "s3_object_key": upload_record.s3_object_key,
        "upload_operation_id": upload_record.operation_id,
        "upload_timestamp": upload_record.completed_at.isoformat(),
    },
)

upload_record.completed_file_record = completed_file_record
upload_record.completed_dir_path = str(completed_path)

# Update source file record status
source_file_record.status = "completed"
source_file_record.location = "completed"
source_file_record.path = str(completed_path)
```

### Stage 7: Metadata Persistence

**Process:**

- Save `UploadRecord` to metadata store (SQLite/JSON)
- Save all `FileRecord` objects (source, compressed, S3, completed)
- Link records for queryability

**Storage:**

- Operations stored in operations table/database
- File records stored in files registry
- Relationships maintained via operation_id and file paths

### Stage 8: Cleanup

**Process:**

- Remove temporary compressed file (`.tar.gz`)
- Update compressed file record status to "deleted"
- Log cleanup actions

**FileRecord Updated:**

```python
compressed_file_record.status = "deleted"
```

## Complete Example Flow

```
User Command: mgmt upload myfile.mp4

1. File Selection & Validation
   └─> Create FileRecord: name="myfile.mp4", location="local", status="pending"

2. Upload Record Initialization
   └─> Create UploadRecord: operation_id="uuid-123", status="pending"
   └─> Link: upload_record.source_file_record = source_file_record

3. Compression
   └─> Create: myfile.mp4.tar.gz
   └─> Create FileRecord: name="myfile.mp4.tar.gz", location="local"
   └─> Update: upload_record.compressed_file_record, compressed_size=500MB

4. S3 Upload
   └─> Upload to: s3://bucket/prefix/myfile.mp4.tar.gz
   └─> Create FileRecord: name="myfile.mp4.tar.gz", location="s3", status="completed"
   └─> Update: upload_record.s3_file_record, s3_object_key

5. Verification
   └─> Get S3 metadata: StorageClass="STANDARD", ETag="abc123"
   └─> Update: upload_record.s3_storage_class, checksum_s3_etag
   └─> Calculate: compression_ratio = 2.0 (1GB original / 500MB compressed)

6. Completed Directory Movement
   └─> Move: myfile.mp4 -> completed/myfile.mp4
   └─> Create FileRecord: name="myfile.mp4", location="completed", status="completed"
   └─> Update: upload_record.completed_file_record, completed_dir_path
   └─> Update: source_file_record.status="completed", location="completed"

7. Metadata Persistence
   └─> Save UploadRecord to operations database
   └─> Save all FileRecord objects to files registry

8. Cleanup
   └─> Delete: myfile.mp4.tar.gz
   └─> Update: compressed_file_record.status="deleted"

Result:
- Original file moved to completed/
- UploadRecord tracks entire operation
- Four FileRecord objects track file at each stage
- All metadata persisted for querying
```

## Data Structure Relationships

```
UploadRecord (OperationRecord)
├── source_file_record: FileRecord (original file, location="local")
├── compressed_file_record: FileRecord (compressed file, location="local")
├── s3_file_record: FileRecord (S3 object, location="s3")
└── completed_file_record: FileRecord (completed file, location="completed")

All FileRecord objects linked via:
- upload_record.operation_id stored in FileRecord.tags
- FileRecord.path references
- FileRecord.status transitions: pending → uploading → completed
```

## Completed Directory Structure

### Directory Layout

```
MGMT_LOCAL_DIR/
├── myfile.mp4              # Original (before upload)
├── completed/              # Completed directory
│   ├── myfile.mp4          # Moved after successful upload
│   ├── another_file.mp4
│   └── .metadata/          # Optional: metadata storage
│       ├── operations.db   # SQLite database
│       └── files.json      # File registry (if using JSON)
```

### Configuration

- `MGMT_COMPLETED_DIR`: Path to completed directory (default: `{MGMT_LOCAL_DIR}/completed`)
- `MGMT_PRESERVE_STRUCTURE`: Preserve directory structure in completed (default: false)
- `MGMT_DUPLICATE_HANDLING`: How to handle duplicates - "timestamp", "subdirectory", "error" (default: "timestamp")

## Benefits

- **Complete Audit Trail**: Every file tracked through all stages via FileRecord objects
- **Queryability**: Can query by file, operation, location, status, timestamp
- **Data Integrity**: Checksums at each stage for verification
- **Relationship Tracking**: Clear links between source, compressed, S3, and completed files
- **Prevents Duplicates**: Check completed directory before upload
- **Operation History**: Full history of all upload operations
- **Error Recovery**: Failed operations can be retried using operation records

## Implementation Considerations

- Only move files after successful S3 upload verification
- Handle errors gracefully - if move fails, log error but don't fail the upload
- Support for both file and directory moves
- Use actual moves (not symlinks) for reliability
- Add configuration option to enable/disable completed directory feature
- Add CLI command to query/list completed uploads: `mgmt history`
- Support batch operations (upload "all") with individual tracking per file

## Integration Points

### Files to Modify

- `mgmt/app.py` - Upload command (create records, track process, save metadata)
- `mgmt/aws.py` - AWS S3 operations (return upload metadata, S3 object info)
- `mgmt/files.py` - File operations (compression, movement to completed)
- `mgmt/config.py` - Configuration management (add `MGMT_COMPLETED_DIR`)

### New Files to Create

- `mgmt/models.py` - Data classes (FileRecord, OperationRecord, UploadRecord)
- `mgmt/metadata.py` - MetadataManager implementation (SQLite/JSON storage)
- `mgmt/completed.py` - File movement and completed directory management (or extend `mgmt/files.py`)

## Related Documentation

- See `docs/data-structures-and-commands-design.md` for complete data structure definitions
- See `docs/improvement-suggestions.md` for additional enhancement ideas
