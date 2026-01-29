# Search Flow Enhancement: Download/Delete Actions Design

## Overview

**Goal**: Add interactive download and delete capabilities to the search command, allowing users to perform actions on search results without switching to separate commands.

**Status**: Design Phase
**Target**: `mgmt search` command enhancement

---

## Current vs Proposed Flow

### Current Flow

```
mgmt search <keyword>
  → Display results
  → "Download?" (yes/no)
    → If yes: select file, download
  → "Check Status?" (yes/no)
    → If yes: select file, show metadata
  → Exit
```

**Limitations**: Sequential prompts, no delete option, can't repeat actions

### Proposed Flow

```
mgmt search <keyword>
  → Display results in table
  → Action Menu:
     [1] Download file
     [2] Delete file
     [3] Check status
     [4] Exit
  → Perform selected action
  → Return to menu (loop until exit)
```

**Benefits**: Flexible, repeatable actions, delete support, better UX

---

## Technical Implementation

### 1. Refactored `search()` Function Structure

```python
@app.command()
def search(keyword: str) -> None:
    # 1. Execute search (unchanged)
    local_matches, s3_matches = perform_search(keyword)

    # 2. Build and display results table
    table, options_map = build_search_results_table(s3_matches)
    console.print(table)

    # 3. Interactive menu loop
    while True:
        action = display_action_menu()
        if action == 4:  # Exit
            break
        handle_action(action, options_map)
```

### 2. New Helper Functions

#### `build_search_results_table(s3_matches: list[str]) -> tuple[Table, dict[int, str]]`

- Extracts table-building logic from main search function
- Returns Rich Table object and index-to-filename mapping
- Reusable for redisplay if needed

#### `display_action_menu() -> int`

- Shows action menu options
- Validates input (1-4)
- Returns selected action number

#### `handle_action(action: int, options: dict[int, str]) -> None`

- Routes to appropriate action handler based on selection
- Handles invalid selections gracefully

#### `handle_download_action(options: dict[int, str]) -> None`

- Prompts for file index
- Validates selection using existing `check_selection()`
- Calls `aws.download()`
- Shows success/error messages

#### `handle_delete_action(options: dict[int, str]) -> None`

- Prompts for file index
- Shows file metadata (size, storage class, last modified)
- **Requires confirmation**: "Confirm deletion of `filename`?"
- Calls `aws.delete_file()`
- Shows success/error messages

#### `handle_status_action(options: dict[int, str]) -> None`

- Prompts for file index
- Calls `aws.get_obj_head()`
- Displays formatted JSON metadata

---

## Implementation Details

### Menu Display (using Typer/Rich)

```python
def display_action_menu() -> int:
    echo("\nWhat would you like to do?")
    echo("[1] Download file")
    echo("[2] Delete file")
    echo("[3] Check status")
    echo("[4] Exit")

    while True:
        try:
            choice = typer.prompt("Select action", type=int)
            if 1 <= choice <= 4:
                return choice
            echo("Invalid selection. Please choose 1-4.", err=True)
        except ValueError:
            echo("Invalid input. Please enter a number.", err=True)
```

### Delete Action with Safety

```python
def handle_delete_action(options: dict[int, str]) -> None:
    file_idx = typer.prompt("Which file to delete? [option #]", type=int)

    if not check_selection(file_idx, list(options.keys())):
        echo("Invalid selection.", err=True)
        return

    filename = options[file_idx]

    # Show metadata for context
    try:
        metadata = aws.get_obj_head(filename)
        echo(f"\nFile: {filename}")
        echo(f"Size: {metadata.get('ContentLength', 0) / (1024**3):.2f} GB")
        echo(f"Storage: {metadata.get('StorageClass', 'STANDARD')}")
        echo(f"Modified: {metadata.get('LastModified', 'Unknown')}")
    except Exception as e:
        echo(f"Warning: Could not fetch metadata: {e}", err=True)

    # Require confirmation
    if not typer.confirm(f"\nConfirm deletion of '{filename}'?", default=False):
        echo("Deletion cancelled.")
        return

    # Perform deletion
    try:
        if aws.delete_file(filename):
            echo(f"✓ Successfully deleted {filename}", fg=typer.colors.GREEN)
        else:
            echo(f"✗ Failed to delete {filename}", err=True)
    except Exception as e:
        echo(f"Error during deletion: {e}", err=True)
```

---

## Error Handling Strategy

1. **Invalid menu selection**: Show error, re-prompt
2. **Invalid file index**: Show error, return to menu
3. **Network/AWS errors**: Catch, log, show user-friendly message, return to menu
4. **No search results**: Display message, skip menu, exit gracefully

---

## Testing Checklist

- [ ] Search with no results
- [ ] Search with only local matches (no S3 files)
- [ ] Search with S3 matches
- [ ] Download action (STANDARD storage)
- [ ] Download action (GLACIER storage)
- [ ] Delete action with confirmation
- [ ] Delete action cancelled
- [ ] Status check action
- [ ] Invalid menu selections
- [ ] Invalid file index selections
- [ ] Multiple operations in sequence
- [ ] Exit action

---

## Future Enhancements (Out of Scope)

- Batch operations (multi-select downloads/deletes)
- Range selection syntax (e.g., "1-5")
- Local file operations from search results
- Search result filtering/sorting
- Export search results to file

---

## Files to Modify

- **Primary**: `/Users/will/repos/media-mgmt-cli/mgmt/app.py`
    - Refactor `search()` function (lines 182-267)
    - Add new helper functions

---

## Backward Compatibility

**Fully backward compatible** - The search command signature remains unchanged:

```bash
mgmt search <keyword>
```

No breaking changes to CLI interface or existing commands.
