"""Small deterministic I/O and logging helpers."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_utc(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(payload))
    os.replace(temporary, path)


class JsonLogger:
    """Emit one ASCII-safe JSON object per line to console and disk."""

    def __init__(self, stream: TextIO, run_id: str) -> None:
        self.stream = stream
        self.run_id = run_id

    def emit(self, event: str, **details: Any) -> None:
        payload = {
            "timestamp_utc": iso_utc(),
            "run_id": self.run_id,
            "event": event,
            **details,
        }
        line = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        self.stream.write(line + "\n")
        self.stream.flush()
        print(line, flush=True)
