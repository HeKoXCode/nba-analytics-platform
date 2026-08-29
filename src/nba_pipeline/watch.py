"""Watch mode built on the same initial-load path as the explicit CLI command."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from nba_pipeline.pipeline import run_pipeline


class RawFileHandler(FileSystemEventHandler):
    def __init__(self, input_dir: Path, runs_dir: Path, cooldown_seconds: float) -> None:
        self.input_dir = input_dir
        self.runs_dir = runs_dir
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._last_run = 0.0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory or not str(event.src_path).lower().endswith("_raw.csv"):
            return
        now = time.monotonic()
        if now - self._last_run < self.cooldown_seconds or not self._lock.acquire(blocking=False):
            return
        try:
            self._last_run = now
            run_name = datetime.now(UTC).strftime("watch-%Y%m%dT%H%M%SZ")
            run_pipeline(self.input_dir, self.runs_dir / run_name)
        finally:
            self._lock.release()


def watch_pipeline(
    input_dir: Path,
    runs_dir: Path,
    *,
    initial_load: bool = True,
    cooldown_seconds: float = 15.0,
) -> None:
    input_dir = input_dir.resolve()
    runs_dir = runs_dir.resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)
    if initial_load:
        run_name = datetime.now(UTC).strftime("initial-%Y%m%dT%H%M%SZ")
        run_pipeline(input_dir, runs_dir / run_name)

    handler = RawFileHandler(input_dir, runs_dir, cooldown_seconds)
    observer = Observer()
    observer.schedule(handler, str(input_dir), recursive=False)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.stop()
        observer.join()
