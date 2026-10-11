"""Automated File Organizer - Full Stack Flask Web Application."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from config import (
    BASE_DIR,
    CATEGORY_EXTENSIONS,
    CATEGORY_METADATA,
    ORDERED_CATEGORIES,
)
from backend.database import (
    add_custom_rule,
    delete_custom_rule,
    delete_watcher,
    get_all_batches,
    get_batch_operations,
    get_custom_rules,
    toggle_custom_rule,
)
from backend.demo_generator import DEMO_DIR, create_demo_sandbox
from backend.logger import get_logger, get_recent_logs
from backend.organizer import FileOrganizer, rollback_batch
from backend.scanner import DirectoryScanner
from backend.utils import validate_directory
from backend.watcher import watcher_manager

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
CORS(app)
logger = get_logger()


@app.route("/")
def index():
    """Renders main dashboard interface."""
    return render_template("index.html")


@app.route("/api/shortcuts", methods=["GET"])
def get_shortcuts():
    """Returns quick accessible directories on the host machine."""
    user_home = Path.home()
    shortcuts = [
        {"name": "Downloads", "icon": "fa-download", "path": str(user_home / "Downloads")},
        {"name": "Desktop", "icon": "fa-desktop", "path": str(user_home / "Desktop")},
        {"name": "Documents", "icon": "fa-folder-open", "path": str(user_home / "Documents")},
        {"name": "Pictures", "icon": "fa-images", "path": str(user_home / "Pictures")},
        {"name": "Videos", "icon": "fa-film", "path": str(user_home / "Videos")},
        {"name": "Demo Sandbox", "icon": "fa-flask-vial", "path": str(DEMO_DIR)},
    ]
    # Filter only existing paths (except demo which can be created)
    valid_shortcuts = [
        s for s in shortcuts
        if Path(s["path"]).exists() or s["name"] == "Demo Sandbox"
    ]
    return jsonify({"shortcuts": valid_shortcuts, "default_path": str(DEMO_DIR if DEMO_DIR.exists() else user_home / "Downloads")})


@app.route("/api/scan", methods=["POST"])
def scan_folder():
    """Scans target directory and returns item analysis."""
    data = request.get_json() or {}
    folder_path = data.get("folder_path", "").strip()
    recursive = bool(data.get("recursive", False))
    detect_duplicates = bool(data.get("detect_duplicates", True))
    strategy = data.get("strategy", "category")
    quarantine_duplicates = bool(data.get("quarantine_duplicates", True))
    use_custom_rules = bool(data.get("use_custom_rules", True))

    is_valid, err, resolved = validate_directory(folder_path)
    if not is_valid or resolved is None:
        return jsonify({"success": False, "error": err}), 400

    try:
        scanner = DirectoryScanner(resolved)
        result = scanner.scan(
            recursive=recursive,
            detect_duplicates=detect_duplicates,
            strategy=strategy,
            quarantine_duplicates=quarantine_duplicates,
            use_custom_rules=use_custom_rules,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/preview", methods=["POST"])
def preview_organization():
    """Generates simulation preview of organization moves."""
    data = request.get_json() or {}
    folder_path = data.get("folder_path", "").strip()
    strategy = data.get("strategy", "category")
    recursive = bool(data.get("recursive", False))
    detect_duplicates = bool(data.get("detect_duplicates", True))
    quarantine_duplicates = bool(data.get("quarantine_duplicates", True))
    use_custom_rules = bool(data.get("use_custom_rules", True))

    is_valid, err, resolved = validate_directory(folder_path)
    if not is_valid or resolved is None:
        return jsonify({"success": False, "error": err}), 400

    try:
        organizer = FileOrganizer(resolved)
        result = organizer.preview(
            strategy=strategy,
            recursive=recursive,
            detect_duplicates=detect_duplicates,
            quarantine_duplicates=quarantine_duplicates,
            use_custom_rules=use_custom_rules,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Error during preview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/organize", methods=["POST"])
def execute_organization():
    """Executes live organization moves."""
    data = request.get_json() or {}
    folder_path = data.get("folder_path", "").strip()
    strategy = data.get("strategy", "category")
    recursive = bool(data.get("recursive", False))
    detect_duplicates = bool(data.get("detect_duplicates", True))
    quarantine_duplicates = bool(data.get("quarantine_duplicates", True))
    use_custom_rules = bool(data.get("use_custom_rules", True))
    clean_empty_folders = bool(data.get("clean_empty_folders", False))
    selected_files = data.get("selected_files", None)

    is_valid, err, resolved = validate_directory(folder_path)
    if not is_valid or resolved is None:
        return jsonify({"success": False, "error": err}), 400

    try:
        organizer = FileOrganizer(resolved)
        result = organizer.execute(
            strategy=strategy,
            recursive=recursive,
            detect_duplicates=detect_duplicates,
            quarantine_duplicates=quarantine_duplicates,
            use_custom_rules=use_custom_rules,
            selected_file_paths=selected_files,
            clean_empty_folders=clean_empty_folders,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing organization: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def list_history():
    """Returns all past organization batches."""
    try:
        batches = get_all_batches()
        return jsonify({"success": True, "batches": batches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/<batch_id>", methods=["GET"])
def get_batch_details(batch_id: str):
    """Returns detailed file operations for a single batch."""
    try:
        ops = get_batch_operations(batch_id)
        return jsonify({"success": True, "operations": ops})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/<batch_id>/rollback", methods=["POST"])
def rollback_history_batch(batch_id: str):
    """Rolls back all changes made in a specific batch."""
    try:
        result = rollback_batch(batch_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/rules", methods=["GET", "POST"])
def handle_rules():
    """Gets all custom rules or creates a new rule."""
    if request.method == "GET":
        rules = get_custom_rules()
        return jsonify({"success": True, "rules": rules})

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    cond = data.get("condition_type", "").strip()
    pattern = data.get("pattern", "").strip()
    target = data.get("target_folder", "").strip()
    priority = int(data.get("priority", 10))

    if not name or not cond or not pattern or not target:
        return jsonify({"success": False, "error": "All fields (name, condition_type, pattern, target_folder) are required."}), 400

    try:
        rule_id = add_custom_rule(name, cond, pattern, target, priority)
        return jsonify({"success": True, "rule_id": rule_id, "message": "Rule created successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/rules/<int:rule_id>", methods=["DELETE"])
def remove_rule(rule_id: int):
    """Deletes a custom rule."""
    try:
        deleted = delete_custom_rule(rule_id)
        return jsonify({"success": deleted})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/rules/<int:rule_id>/toggle", methods=["POST"])
def toggle_rule(rule_id: int):
    """Toggles rule enabled state."""
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", True))
    try:
        updated = toggle_custom_rule(rule_id, enabled)
        return jsonify({"success": updated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/watchers", methods=["GET"])
def list_watchers():
    """Gets status of all folder watchers."""
    try:
        status = watcher_manager.get_status()
        return jsonify({"success": True, "watchers": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/watchers/start", methods=["POST"])
def start_watcher():
    """Starts monitoring a folder."""
    data = request.get_json() or {}
    folder_path = data.get("folder_path", "").strip()
    strategy = data.get("strategy", "category")
    handle_duplicates = bool(data.get("handle_duplicates", True))

    result = watcher_manager.start_watcher(folder_path, strategy, handle_duplicates)
    return jsonify(result)


@app.route("/api/watchers/stop", methods=["POST"])
def stop_watcher():
    """Stops monitoring a folder."""
    data = request.get_json() or {}
    folder_path = data.get("folder_path", "").strip()
    result = watcher_manager.stop_watcher(folder_path)
    return jsonify(result)


@app.route("/api/watchers/<int:watcher_id>", methods=["DELETE"])
def remove_watcher(watcher_id: int):
    """Removes a watcher config."""
    try:
        deleted = delete_watcher(watcher_id)
        return jsonify({"success": deleted})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/demo-sandbox", methods=["POST"])
def generate_demo():
    """Generates sandbox test directory."""
    try:
        res = create_demo_sandbox()
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/open-folder", methods=["POST"])
def open_folder_in_os():
    """Opens folder in native file explorer (Windows Explorer)."""
    data = request.get_json() or {}
    folder_path = data.get("folder_path", "").strip()
    is_valid, err, resolved = validate_directory(folder_path)
    if not is_valid or resolved is None:
        return jsonify({"success": False, "error": err}), 400

    try:
        if sys.platform == "win32":
            os.startfile(str(resolved))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(resolved)], check=False)
        else:
            subprocess.run(["xdg-open", str(resolved)], check=False)
        return jsonify({"success": True, "message": f"Opened {resolved}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Returns recent log lines."""
    max_lines = request.args.get("lines", 50, type=int)
    lines = get_recent_logs(max_lines=max_lines)
    return jsonify({"success": True, "logs": lines})


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Returns category extensions mapping and visual metadata."""
    return jsonify({
        "success": True,
        "categories": CATEGORY_EXTENSIONS,
        "metadata": CATEGORY_METADATA,
        "order": ORDERED_CATEGORIES,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Automated File Organizer server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
