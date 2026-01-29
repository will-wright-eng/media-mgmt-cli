#!/bin/bash

# Test script for upload/download functionality
# This script:
# 1. Creates a test-file.txt
# 2. Deletes the remote file if it exists (clean slate)
# 3. Uploads this test file
# 4. Downloads the test file
# 5. Uses tar to unzip the downloaded file
# 6. Confirms that the file is the same

set -euo pipefail
IFS=$'\n\t'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test file name
TEST_FILE="test-file.txt"
S3_OBJECT_NAME="${TEST_FILE}.tar.gz"
TEST_FILE_PREFIX="mediaobj"
TEST_CONTENT="This is a test file for upload/download verification.
Created at $(date).
Random content: $RANDOM"

log_header() {
    echo -e "${GREEN}=== Upload/Download Test Script ===${NC}\n"
}

log_step() {
    local message="$1"
    echo -e "${YELLOW}${message}${NC}"
}

log_ok() {
    local message="$1"
    echo -e "${GREEN}✓ ${message}${NC}\n"
}

die() {
    local message="$1"
    echo -e "${RED}Error: ${message}${NC}" >&2
    exit 1
}

cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    local test_file="${TEST_FILE:-}"
    local s3_object_name="${S3_OBJECT_NAME:-}"
    local extract_dir="${EXTRACT_DIR:-}"

    [ -n "$test_file" ] && [ -f "$test_file" ] && rm -f "$test_file"
    [ -n "$s3_object_name" ] && [ -f "$s3_object_name" ] && rm -f "$s3_object_name"
    [ -n "$extract_dir" ] && [ -d "$extract_dir" ] && rm -rf "$extract_dir"
}

# Set trap to cleanup on exit
trap cleanup EXIT

create_test_file() {
    log_step "Step 1: Creating ${TEST_FILE}..."
    echo "$TEST_CONTENT" > "$TEST_FILE"
    [ -f "$TEST_FILE" ] || die "Failed to create $TEST_FILE"
    log_ok "Created $TEST_FILE"
}

delete_remote_file_if_exists() {
    log_step "Step 2: Deleting remote file if it exists (clean slate)..."
    local remote_path="${TEST_FILE_PREFIX}/${S3_OBJECT_NAME}"

    # Attempt to delete; if file doesn't exist, that's fine
    if uv run mgmt delete "$remote_path" 2>/dev/null; then
        log_ok "Deleted existing remote file: $remote_path"
    else
        echo -e "${GREEN}✓ No existing remote file to delete${NC}\n"
    fi
}

upload_test_file() {
    log_step "Step 3: Uploading $TEST_FILE..."
    uv run mgmt upload "$TEST_FILE" || die "Failed to upload $TEST_FILE"
    log_ok "Uploaded $TEST_FILE"
}

download_tarball() {
    log_step "Step 4: Downloading ${S3_OBJECT_NAME} from S3..."
    uv run mgmt download "${TEST_FILE_PREFIX}/${S3_OBJECT_NAME}" || die "Failed to download $S3_OBJECT_NAME"
    [ -f "$S3_OBJECT_NAME" ] || die "Downloaded file $S3_OBJECT_NAME not found"
    log_ok "Downloaded $S3_OBJECT_NAME"
}

extract_tarball() {
    log_step "Step 5: Extracting $S3_OBJECT_NAME..."
    EXTRACT_DIR="${S3_OBJECT_NAME}.extracted"
    mkdir -p "$EXTRACT_DIR"
    tar -xzf "$S3_OBJECT_NAME" -C "$EXTRACT_DIR" || die "Failed to extract $S3_OBJECT_NAME"
    log_ok "Extracted $S3_OBJECT_NAME"
}

find_original_file() {
    if [ -f "completed/$TEST_FILE" ]; then
        echo "completed/$TEST_FILE"
        return 0
    fi

    # If file wasn't moved (shouldn't happen, but just in case)
    if [ -f "$TEST_FILE" ]; then
        echo "$TEST_FILE"
        return 0
    fi

    echo -e "${RED}Error: Cannot find original file for comparison${NC}" >&2
    echo -e "${YELLOW}Note: Original file should be in completed/ directory after upload${NC}" >&2
    return 1
}

compare_files() {
    log_step "Step 6: Comparing files..."

    # The extracted file should be in the extract directory
    # Based on the gzip_process function, it uses arcname=target_path.name
    # So the extracted file should be at: EXTRACT_DIR/TEST_FILE
    local extracted_file="$EXTRACT_DIR/$TEST_FILE"
    local original_file
    original_file="$(find_original_file)" || exit 1

    if [ ! -f "$extracted_file" ]; then
        echo -e "${RED}Error: Extracted file not found at $extracted_file${NC}" >&2
        echo -e "${YELLOW}Contents of extract directory:${NC}" >&2
        ls -la "$EXTRACT_DIR" >&2
        exit 1
    fi

    if diff -q "$original_file" "$extracted_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Files are identical!${NC}"
        echo -e "${GREEN}Original: $original_file${NC}"
        echo -e "${GREEN}Extracted: $extracted_file${NC}"
        return 0
    fi

    echo -e "${RED}✗ Files are different!${NC}" >&2
    echo -e "${YELLOW}Differences:${NC}" >&2
    diff "$original_file" "$extracted_file" || true
    exit 1
}

main() {
    log_header
    create_test_file
    delete_remote_file_if_exists
    upload_test_file
    download_tarball
    extract_tarball
    compare_files
    echo -e "\n${GREEN}=== All tests passed! ===${NC}"
}

main "$@"
