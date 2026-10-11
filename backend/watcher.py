"""Real-time folder watcher daemon using watchdog."""

import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
from watchdog.observers import Observer

from backend.database import get_watchers, save_or_update_watcher
from backend.logger import get_logger
from backend.organizer import FileOrganizer
from backend.utils import validate_directory


class AutoOrganizeEventHandler(FileSystemEventHandler):
    """Handles file system events for monitored folders."""

    def __init__(self, folder_path: Path, strategy: str = "category", handle_duplicates: bool = True):
        super().__init__()
        self.folder_path = folder_path.resolve()
        self.strategy = strategy
        self.handle_duplicates = handle_duplicates
        self.logger = get_logger()
        self.recent_events: List[Dict[str, Any]] = []

    def on_created(self, event):
        if not event.is_directory:
            self._handle_new_file(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self._handle_new_file(Path(event.dest_path))

    def _handle_new_file(self, file_path: Path):
        # Ignore temp files or hidden files
        if file_path.name.startswith((".", "~$", "__perm_probe")):
            return
        
        # Check if file is directly in the watched root directory (not already inside a category subfolder)
        if file_path.parent != self.folder_path:
            return

        # Wait briefly for file write lock release (e.g. download finishing)
        threading.Thread(target=self._delayed_process, args=(file_path,), daemon=True).start()

    def _delayed_process(self, file_path: Path):
        time.sleep(1.5)  # Wait for file download / copy to complete
        if not file_path.exists():
            return

        # Check file stability (size not changing)
        try:
            initial_size = file_path.stat().st_size
            time.sleep(0.5)
            if file_path.stat().st_size != initial_size:
                time.sleep(1.5)
        except Exception:
            return

        self.logger.info(f"[AutoWatcher] Detected new file in {self.folder_path}: {file_path.name}")
        try:
            organizer = FileOrganizer(self.folder_path)
            res = organizer.execute(
                strategy=self.strategy,
                recursive=False,
                detect_duplicates=self.handle_duplicates,
                quarantine_duplicates=self.handle_duplicates,
                use_custom_rules=True,
                selected_file_paths=[str(file_path)],
            )
            event_log = {
                "timestamp": time.strftime("%H:%M:%S"),
                "folder": str(self.folder_path),
                "file": file_path.name,
                "status": "Organized" if res["summary"]["moved_files"] > 0 else "Skipped"
            }
            self.recent_events.append(event_log)
            if len(self.recent_events) > 50:
                self.recent_events.pop(0)
        except Exception as e:
            self.logger.error(f"[AutoWatcher] Error processing {file_path}: {e}")


class WatcherManager:
    """Manages active watchdog observers across multiple directories."""

    def __init__(self):
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, AutoOrganizeEventHandler] = {}
        self.lock = threading.Lock()
        self.logger = get_logger()

    def start_watcher(self, folder_path_str: str, strategy: str = "category", handle_duplicates: bool = True) -> Dict[str, Any]:
        """Starts real-time monitoring on a directory."""
        is_valid, err, resolved = validate_directory(folder_path_str)
        if not is_valid or resolved is None:
            return {"success": False, "error": err}

        key = str(resolved)
        with self.lock:
            if key in self.observers and self.observers[key].is_alive():
                return {"success": True, "message": "Watcher is already active for this directory", "folder": key}

            handler = AutoOrganizeEventHandler(resolved, strategy=strategy, handle_duplicates=handle_duplicates)
            observer = Observer()
            observer.schedule(handler, str(resolved), recursive=False)
            observer.start()

            self.observers[key] = observer
            self.handlers[key] = handler

            save_or_update_watcher(
                folder_path=key,
                strategy=strategy,
                auto_organize=True,
                handle_duplicates=handle_duplicates,
                is_active=True
            )
            self.logger.info(f"Started real-time watcher on: {key}")

        return {"success": True, "message": f"Real-time watcher active on {key}", "folder": key}

    def stop_watcher(self, folder_path_str: str) -> Dict[str, Any]:
        """Stops monitoring on a directory."""
        is_valid, _, resolved = validate_directory(folder_path_str)
        key = str(resolved) if resolved else folder_path_str

        with self.lock:
            if key in self.observers:
                observer = self.observers.pop(key)
                try:
                    observer.stop()
                    observer.join(timeout=2.0)
                except Exception as e:
                    self.logger.error(f"Error stopping watcher: {e}")
                self.handlers.pop(key, None)

            save_or_update_watcher(folder_path=key, is_active=False)
            self.logger.info(f"Stopped real-time watcher on: {key}")

        return {"success": True, "message": f"Watcher stopped for {key}"}

    def get_status(self) -> List[Dict[str, Any]]:
        """Returns the status and recent events of all registered watchers."""
        watchers = get_watchers()
        results = []
        for w in watchers:
            key = w["folder_path"]
            is_running = key in self.observers and self.observers[key].is_alive()
            events = self.handlers[key].recent_events if key in self.handlers else []
            results.append({
                "id": w["id"],
                "folder_path": key,
                "strategy": w["strategy"],
                "auto_organize": bool(w["auto_organize"]),
                "handle_duplicates": bool(w["handle_duplicates"]),
                "is_active": is_running,
                "recent_events": events,
                "created_at": w["created_at"],
            })
        return results

    def stop_all(self):
        """Stops all running watchers during shutdown."""
        with self.lock:
            for key, observer in list(self.observers.items()):
                try:
                    observer.stop()
                    observer.join(timeout=1.0)
                except Exception:
                    pass
            self.observers.clear()
            self.handlers.clear()


# Global Watcher Manager instance
watcher_manager = WatcherManager()
