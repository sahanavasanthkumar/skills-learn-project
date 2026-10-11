"""Directory scanner with fast streaming hash-based duplicate detection and metadata analysis."""

import hashlib
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import (
    CATEGORY_METADATA,
    CHUNK_SIZE,
    DEFAULT_EXCLUDED_DIRS,
    ORDERED_CATEGORIES,
    OTHER_CATEGORY_NAME,
)
from backend.logger import get_logger
from backend.rules_engine import RulesEngine
from backend.utils import format_size, validate_directory


def calculate_file_hash(file_path: Path, max_bytes: Optional[int] = None) -> str:
    """Calculates SHA-256 hash of a file efficiently using chunk streaming.
    
    If max_bytes is provided, only hashes up to that limit (useful for quick preliminary check).
    """
    hasher = hashlib.sha256()
    bytes_read = 0
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
                bytes_read += len(chunk)
                if max_bytes and bytes_read >= max_bytes:
                    break
        return hasher.hexdigest()
    except Exception as e:
        get_logger().error(f"Error hashing file {file_path}: {e}")
        return ""


class DirectoryScanner:
    """Scans and analyzes folder structures for organization."""

    def __init__(self, root_dir: Path, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.root_dir = root_dir.resolve()
        self.rules_engine = RulesEngine(custom_rules)
        self.logger = get_logger()

    def scan(
        self,
        recursive: bool = False,
        detect_duplicates: bool = True,
        strategy: str = "category",
        quarantine_duplicates: bool = True,
        use_custom_rules: bool = True,
    ) -> Dict[str, Any]:
        """Executes full scan of the directory."""
        start_time = time.time()
        files_list: List[Dict[str, Any]] = []
        size_groups: Dict[int, List[Path]] = defaultdict(list)
        category_counts: Dict[str, int] = defaultdict(int)
        category_sizes: Dict[str, int] = defaultdict(int)
        total_bytes = 0

        # Scan filesystem
        try:
            if recursive:
                for root, dirs, filenames in os.walk(self.root_dir):
                    # Filter out excluded directories in-place
                    dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDED_DIRS]
                    curr_root = Path(root)
                    for fname in filenames:
                        fpath = curr_root / fname
                        self._process_single_file_record(fpath, files_list, size_groups)
            else:
                for entry in os.scandir(self.root_dir):
                    if entry.is_file(follow_symlinks=False):
                        fpath = Path(entry.path)
                        self._process_single_file_record(fpath, files_list, size_groups)

        except Exception as e:
            self.logger.error(f"Scan failed on {self.root_dir}: {e}")
            raise

        # Duplicate detection (two-pass for blazing fast speed)
        # 1. Group by exact file size
        # 2. For items sharing exact same size > 0, compute SHA-256 hash
        duplicate_hashes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        duplicate_file_paths: Set[str] = set()
        wasted_duplicate_bytes = 0

        if detect_duplicates:
            # Map files by path for fast lookup
            file_lookup = {f["path"]: f for f in files_list}

            for size, paths in size_groups.items():
                if len(paths) > 1 and size > 0:
                    hash_buckets: Dict[str, List[Path]] = defaultdict(list)
                    for p in paths:
                        fhash = calculate_file_hash(p)
                        if fhash:
                            hash_buckets[fhash].append(p)

                    for fhash, matching_paths in hash_buckets.items():
                        if len(matching_paths) > 1:
                            # Keep first as original, mark rest as duplicate
                            group_records = []
                            for idx, mp in enumerate(matching_paths):
                                record = file_lookup[str(mp)]
                                record["file_hash"] = fhash
                                if idx > 0:
                                    record["is_duplicate"] = True
                                    duplicate_file_paths.add(str(mp))
                                    wasted_duplicate_bytes += record["size_bytes"]
                                group_records.append(record)
                            duplicate_hashes[fhash] = group_records

        # Calculate destination and categories for all files
        for item in files_list:
            is_dup = item.get("is_duplicate", False)
            target_subfolder, cat_name = self.rules_engine.determine_destination(
                Path(item["path"]),
                item["size_bytes"],
                strategy=strategy,
                is_duplicate=is_dup,
                quarantine_duplicates=quarantine_duplicates,
                use_custom_rules=use_custom_rules,
            )

            item["target_subfolder"] = target_subfolder
            item["target_full_path"] = str(self.root_dir / target_subfolder / item["name"])
            item["display_category"] = cat_name

            base_cat = item["category"]
            category_counts[base_cat] += 1
            category_sizes[base_cat] += item["size_bytes"]
            total_bytes += item["size_bytes"]

            meta = CATEGORY_METADATA.get(base_cat, CATEGORY_METADATA.get(OTHER_CATEGORY_NAME, {}))
            item["icon"] = meta.get("icon", "fa-file")
            item["color"] = meta.get("color", "#64748b")
            item["bg_color"] = meta.get("bg", "rgba(100, 116, 139, 0.15)")

        elapsed = time.time() - start_time

        # Format duplicate groups for frontend display
        duplicate_groups_list = []
        for fhash, group in duplicate_hashes.items():
            duplicate_groups_list.append({
                "hash": fhash,
                "file_name": group[0]["name"],
                "size_formatted": group[0]["size_formatted"],
                "count": len(group),
                "files": group
            })

        # Category summary list in preferred order
        category_summary = []
        for cat in ORDERED_CATEGORIES:
            if cat in category_counts:
                meta = CATEGORY_METADATA.get(cat, {})
                category_summary.append({
                    "name": cat,
                    "count": category_counts[cat],
                    "size_bytes": category_sizes[cat],
                    "size_formatted": format_size(category_sizes[cat]),
                    "icon": meta.get("icon", "fa-file"),
                    "color": meta.get("color", "#64748b"),
                    "bg_color": meta.get("bg", "rgba(100,116,139,0.15)")
                })

        return {
            "root_dir": str(self.root_dir),
            "total_files": len(files_list),
            "total_size_bytes": total_bytes,
            "total_size_formatted": format_size(total_bytes),
            "duplicates_count": len(duplicate_file_paths),
            "wasted_duplicate_bytes": wasted_duplicate_bytes,
            "wasted_duplicate_formatted": format_size(wasted_duplicate_bytes),
            "scan_duration_sec": round(elapsed, 3),
            "files": files_list,
            "duplicate_groups": duplicate_groups_list,
            "categories": category_summary,
        }

    def _process_single_file_record(
        self,
        fpath: Path,
        files_list: List[Dict[str, Any]],
        size_groups: Dict[int, List[Path]],
    ) -> None:
        """Extracts stats and creates dictionary entry for a single file."""
        try:
            stat = fpath.stat()
            size = stat.st_size
            ext = fpath.suffix.lower()
            cat = self.rules_engine.get_category_for_file(fpath)

            file_info = {
                "name": fpath.name,
                "stem": fpath.stem,
                "extension": ext,
                "path": str(fpath),
                "size_bytes": size,
                "size_formatted": format_size(size),
                "modified_time": stat.st_mtime,
                "modified_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "category": cat,
                "is_duplicate": False,
                "file_hash": "",
            }

            files_list.append(file_info)
            size_groups[size].append(fpath)
        except (PermissionError, FileNotFoundError, OSError):
            pass
