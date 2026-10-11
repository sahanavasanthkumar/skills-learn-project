"""Global Configuration for Automated File Organizer."""

from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Core runtime directories
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "organizer.db"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "activity.log"

REPORTS_DIR = BASE_DIR / "reports"
REPORT_FILE = REPORTS_DIR / "organization_report.json"

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Chunk size for streaming SHA-256 calculations (8 KB)
CHUNK_SIZE = 8192

# Reserved subfolder names
DUPLICATES_FOLDER_NAME = "Duplicates"
OTHER_CATEGORY_NAME = "Other"

# Category to file extensions mapping
CATEGORY_EXTENSIONS: dict[str, list[str]] = {
    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
    ],
    "Images": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",
    ],
    "Videos": [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
    ],
    "Audio": [
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
    ],
    "Code": [
        ".py",
        ".java",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".cpp",
        ".c",
        ".php",
        ".sql",
    ],
    "Spreadsheets": [
        ".xls",
        ".xlsx",
        ".csv",
    ],
    "Presentations": [
        ".ppt",
        ".pptx",
    ],
    "Archives": [
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
    ],
    "Applications": [
        ".exe",
        ".msi",
    ],
}

# Category visual styling metadata for web interface
CATEGORY_METADATA: dict[str, dict[str, str]] = {
    "Documents": {"icon": "fa-file-lines", "color": "#3b82f6", "bg": "rgba(59, 130, 246, 0.15)"},
    "Images": {"icon": "fa-image", "color": "#ec4899", "bg": "rgba(236, 72, 153, 0.15)"},
    "Videos": {"icon": "fa-video", "color": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.15)"},
    "Audio": {"icon": "fa-music", "color": "#10b981", "bg": "rgba(16, 185, 129, 0.15)"},
    "Code": {"icon": "fa-code", "color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.15)"},
    "Spreadsheets": {"icon": "fa-file-excel", "color": "#059669", "bg": "rgba(5, 150, 105, 0.15)"},
    "Presentations": {"icon": "fa-file-powerpoint", "color": "#ea580c", "bg": "rgba(234, 88, 12, 0.15)"},
    "Archives": {"icon": "fa-box-archive", "color": "#6366f1", "bg": "rgba(99, 102, 241, 0.15)"},
    "Applications": {"icon": "fa-window-restore", "color": "#06b6d4", "bg": "rgba(6, 182, 212, 0.15)"},
    "Other": {"icon": "fa-file", "color": "#64748b", "bg": "rgba(100, 116, 139, 0.15)"},
    "Duplicates": {"icon": "fa-copy", "color": "#ef4444", "bg": "rgba(239, 68, 68, 0.15)"},
}

# Inverted mapping: extension -> category
EXTENSION_TO_CATEGORY: dict[str, str] = {}
for category, extensions in CATEGORY_EXTENSIONS.items():
    for ext in extensions:
        EXTENSION_TO_CATEGORY[ext.lower()] = category

# Preferred category ordering
ORDERED_CATEGORIES: list[str] = [
    "Documents",
    "Images",
    "Videos",
    "Audio",
    "Code",
    "Spreadsheets",
    "Presentations",
    "Archives",
    "Applications",
    OTHER_CATEGORY_NAME,
]

# Standard category subfolder names
CATEGORY_FOLDERS: set[str] = set(CATEGORY_EXTENSIONS.keys()) | {
    DUPLICATES_FOLDER_NAME,
    OTHER_CATEGORY_NAME,
}

# Directories to skip when scanning a folder (system and runtime folders only)
DEFAULT_EXCLUDED_DIRS: set[str] = {
    "logs",
    "database",
    "reports",
    "templates",
    "static",
    "backend",
    ".git",
    ".svn",
    ".hg",
    ".vscode",
    ".idea",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "$RECYCLE.BIN",
    "System Volume Information",
}
