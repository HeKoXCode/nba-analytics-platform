"""Contract-driven transformations with row-level quarantine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from nba_pipeline.contracts import ColumnSpec, TableSpec

BOOLEAN_MAP = {
    "1": True,
    "true": True,
    "t": True,
    "yes": True,
    "y": True,
    "si": True,
    "sí": True,
    "0": False,
    "false": False,
    "f": False,
    "no": False,
    "n": False,
}
HEIGHT_PATTERN = re.compile(r"^\s*(\d+)\s*[-']\s*(\d+)\s*$")


@dataclass
class TransformResult:
    table: str
    output_name: str
    accepted: pd.DataFrame
    rejected: pd.DataFrame
    metrics: dict[str, Any]


def read_source(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        encoding="utf-8-sig",
        dtype="string",
        keep_default_na=False,
        na_filter=False,
    )


def normalize_nulls(series: pd.Series, spec: ColumnSpec) -> pd.Series:
    normalized = series.astype("string").str.strip()
    lowered = normalized.str.lower()
    return normalized.mask(lowered.isin(spec.null_tokens), pd.NA)


def convert_column(series: pd.Series, spec: ColumnSpec) -> tuple[pd.Series, pd.Series]:
    source = normalize_nulls(series, spec)
    source_present = source.notna()

    if spec.dtype == "string":
        converted = source.astype("string")
        invalid = pd.Series(False, index=source.index)
    elif spec.dtype == "integer":
        numeric = pd.to_numeric(source, errors="coerce")
        fractional = numeric.notna() & numeric.mod(1).ne(0)
        invalid = source_present & (numeric.isna() | fractional)
        converted = numeric.mask(fractional).astype("Int64")
    elif spec.dtype == "float":
        converted = pd.to_numeric(source, errors="coerce").astype("Float64")
        invalid = source_present & converted.isna()
    elif spec.dtype == "boolean":
        mapped = source.str.lower().map(BOOLEAN_MAP)
        converted = mapped.astype("boolean")
        invalid = source_present & converted.isna()
    elif spec.dtype == "date":
        parsed = pd.to_datetime(source, errors="coerce", format="mixed")
        invalid = source_present & parsed.isna()
        converted = parsed.dt.strftime("%Y-%m-%d").astype("string")
    else:
        raise ValueError(f"Tipo de contrato no soportado: {spec.dtype}")

    return converted, invalid.fillna(False)


def _add_reason(reasons: list[list[str]], mask: pd.Series, reason: str) -> None:
    for position, rejected in enumerate(mask.fillna(False).tolist()):
        if rejected:
            reasons[position].append(reason)


def _derive_height(frame: pd.DataFrame) -> None:
    inches: list[float | None] = []
    for value in frame["height"].tolist():
        if pd.isna(value):
            inches.append(None)
            continue
        match = HEIGHT_PATTERN.match(str(value))
        if not match:
            inches.append(None)
            continue
        feet, remainder = (int(part) for part in match.groups())
        inches.append(float(feet * 12 + remainder) if remainder < 12 else None)
    frame["height_inches"] = pd.Series(inches, index=frame.index, dtype="Float64")
    frame["height_cm"] = (frame["height_inches"] * 2.54).round(2).astype("Float64")


def _derive_game_season(frame: pd.DataFrame) -> None:
    frame["season_year"] = frame["season_id"].mod(10_000).astype("Int64")
    stage = frame["season_type"].replace({"All-Star": "All Star"})
    frame["season_stage"] = stage.astype("string")


def transform_table(path: Path, spec: TableSpec) -> TransformResult:
    raw = read_source(path)
    actual_columns = tuple(raw.columns)
    if actual_columns != spec.input_columns:
        missing = sorted(set(spec.input_columns) - set(actual_columns))
        extra = sorted(set(actual_columns) - set(spec.input_columns))
        raise ValueError(
            f"Contrato de columnas incumplido en {path.name}: missing={missing}, extra={extra}, "
            f"order_matches={set(actual_columns) == set(spec.input_columns)}"
        )

    raw = raw.copy()
    raw.insert(0, "_source_row_number", range(2, len(raw) + 2))
    converted = pd.DataFrame(index=raw.index)
    reasons: list[list[str]] = [[] for _ in range(len(raw))]
    column_metrics: dict[str, dict[str, int]] = {}

    for column in spec.columns:
        source = raw[column.name]
        output, invalid_type = convert_column(source, column)
        converted[column.canonical_name] = output
        _add_reason(reasons, invalid_type, f"invalid_type:{column.name}")

        if not column.nullable:
            _add_reason(reasons, output.isna(), f"null_not_allowed:{column.name}")
        if column.allowed:
            _add_reason(
                reasons,
                output.notna() & ~output.isin(column.allowed),
                f"domain_violation:{column.name}",
            )
        if column.minimum is not None:
            _add_reason(
                reasons,
                output.notna() & output.lt(column.minimum),
                f"below_minimum:{column.name}",
            )
        if column.maximum is not None:
            _add_reason(
                reasons,
                output.notna() & output.gt(column.maximum),
                f"above_maximum:{column.name}",
            )

        source_nonnull = int(normalize_nulls(source, column).notna().sum())
        output_nonnull = int(output.notna().sum())
        column_metrics[column.name] = {
            "input_nonnull": source_nonnull,
            "output_nonnull": output_nonnull,
            "introduced_nulls": int(invalid_type.sum()),
        }
        if source_nonnull and output_nonnull == 0:
            raise ValueError(
                f"La transformación convirtió el 100 % de {spec.name}.{column.name} en nulos."
            )

    key_columns = list(spec.output_primary_key)
    duplicate_mask = converted.duplicated(key_columns, keep="first")
    _add_reason(reasons, duplicate_mask, "duplicate_primary_key")

    if spec.name == "common_player_info":
        _derive_height(converted)
    elif spec.name == "game":
        _derive_game_season(converted)
    elif spec.name == "team":
        converted["is_historical_unmapped"] = pd.Series(
            False, index=converted.index, dtype="boolean"
        )

    rejected_mask = pd.Series([bool(items) for items in reasons], index=raw.index)
    accepted = converted.loc[~rejected_mask].copy()
    accepted = accepted.sort_values(key_columns, kind="stable").reset_index(drop=True)

    rejected = raw.loc[rejected_mask].copy()
    rejected["_reject_reasons"] = [
        "|".join(items)
        for items, is_rejected in zip(reasons, rejected_mask, strict=True)
        if is_rejected
    ]
    rejected = rejected.reset_index(drop=True)

    reason_counts: dict[str, int] = {}
    for items in reasons:
        for reason in items:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return TransformResult(
        table=spec.name,
        output_name=spec.output_name,
        accepted=accepted,
        rejected=rejected,
        metrics={
            "input_rows": len(raw),
            "accepted_source_rows": len(accepted),
            "rejected_rows": len(rejected),
            "generated_rows": 0,
            "output_rows": len(accepted),
            "reason_counts": dict(sorted(reason_counts.items())),
            "columns": column_metrics,
        },
    )
