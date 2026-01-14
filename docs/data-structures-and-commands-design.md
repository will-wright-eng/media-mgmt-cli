# Data Structures and Commands Design Document

## Overview

This document defines the general data structures, command patterns, and architectural framework for the media management CLI. It provides a foundation for tracking file operations, managing metadata, and extending functionality across all commands.

## Goals

- **Standardize data structures**: Define consistent data models for files, operations, and metadata
- **Establish command patterns**: Create reusable patterns for CLI commands
- **Enable extensibility**: Design structures that support future enhancements
- **Provide audit trail**: Track all operations with comprehensive metadata
- **Support querying**: Enable efficient querying and reporting of operations

## Core Data Structures

### File Record

Represents a file or directory in the system, whether local or remote.

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

### Operation Record

Represents a single operation performed on a file (upload, download, delete, etc.).

```python
@dataclass
class OperationRecord:
    """Represents a single operation performed on a file."""
    # Identity
    operation_id: str            # Unique identifier (UUID)
    operation_type: str          # "upload", "download", "delete", "search", "status"

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
    metadata: dict[str, Any]     # Type-specific metadata (see below)

    # Context
    user: Optional[str]          # User who performed operation
    command_args: dict[str, Any]  # Original command arguments
```

### Upload Record

Extends `OperationRecord` with upload-specific metadata.

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

### Download Record

Extends `OperationRecord` with download-specific metadata.

```python
@dataclass
class DownloadRecord(OperationRecord):
    """Represents a download operation with specific metadata."""
    # Source
    s3_bucket: str                  # S3 bucket name
    s3_object_key: str              # S3 object key/name
    s3_storage_class: Optional[str] # S3 storage class

    # Destination
    local_path: str                 # Local destination path
    downloaded_size: int            # Size of downloaded file

    # Verification
    checksum_s3_etag: Optional[str] # S3 ETag
    checksum_local: Optional[str]   # Local file checksum after download

    def __post_init__(self):
        """Initialize base OperationRecord fields."""
        self.operation_type = "download"
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update({
            "s3_bucket": self.s3_bucket,
            "s3_object_key": self.s3_object_key,
            "downloaded_size": self.downloaded_size,
        })
```

### Search Record

Represents a search operation and its results.

```python
@dataclass
class SearchRecord(OperationRecord):
    """Represents a search operation and its results."""
    # Search parameters
    keyword: str                    # Search keyword
    location: str                   # "local", "s3", "global"

    # Results
    local_matches: list[str]        # List of matching local file paths
    s3_matches: list[str]           # List of matching S3 object keys
    total_matches: int              # Total number of matches

    # Actions taken
    download_selected: Optional[str] # S3 key if download was selected
    status_checked: Optional[str]    # S3 key if status was checked

    def __post_init__(self):
        """Initialize base OperationRecord fields."""
        self.operation_type = "search"
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update({
            "keyword": self.keyword,
            "location": self.location,
            "total_matches": self.total_matches,
        })
```

## Command Patterns

### Command Structure

All commands follow a consistent pattern:

```python
@app.command()
def command_name(
    # Required arguments
    arg1: str,
    # Optional arguments
    arg2: Optional[str] = None,
    # Options
    option1: bool = typer.Option(False, "--flag", help="..."),
) -> None:
    """
    Command description.

    Args:
        arg1: Description of argument
        arg2: Description of optional argument
    """
    # 1. Initialize operation record
    operation = OperationRecord(
        operation_id=generate_uuid(),
        operation_type="command_name",
        target_path=...,
        started_at=datetime.now(),
        command_args={...},
    )

    try:
        # 2. Validate inputs
        validate_inputs(...)

        # 3. Perform operation
        result = perform_operation(...)

        # 4. Update operation record
        operation.status = "success"
        operation.completed_at = datetime.now()
        operation.result_path = result

        # 5. Save operation record
        save_operation_record(operation)

        # 6. Display results
        display_results(result)

    except Exception as e:
        # Handle errors
        operation.status = "failed"
        operation.error_message = str(e)
        operation.completed_at = datetime.now()
        save_operation_record(operation)
        echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
```

### Command Categories

#### 1. File Transfer Commands

**Upload Command**

- Creates `UploadRecord`
- Tracks compression, S3 upload, file movement
- Updates `FileRecord` status

**Download Command**

- Creates `DownloadRecord`
- Tracks S3 download, local file creation
- Updates `FileRecord` status

#### 2. Query Commands

**Search Command**

- Creates `SearchRecord`
- Searches local and S3 locations
- Returns matching `FileRecord` objects

**List Command (`ls`)**

- Queries `FileRecord` objects
- Filters by location
- Displays formatted results

**Status Command**

- Queries `FileRecord` and `OperationRecord`
- Displays metadata for specific file
- Shows operation history

#### 3. Management Commands

