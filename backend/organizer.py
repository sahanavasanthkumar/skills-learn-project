"""Organization engine with Preview/Dry-Run, Atomic Execution, and Full Rollback capabilities."""

import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.database import (
    get_batch_operations,
    mark_batch_rolled_back,
    record_file_operations_batch,
    save_batch,
)
from backend.logger import get_logger
from backend.scanner import DirectoryScanner
from backend.utils import format_size, get_unique_destination_path, validate_directory


class FileOrganizer:
    """Core organization controller."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.logger = get_logger()

    def preview(
        self,
        strategy: str = "category",
        recursive: bool = False,
        detect_duplicates: bool = True,
        quarantine_duplicates: bool = True,
        use_custom_rules: bool = True,
        clean_empty_folders: bool = False,
    ) -> Dict[str, Any]:
        """Generates dry-run simulation of what moves will occur without touching the filesystem."""
        scanner = DirectoryScanner(self.root_dir)
        scan_data = scanner.scan(
            recursive=recursive,
            detect_duplicates=detect_duplicates,
            strategy=strategy,
            quarantine_duplicates=quarantine_duplicates,
            use_custom_rules=use_custom_rules,
        )

        planned_moves = []
        for item in scan_data["files"]:
            target_subfolder = item["target_subfolder"]
            target_dir = self.root_dir / target_subfolder
            planned_destination = target_dir / item["name"]

            # Calculate if moving is actually needed (case-insensitive resolve on Windows)
            item_path_resolved = Path(item["path"]).resolve()
            target_dir_resolved = target_dir.resolve()
            is_already_in_place = item_path_resolved.parent == target_dir_resolved

            planned_moves.append({
                "original_path": item["path"],
                "file_name": item["name"],
                "category": item["category"],
                "size_bytes": item["size_bytes"],
                "size_formatted": item["size_formatted"],
                "target_subfolder": target_subfolder,
                "target_destination": str(planned_destination),
                "is_duplicate": item.get("is_duplicate", False),
                "is_already_in_place": is_already_in_place,
                "icon": item["icon"],
                "color": item["color"],
                "bg_color": item["bg_color"],
            })

        return {
            "root_dir": str(self.root_dir),
            "strategy": strategy,
            "total_files": scan_data["total_files"],
            "total_size_formatted": scan_data["total_size_formatted"],
            "duplicates_count": scan_data["duplicates_count"],
            "planned_moves": planned_moves,
            "categories": scan_data["categories"],
            "duplicate_groups": scan_data["duplicate_groups"],
        }

    def execute(
        self,
        strategy: str = "category",
        recursive: bool = False,
        detect_duplicates: bool = True,
        quarantine_duplicates: bool = True,
        use_custom_rules: bool = True,
        selected_file_paths: Optional[List[str]] = None,
        clean_empty_folders: bool = False,
    ) -> Dict[str, Any]:
        """Executes actual file move operations, records batch for rollback, and cleans empty dirs."""
        preview_data = self.preview(
            strategy=strategy,
            recursive=recursive,
            detect_duplicates=detect_duplicates,
            quarantine_duplicates=quarantine_duplicates,
            use_custom_rules=use_custom_rules,
        )

        batch_id = str(uuid.uuid4())[:8] + "_" + str(int(time.time()))
        moved_count = 0
        skipped_count = 0
        error_count = 0
        operations_to_record: List[Dict[str, Any]] = []
        moved_details: List[Dict[str, Any]] = []
        
        # Normalize selected file paths for cross-platform case-insensitive comparison
        selected_set = (
            {str(Path(p).resolve()).lower() for p in selected_file_paths}
            if selected_file_paths else None
        )

        self.logger.info(f"Starting Batch {batch_id} on {self.root_dir} with strategy '{strategy}'")

        for item in preview_data["planned_moves"]:
            orig_path = Path(item["original_path"])
            orig_resolved = orig_path.resolve()

            # If user selected specific files to move
            if selected_set is not None and str(orig_resolved).lower() not in selected_set:
                skipped_count += 1
                continue

            target_dir = self.root_dir / item["target_subfolder"]
            target_resolved = target_dir.resolve()

            # Skip if already in the target subfolder
            if orig_resolved.parent == target_resolved:
                skipped_count += 1
                continue

            try:
                # Ensure target subfolder exists
                target_dir.mkdir(parents=True, exist_ok=True)

                # Determine unique destination path to prevent accidental overwrites
                dest_path = get_unique_destination_path(target_dir, orig_path.name, source_path=orig_path)
                
                # If destination is identical to source, skip
                if orig_resolved == dest_path.resolve():
                    skipped_count += 1
                    continue

                # Move the file safely
                shutil.move(str(orig_path), str(dest_path))

                moved_count += 1
                op_record = {
                    "batch_id": batch_id,
                    "original_path": str(orig_path),
                    "new_path": str(dest_path),
                    "category": item["category"],
                    "size_bytes": item["size_bytes"],
                    "file_hash": "",
                }
                operations_to_record.append(op_record)
                moved_details.append({
                    "name": orig_path.name,
                    "from": str(orig_path.parent),
                    "to": item["target_subfolder"],
                    "final_path": str(dest_path),
                    "category": item["category"],
                    "size_formatted": item["size_formatted"]
                })

            except Exception as e:
                error_count += 1
                self.logger.error(f"Failed to move {orig_path} -> {target_dir}: {e}")

        # Clean empty folders if option enabled
        cleaned_folders_count = 0
        if clean_empty_folders:
            cleaned_folders_count = self._remove_empty_folders(self.root_dir)

        # Bulk save operations to SQLite DB
        record_file_operations_batch(operations_to_record)

        summary = {
            "batch_id": batch_id,
            "root_dir": str(self.root_dir),
            "strategy": strategy,
            "total_files": preview_data["total_files"],
            "moved_files": moved_count,
            "skipped_files": skipped_count,
            "errors": error_count,
            "cleaned_folders": cleaned_folders_count,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        save_batch(
            batch_id=batch_id,
            root_dir=str(self.root_dir),
            strategy=strategy,
            total_files=preview_data["total_files"],
            moved_files=moved_count,
            summary=summary,
        )

        self.logger.info(
            f"Completed Batch {batch_id}: moved={moved_count}, skipped={skipped_count}, errors={error_count}"
        )

        return {
            "success": True,
            "batch_id": batch_id,
            "summary": summary,
            "moved_details": moved_details,
        }

    def _remove_empty_folders(self, folder: Path) -> int:
        """Recursively removes empty directories within folder, skipping reserved ones."""
        removed_count = 0
        for root, dirs, files in os.walk(folder, topdown=False):
            curr = Path(root)
            if curr == folder:
                continue
            try:
                # Check if dir is empty
                if not any(curr.iterdir()):
                    curr.rmdir()
                    removed_count += 1
            except Exception:
                pass
        return removed_count


def rollback_batch(batch_id: str) -> Dict[str, Any]:
    """Rolls back all moved files in a batch to their original locations."""
    logger = get_logger()
    operations = get_batch_operations(batch_id)

    if not operations:
        return {"success": False, "error": f"No operations found for Batch ID: {batch_id}"}

    restored_count = 0
    error_count = 0
    errors = []

    logger.info(f"Initiating Rollback for Batch {batch_id} ({len(operations)} operations)")

    for op in reversed(operations):
        if op.get("status") == "rolled_back":
            continue

        curr_path = Path(op["new_path"])
        orig_path = Path(op["original_path"])

        if not curr_path.exists():
            error_count += 1
            errors.append(f"File not found at {curr_path}")
            continue

        try:
            # Ensure original directory exists
            orig_path.parent.mkdir(parents=True, exist_ok=True)
            # Revert destination path
            dest = get_unique_destination_path(orig_path.parent, orig_path.name)
            shutil.move(str(curr_path), str(dest))
            restored_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"Failed to restore {curr_path} to {orig_path}: {e}")
            logger.error(f"Rollback error on {curr_path}: {e}")

    mark_batch_rolled_back(batch_id)
    logger.info(f"Batch {batch_id} Rollback complete: Restored={restored_count}, Errors={error_count}")

    return {
        "success": True,
        "batch_id": batch_id,
        "restored_files": restored_count,
        "error_count": error_count,
        "errors": errors,
    }
