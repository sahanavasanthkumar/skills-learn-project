"""Demo sandbox folder generator with diverse dummy files for testing."""

import os
import shutil
from pathlib import Path
from typing import Dict, Any

from config import BASE_DIR
from backend.logger import get_logger

DEMO_DIR = BASE_DIR / "demo_sandbox"


def clean_directory(dir_path: Path):
    """Safely cleans all files and subfolders inside a directory without failing on Windows lock."""
    if not dir_path.exists():
        return
    import stat
    def handle_remove_readonly(func, path, exc):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    try:
        shutil.rmtree(dir_path, onerror=handle_remove_readonly)
    except Exception:
        # Fallback: remove child entries
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for f in files:
                try:
                    fp = Path(root) / f
                    fp.chmod(stat.S_IWRITE)
                    fp.unlink(missing_ok=True)
                except Exception:
                    pass
            for d in dirs:
                try:
                    (Path(root) / d).rmdir()
                except Exception:
                    pass


def create_demo_sandbox() -> Dict[str, Any]:
    """Creates a clean demo sandbox directory with sample files across various categories and duplicates."""
    logger = get_logger()
    
    # Reset cleanly
    try:
        clean_directory(DEMO_DIR)
    except Exception as e:
        logger.warning(f"Could not cleanly reset sandbox: {e}")

    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    # Sample text content
    pdf_content = b"%PDF-1.4 Mock PDF file content for testing automated file organizer.\n%%EOF"
    doc_content = "Quarterly Business Review Report\nKey Performance Indicators & Growth Strategy 2026\n"
    code_content = "#!/usr/bin/env python3\n\ndef main():\n    print('Automated File Organizer Rocks!')\n\nif __name__ == '__main__':\n    main()\n"
    js_content = "console.log('Frontend UI module initialized');\nexport const version = '2.0.0';\n"
    csv_content = "id,product_name,category,price,inventory\n101,MacBook Pro,Laptops,1999,45\n102,Sony WH-1000XM5,Audio,399,120\n103,Dell 4K Monitor,Displays,599,30\n"
    
    # 1x1 Transparent PNG byte mockup
    png_content = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360606060000000050001a7e48b520000000049454e44ae426082"
    )
    # Duplicate image byte mockup
    dup_image_content = b"GENERIC_BINARY_MOCK_IMAGE_DATA_XYZ_1234567890_SAMPLE"
    audio_content = b"ID3\x03\x00\x00\x00\x00\x00#TIT2\x00\x00\x00\x10\x00\x00\x00Cyberpunk Beat"

    sample_files = [
        # Documents
        ("Annual_Financial_Report_2025.pdf", pdf_content),
        ("Project_Proposal_Draft.docx", doc_content.encode("utf-8")),
        ("Meeting_Notes_Sept.txt", doc_content.encode("utf-8")),
        ("Resume_Candidate.pdf", pdf_content),
        
        # Images
        ("hero_banner_neon.png", png_content),
        ("landscape_photo_mountain.jpg", dup_image_content),
        ("landscape_photo_mountain_copy.jpg", dup_image_content),  # DUPLICATE 1
        ("landscape_photo_mountain (1).jpg", dup_image_content),   # DUPLICATE 2
        ("profile_avatar.webp", b"WEBP MOCK DATA AVATAR 999"),

        # Code & Web
        ("organizer_script.py", code_content.encode("utf-8")),
        ("dashboard_controller.js", js_content.encode("utf-8")),
        ("styles_theme.css", b"body { background: #0f172a; color: #fff; }"),
        ("database_schema.sql", b"CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255));"),

        # Spreadsheets & Data
        ("Sales_Q3_Summary.csv", csv_content.encode("utf-8")),
        ("Inventory_Audit_2026.xlsx", b"MOCK EXCEL ZIP BINARY DATA SHEET 1"),

        # Audio & Media
        ("podcast_episode_42.mp3", audio_content),
        ("background_ambient.wav", audio_content),
        ("intro_trailer_4k.mp4", b"MOCK MP4 VIDEO STREAM DATA HEADER"),

        # Archives & Installers
        ("backup_project_archive.zip", b"PK\x03\x04\x14\x00\x00\x00MOCK_ZIP_ARCHIVE_DATA"),
        ("setup_installer_tool.exe", b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00MOCK_EXE"),
    ]

    for fname, content in sample_files:
        fpath = DEMO_DIR / fname
        try:
            with open(fpath, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to create demo file {fname}: {e}")

    logger.info(f"Created demo sandbox at {DEMO_DIR} with {len(sample_files)} sample files.")

    return {
        "success": True,
        "path": str(DEMO_DIR),
        "total_files": len(sample_files),
        "message": f"Demo sandbox created with {len(sample_files)} diverse files at {DEMO_DIR}"
    }
