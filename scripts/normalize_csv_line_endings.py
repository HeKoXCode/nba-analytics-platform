"""Normalize the six versioned source CSV files to repository-stable LF bytes."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "CODE" / "data_raw"
EXPECTED = {
    "common_player_info_raw.csv",
    "game_raw.csv",
    "game_summary_raw.csv",
    "other_stats_raw.csv",
    "player_raw.csv",
    "team_raw.csv",
}


def main() -> int:
    paths = sorted(DATA.glob("*_raw.csv"))
    if {path.name for path in paths} != EXPECTED:
        raise SystemExit("El conjunto de seis CSV no coincide con el contrato.")
    for path in paths:
        payload = path.read_bytes().replace(b"\r\n", b"\n")
        if b"\r" in payload:
            raise SystemExit(f"Retorno de carro inesperado: {path.name}")
        path.write_bytes(payload)
    total_bytes = sum(path.stat().st_size for path in paths)
    print(f"CSV normalizados a LF: {len(paths)} archivos; {total_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
