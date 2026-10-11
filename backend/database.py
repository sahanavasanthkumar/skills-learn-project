"""Database manager for Automated File Organizer using SQLite."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from config import DB_PATH, DB_DIR


def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured with row factory."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes database schema and tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Batches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id TEXT PRIMARY KEY,
            root_dir TEXT NOT NULL,
            strategy TEXT NOT NULL,
            total_files INTEGER NOT NULL,
            moved_files INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_rolled_back INTEGER DEFAULT 0,
            summary_json TEXT
        )
    """)

    # File operations table for atomic undo/rollback
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            original_path TEXT NOT NULL,
            new_path TEXT NOT NULL,
            category TEXT,
            size_bytes INTEGER,
            file_hash TEXT,
            status TEXT DEFAULT 'moved', -- 'moved', 'rolled_back'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(batch_id) REFERENCES batches(batch_id)
        )
    """)

    # Custom rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            condition_type TEXT NOT NULL, -- 'extension', 'prefix', 'keyword', 'regex', 'size_gt_mb'
            pattern TEXT NOT NULL,
            target_folder TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Active folder watchers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path TEXT UNIQUE NOT NULL,
            strategy TEXT DEFAULT 'category',
            auto_organize INTEGER DEFAULT 1,
            handle_duplicates INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_batch(batch_id: str, root_dir: str, strategy: str, total_files: int, moved_files: int, summary: dict) -> None:
    """Saves a completed batch record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO batches (batch_id, root_dir, strategy, total_files, moved_files, summary_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (batch_id, root_dir, strategy, total_files, moved_files, json.dumps(summary))
    )
    conn.commit()
    conn.close()


def record_file_operation(batch_id: str, original_path: str, new_path: str, category: str, size_bytes: int, file_hash: str = "") -> None:
    """Records an individual file move operation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO file_operations (batch_id, original_path, new_path, category, size_bytes, file_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (batch_id, original_path, new_path, category, size_bytes, file_hash)
    )
    conn.commit()
    conn.close()


def record_file_operations_batch(operations: List[Dict[str, Any]]) -> None:
    """Bulk records file operations for speed."""
    if not operations:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO file_operations (batch_id, original_path, new_path, category, size_bytes, file_hash)
        VALUES (:batch_id, :original_path, :new_path, :category, :size_bytes, :file_hash)
        """,
        operations
    )
    conn.commit()
    conn.close()


def get_all_batches() -> List[Dict[str, Any]]:
    """Retrieves all organization batch histories ordered by latest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT batch_id, root_dir, strategy, total_files, moved_files, created_at, is_rolled_back, summary_json
        FROM batches
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "batch_id": r["batch_id"],
            "root_dir": r["root_dir"],
            "strategy": r["strategy"],
            "total_files": r["total_files"],
            "moved_files": r["moved_files"],
            "created_at": r["created_at"],
            "is_rolled_back": bool(r["is_rolled_back"]),
            "summary": json.loads(r["summary_json"]) if r["summary_json"] else {}
        })
    conn.close()
    return results


def get_batch_operations(batch_id: str) -> List[Dict[str, Any]]:
    """Retrieves all file operations for a specific batch."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, batch_id, original_path, new_path, category, size_bytes, file_hash, status, timestamp
        FROM file_operations
        WHERE batch_id = ?
        ORDER BY id ASC
    """, (batch_id,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def mark_batch_rolled_back(batch_id: str) -> None:
    """Marks batch and its operations as rolled back."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE batches SET is_rolled_back = 1 WHERE batch_id = ?", (batch_id,))
    cursor.execute("UPDATE file_operations SET status = 'rolled_back' WHERE batch_id = ?", (batch_id,))
    conn.commit()
    conn.close()


# Custom Rules DB Helpers
def get_custom_rules() -> List[Dict[str, Any]]:
    """Returns all custom sorting rules."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_rules ORDER BY priority ASC, id ASC")
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def add_custom_rule(name: str, condition_type: str, pattern: str, target_folder: str, priority: int = 10) -> int:
    """Adds a new custom rule."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO custom_rules (name, condition_type, pattern, target_folder, priority, enabled)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (name, condition_type, pattern, target_folder, priority)
    )
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rule_id


def delete_custom_rule(rule_id: int) -> bool:
    """Deletes a custom rule by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM custom_rules WHERE id = ?", (rule_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected


def toggle_custom_rule(rule_id: int, enabled: bool) -> bool:
    """Toggles rule enabled state."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE custom_rules SET enabled = ? WHERE id = ?", (1 if enabled else 0, rule_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected


# Watcher DB Helpers
def get_watchers() -> List[Dict[str, Any]]:
    """Gets all configured watchers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def save_or_update_watcher(folder_path: str, strategy: str = "category", auto_organize: bool = True, handle_duplicates: bool = True, is_active: bool = False) -> int:
    """Saves or updates watcher configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO watchers (folder_path, strategy, auto_organize, handle_duplicates, is_active)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(folder_path) DO UPDATE SET
            strategy=excluded.strategy,
            auto_organize=excluded.auto_organize,
            handle_duplicates=excluded.handle_duplicates,
            is_active=excluded.is_active
        """,
        (folder_path, strategy, 1 if auto_organize else 0, 1 if handle_duplicates else 0, 1 if is_active else 0)
    )
    watcher_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return watcher_id


def delete_watcher(watcher_id: int) -> bool:
    """Deletes a watcher config."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchers WHERE id = ?", (watcher_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected


# Initialize database on module load
init_db()
