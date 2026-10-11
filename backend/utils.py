"""Utility helper functions for file and path operations."""

import os
from pathlib import Path
from typing import Optional, Tuple


def sanitize_path_input(path_str: str) -> str:
    """Cleans user input string by stripping whitespace and surrounding quotes."""
    cleaned = path_str.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def validate_directory(path_input: str | Path) -> Tuple[bool, str, Optional[Path]]:
    """Validates that a given path points to an accessible directory on Windows.

    Args:
        path_input: Folder path entered by the user.

    Returns:
        Tuple of (is_valid, error_message, resolved_path).
    """
    if isinstance(path_input, str):
        cleaned = sanitize_path_input(path_input)
        if not cleaned:
            return False, "Folder path cannot be empty.", None
        try:
            expanded = os.path.expandvars(os.path.expanduser(cleaned))
            path = Path(expanded)
        except Exception:
            path = Path(cleaned)
    else:
        path = path_input

    try:
        resolved_path = path.resolve()
    except Exception as e:
        return False, f"Invalid path syntax: {e}", None

    if not resolved_path.exists():
        return False, f"Directory does not exist: {resolved_path}", None

    if not resolved_path.is_dir():
        return False, f"Path is a file, not a directory: {resolved_path}", None

    # Verify read access
    try:
        _ = list(os.scandir(resolved_path))
    except PermissionError:
        return False, f"Permission denied: cannot read directory {resolved_path}", None
    except OSError as e:
        return False, f"OS error accessing directory: {e}", None

    # Verify write access via a temporary probe (safe and reliable on Windows NTFS)
    test_probe = resolved_path / f".__perm_probe_{os.getpid()}__"
    try:
        test_probe.touch()
        test_probe.unlink(missing_ok=True)
    except (PermissionError, OSError):
        return False, f"Permission denied: no write access to {resolved_path}", None

    return True, "", resolved_path


def get_unique_destination_path(target_dir: Path, filename: str, source_path: Optional[Path] = None) -> Path:
    """Generates a non-conflicting destination path in target_dir.

    If target_dir / filename already exists, appends _1, _2, etc. before the extension:
    e.g., report.pdf -> report_1.pdf -> report_2.pdf

    Args:
        target_dir: The destination directory.
        filename: The original filename.
        source_path: Optional original file path being moved.

    Returns:
        A Path object guaranteed not to collide with an existing file at check time.
    """
    dest_path = target_dir / filename
    if not dest_path.exists():
        return dest_path

    # If source_path is already dest_path, return it
    if source_path is not None:
        try:
            if source_path.resolve() == dest_path.resolve():
                return dest_path
        except Exception:
            pass

    original_path = Path(filename)
    stem = original_path.stem
    suffix = original_path.suffix

    counter = 1
    while True:
        candidate_name = f"{stem}_{counter}{suffix}"
        candidate_path = target_dir / candidate_name
        if not candidate_path.exists():
            return candidate_path
        if source_path is not None:
            try:
                if source_path.resolve() == candidate_path.resolve():
                    return candidate_path
            except Exception:
                pass
        counter += 1


def format_size(size_bytes: int) -> str:
    """Formats bytes into human-readable string (B, KB, MB, GB, TB)."""
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_idx = 0
    while size >= 1024.0 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(size)} {units[unit_idx]}"
    return f"{size:.2f} {units[unit_idx]}"