**Delete Command**

- Creates `OperationRecord` with type "delete"
- Removes file from S3
- Updates `FileRecord` status to "deleted"
- Preserves operation record for audit

**Config Command**

- Manages configuration
- No file operations, but may create `OperationRecord` for audit

**Log Command**

- Displays operation history
- Queries `OperationRecord` objects
- Filters by date, type, status

## Metadata Storage Architecture

### Storage Options

#### Option A: JSON File Storage (Simple)

**Structure:**

```
completed/
├── .uploads.json          # All upload records
├── .downloads.json        # All download records
├── .operations.json       # All operation records
└── .files.json            # File registry
```

**Pros:**

- Simple to implement
- Human-readable
- Easy to backup/version control

**Cons:**

- Not efficient for large datasets
- No querying capabilities
- Potential file locking issues

#### Option B: SQLite Database (Recommended)

**Structure:**

```sql
-- Operations table (base for all operations)
CREATE TABLE operations (
    operation_id TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL,
    target_path TEXT NOT NULL,
    target_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    status TEXT NOT NULL,
    result_path TEXT,
    error_message TEXT,
    user TEXT,
    command_args TEXT,  -- JSON
    metadata TEXT       -- JSON
);

-- Files table (registry of all files)
CREATE TABLE files (
    name TEXT NOT NULL,
    path TEXT PRIMARY KEY,
    location TEXT NOT NULL,
    size INTEGER,
    is_directory BOOLEAN,
    mime_type TEXT,
    created_at TIMESTAMP,
    modified_at TIMESTAMP,
    accessed_at TIMESTAMP,
    checksum TEXT,
    tags TEXT,  -- JSON
    status TEXT NOT NULL,
    error_message TEXT
);

-- Indexes for common queries
CREATE INDEX idx_operations_type ON operations(operation_type);
CREATE INDEX idx_operations_status ON operations(status);
CREATE INDEX idx_operations_started_at ON operations(started_at);
CREATE INDEX idx_files_location ON files(location);
CREATE INDEX idx_files_status ON files(status);
```

**Pros:**

- Efficient querying
- ACID transactions
- Scalable
- Built-in Python support

**Cons:**

- Requires database schema management
- Slightly more complex

#### Option C: Hybrid Approach

- SQLite for operations and queries
- JSON files for human-readable backups
- Periodic sync between formats

### Metadata Manager Interface

```python
class MetadataManager:
    """Manages storage and retrieval of operation and file records."""

    def save_operation(self, operation: OperationRecord) -> None:
        """Save an operation record."""
        pass

    def get_operation(self, operation_id: str) -> Optional[OperationRecord]:
        """Retrieve an operation record by ID."""
        pass

    def list_operations(
        self,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[OperationRecord]:
        """Query operation records with filters."""
        pass

    def save_file_record(self, file_record: FileRecord) -> None:
        """Save or update a file record."""
        pass

    def get_file_record(self, path: str) -> Optional[FileRecord]:
        """Retrieve a file record by path."""
        pass

    def search_files(
        self,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[FileRecord]:
        """Search file records."""
        pass

    def get_upload_history(self, target_path: str) -> list[UploadRecord]:
        """Get upload history for a specific file."""
        pass
```

## Integration Points

### Module Structure

```
mgmt/
├── app.py              # CLI commands (uses patterns above)
├── aws.py              # AWS S3 operations (returns metadata)
├── config.py           # Configuration management
├── files.py            # File operations (compression, movement)
├── metadata.py         # MetadataManager implementation
├── models.py           # Data classes (FileRecord, OperationRecord, etc.)
└── utils.py            # Utility functions
```

### Command Integration Flow

```
User Command
    │
    ├─> app.py (command handler)
    │   ├─> Create OperationRecord
    │   ├─> Validate inputs
    │   │
    │   ├─> Call aws.py / files.py
    │   │   └─> Return operation metadata
    │   │
    │   ├─> Update OperationRecord
    │   ├─> Save via MetadataManager
    │   └─> Display results
    │
    └─> metadata.py (MetadataManager)
        └─> Store in SQLite/JSON
```

## Example Implementations

### Upload Command with Metadata

