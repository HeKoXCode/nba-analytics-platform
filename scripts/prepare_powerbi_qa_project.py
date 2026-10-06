"""Create a non-destructive Power BI project copy for isolated SQL QA.

The published source continues to point to NBA_Project. This script changes
only the database name in a new copy; it refuses an existing destination.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam"
DATABASE_PATTERN = re.compile(r"^NBA_EN_QA_[0-9]{8}$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    if not DATABASE_PATTERN.fullmatch(args.database):
        raise ValueError("Only a dedicated NBA_EN_QA_YYYYMMDD database is allowed")
    destination = args.destination.resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to replace an existing project: {destination}")
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)

    shutil.copytree(SOURCE, destination, symlinks=True)
    changed = 0
    original = 'Sql.Database(".\\SQLEXPRESS", "NBA_Project")'
    replacement = f'Sql.Database(".\\SQLEXPRESS", "{args.database}")'
    for path in sorted((destination / "Model" / "tables").glob("*.tmdl")):
        text = path.read_text(encoding="utf-8-sig")
        if text.count(original) != 1:
            raise ValueError(f"Expected one portable SQL source in {path.name}")
        path.write_text(text.replace(original, replacement), encoding="utf-8", newline="\n")
        changed += 1
    if changed != 15:
        raise ValueError(f"Expected 15 model tables, found {changed}")
    print(f"QA-only Power BI source: {destination} ({changed} connection strings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
