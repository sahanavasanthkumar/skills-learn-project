"""Rule engine for categorizing files and evaluating custom user rules."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import (
    CATEGORY_EXTENSIONS,
    CATEGORY_METADATA,
    DUPLICATES_FOLDER_NAME,
    EXTENSION_TO_CATEGORY,
    OTHER_CATEGORY_NAME,
)
from backend.database import get_custom_rules


class RulesEngine:
    """Evaluates rules to determine target subfolders and categories for files."""

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        if custom_rules is None:
            self.custom_rules = [r for r in get_custom_rules() if r.get("enabled", 1)]
        else:
            self.custom_rules = [r for r in custom_rules if r.get("enabled", 1)]
        
        # Sort custom rules by priority ascending
        self.custom_rules.sort(key=lambda x: x.get("priority", 10))

    def evaluate_custom_rules(self, file_path: Path, file_size: int) -> Optional[str]:
        """Checks if file matches any active custom rules.
        
        Returns target_folder if matched, else None.
        """
        filename = file_path.name
        stem = file_path.stem
        ext = file_path.suffix.lower()

        for rule in self.custom_rules:
            cond = rule.get("condition_type", "")
            pat = rule.get("pattern", "")
            target = rule.get("target_folder", "").strip()

            if not target:
                continue

            try:
                if cond == "extension":
                    # Matches '.pdf' or 'pdf' or comma-separated '.pdf,.epub'
                    exts = [e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}" for e in pat.split(",")]
                    if ext in exts:
                        return target

                elif cond == "prefix":
                    if filename.lower().startswith(pat.lower()):
                        return target

                elif cond == "keyword":
                    if pat.lower() in filename.lower():
                        return target

                elif cond == "regex":
                    if re.search(pat, filename, re.IGNORECASE):
                        return target

                elif cond == "size_gt_mb":
                    threshold_bytes = float(pat) * 1024 * 1024
                    if file_size >= threshold_bytes:
                        return target

                elif cond == "size_lt_mb":
                    threshold_bytes = float(pat) * 1024 * 1024
                    if file_size < threshold_bytes:
                        return target

            except Exception:
                continue

        return None

    def get_category_for_file(self, file_path: Path) -> str:
        """Determines the default category based on file extension."""
        ext = file_path.suffix.lower()
        return EXTENSION_TO_CATEGORY.get(ext, OTHER_CATEGORY_NAME)

    def determine_destination(
        self,
        file_path: Path,
        file_size: int,
        strategy: str = "category",
        is_duplicate: bool = False,
        quarantine_duplicates: bool = True,
        use_custom_rules: bool = True,
    ) -> Tuple[str, str]:
        """Calculates destination subfolder and category label.
        
        Returns:
            Tuple of (target_subfolder, category_name)
        """
        # If it's a duplicate and duplicate isolation is turned on
        if is_duplicate and quarantine_duplicates:
            return DUPLICATES_FOLDER_NAME, "Duplicates"

        # Check custom rules first if enabled
        if use_custom_rules:
            custom_target = self.evaluate_custom_rules(file_path, file_size)
            if custom_target:
                category = self.get_category_for_file(file_path)
                return custom_target, f"Custom ({category})"

        category = self.get_category_for_file(file_path)

        if strategy == "category":
            return category, category

        elif strategy == "extension":
            ext = file_path.suffix.lower().lstrip(".")
            folder = ext.upper() if ext else "NoExtension"
            return f"By_Extension/{folder}", category

        elif strategy == "date_month":
            # Organizes by YYYY/MM (Creation / Modified Date)
            try:
                mtime = file_path.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                return f"{dt.year}/{dt.strftime('%m-%B')}", category
            except Exception:
                return "By_Date/Unknown", category

        elif strategy == "date_year":
            try:
                mtime = file_path.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                return f"{dt.year}", category
            except Exception:
                return "By_Year/Unknown", category

        elif strategy == "size":
            mb = file_size / (1024 * 1024)
            if mb < 1:
                size_folder = "Small (Under 1MB)"
            elif mb < 50:
                size_folder = "Medium (1MB - 50MB)"
            elif mb < 500:
                size_folder = "Large (50MB - 500MB)"
            else:
                size_folder = "Huge (Over 500MB)"
            return f"By_Size/{size_folder}", category

        return category, category