```python
@app.command()
def upload(filename: str = "all") -> None:
    """Uploads the specified file to S3 with full metadata tracking. Always uses gzip compression (tar.gz format)."""
    metadata_mgr = MetadataManager()

    # Create upload record
    upload_record = UploadRecord(
        operation_id=str(uuid.uuid4()),
        operation_type="upload",
        target_path=filename,
        target_name=Path(filename).name,
        started_at=datetime.now(),
        status="pending",
        compression_type="gzip",  # Always gzip (tar.gz)
        original_size=0,  # Will be updated
        s3_bucket=aws.bucket_name,
        s3_object_key="",  # Will be updated
        command_args={"filename": filename},
    )

    try:
        # Get file size
        target_path = Path(filename)
        upload_record.original_size = target_path.stat().st_size if target_path.is_file() else 0

        # Perform upload (always uses gzip compression)
        result = aws.upload_target(target_path)
        s3_key = extract_s3_key(result)

        # Update upload record
        upload_record.status = "success"
        upload_record.completed_at = datetime.now()
        upload_record.s3_object_key = s3_key
        upload_record.duration_seconds = (upload_record.completed_at - upload_record.started_at).total_seconds()

        # Get S3 metadata
        s3_metadata = aws.get_obj_head(s3_key)
        upload_record.s3_storage_class = s3_metadata.get("StorageClass")
        upload_record.compressed_size = s3_metadata.get("ContentLength")

        # Calculate compression ratio
        if upload_record.compressed_size and upload_record.original_size:
            upload_record.compression_ratio = upload_record.original_size / upload_record.compressed_size

        # Move to completed directory
        completed_path = move_to_completed(target_path)
        upload_record.completed_dir_path = str(completed_path)

        # Save metadata
        metadata_mgr.save_operation(upload_record)

        # Update file record
        file_record = FileRecord(
            name=target_path.name,
            path=str(completed_path),
            location="completed",
            size=upload_record.original_size,
            status="completed",
            modified_at=upload_record.completed_at,
        )
        metadata_mgr.save_file_record(file_record)

        echo(f"Successfully uploaded {filename} to {s3_key}")

    except Exception as e:
        upload_record.status = "failed"
        upload_record.error_message = str(e)
        upload_record.completed_at = datetime.now()
        metadata_mgr.save_operation(upload_record)
        raise
```

### Query Command Example

```python
@app.command()
def history(
    operation_type: Optional[str] = None,
    limit: int = 20,
    status: Optional[str] = None,
) -> None:
    """Display operation history."""
    metadata_mgr = MetadataManager()

    operations = metadata_mgr.list_operations(
        operation_type=operation_type,
        status=status,
        limit=limit,
    )

    # Display in table format
    table = Table(title="Operation History")
    table.add_column("Type")
    table.add_column("Target")
    table.add_column("Status")
    table.add_column("Started")
    table.add_column("Duration")

    for op in operations:
        duration = f"{op.duration_seconds:.2f}s" if op.duration_seconds else "N/A"
        table.add_row(
            op.operation_type,
            op.target_name,
            op.status,
            op.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            duration,
        )

    console.print(table)
```

## Benefits

1. **Consistency**: All commands follow the same pattern
2. **Audit Trail**: Complete history of all operations
3. **Queryability**: Efficient querying of operations and files
4. **Extensibility**: Easy to add new commands and operation types
5. **Debugging**: Detailed metadata helps troubleshoot issues
6. **Reporting**: Generate reports on usage, performance, errors
7. **Data Integrity**: Checksums and verification at each step

## Migration Strategy

### Phase 1: Core Structures

1. Create `models.py` with data classes
2. Implement `MetadataManager` interface
3. Choose storage backend (SQLite recommended)

### Phase 2: Command Integration

1. Update `upload` command to use new structures
2. Update `download` command
3. Update `search` command
4. Update remaining commands incrementally

### Phase 3: Query Features

1. Implement `history` command
2. Implement `status` command enhancements
3. Add filtering and reporting capabilities

### Phase 4: Advanced Features

1. Add retry logic based on operation records
2. Implement operation replay
3. Add analytics and reporting

## Future Enhancements

1. **Operation Replay**: Re-run failed operations from records
2. **Batch Operations**: Group related operations
3. **Scheduled Operations**: Queue operations for later execution
4. **Operation Dependencies**: Chain operations (upload → verify → move)
5. **Notifications**: Alert on operation completion/failure
6. **Analytics**: Usage statistics, performance metrics
7. **Export/Import**: Backup and restore operation history
8. **Multi-user Support**: Track operations by user
9. **Operation Templates**: Predefined operation configurations
10. **Webhook Integration**: Notify external systems on operations

## Open Questions

1. Should operation records be immutable once completed?
2. How long should operation records be retained?
3. Should we support operation cancellation?
4. How to handle partial operations (multi-file uploads)?
5. Should metadata be synced to S3 object tags?
6. How to handle concurrent operations on the same file?
7. Should we support operation rollback/undo?

## References

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [SQLite Python](https://docs.python.org/3/library/sqlite3.html)
- [Typer CLI Framework](https://typer.tiangolo.com/)
- [Rich Console](https://rich.readthedocs.io/)

## Approval

- [ ] Design reviewed
- [ ] Data structures validated
- [ ] Command patterns approved
- [ ] Storage architecture selected
- [ ] Implementation plan approved

---

**Document Version**: 1.0
**Last Updated**: 2024
**Author**: Design Document
**Status**: Draft
