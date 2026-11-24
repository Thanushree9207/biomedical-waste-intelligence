"""Inspect the supplied biomedical-waste workbook without modifying it.

This module intentionally uses openpyxl rather than pandas because the
project's current Windows policy blocks a pandas native extension.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = PROJECT_ROOT / "datasets" / "biomedical dataset.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
PRIMARY_SHEET = "State-wise 6 Years"
MISSING_MARKERS = {"", "na", "n/a", "not available", "not reported"}


def _json_value(value: Any) -> Any:
    """Convert workbook values to JSON-safe primitives."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _value_type(value: Any) -> str:
    if value is None or (
        isinstance(value, str) and value.strip().casefold() in MISSING_MARKERS
    ):
        return "missing"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "numeric"
    if isinstance(value, (date, datetime)):
        return "date"
    return "text"


def _find_header_row(rows: list[tuple[Any, ...]]) -> int | None:
    for index, row in enumerate(rows):
        if any(value is not None for value in row):
            return index
    return None


def _summarize_sheet(worksheet: Any) -> dict[str, Any]:
    rows = list(worksheet.iter_rows(values_only=True))
    header_index = _find_header_row(rows)
    if header_index is None:
        return {
            "dimensions": [worksheet.max_row, worksheet.max_column],
            "header_row": None,
            "columns": [],
            "record_count": 0,
            "duplicate_records": 0,
            "missing_by_column": {},
            "types_by_column": {},
            "numeric_summary": {},
        }

    raw_headers = rows[header_index]
    headers = [
        str(value).strip() if value is not None else f"Unnamed column {index + 1}"
        for index, value in enumerate(raw_headers)
    ]
    records = [
        tuple(row[: len(headers)])
        for row in rows[header_index + 1 :]
        if any(value is not None for value in row)
    ]
    duplicate_count = len(records) - len(set(records))
    missing: dict[str, int] = {}
    types: dict[str, dict[str, int]] = {}
    numeric: dict[str, dict[str, float | int | None]] = {}

    for index, header in enumerate(headers):
        values = [row[index] if index < len(row) else None for row in records]
        column_types = Counter(_value_type(value) for value in values)
        missing[header] = column_types.get("missing", 0)
        types[header] = dict(column_types)
        numeric_values = [
            float(value)
            for value in values
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value))
        ]
        if numeric_values:
            numeric[header] = {
                "count": len(numeric_values),
                "mean": statistics.fmean(numeric_values),
                "median": statistics.median(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
            }

    return {
        "dimensions": [worksheet.max_row, worksheet.max_column],
        "header_row": header_index + 1,
        "columns": headers,
        "record_count": len(records),
        "duplicate_records": duplicate_count,
        "missing_by_column": missing,
        "types_by_column": types,
        "numeric_summary": numeric,
    }


def inspect_workbook(
    workbook_path: Path = WORKBOOK_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    """Inspect every workbook sheet and save JSON and readable text reports."""
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Excel workbook not found: {workbook_path}")

    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        sheets = {
            worksheet.title: _summarize_sheet(worksheet)
            for worksheet in workbook.worksheets
        }
        if PRIMARY_SHEET not in sheets:
            raise ValueError(
                f"Expected analysis sheet {PRIMARY_SHEET!r} is missing. "
                f"Available sheets: {workbook.sheetnames}"
            )

        primary = sheets[PRIMARY_SHEET]
        columns = primary["columns"]
        available = set(columns)
        variable_candidates = {
            "year": ["Year"],
            "state_or_ut": ["State_UT_or_Reporting_Entity"],
            "waste_generated_kg_per_day": [
                "BMW_Generated_kg_per_day_as_reported"
            ],
            "waste_treated_kg_per_day": [
                "BMW_Treated_kg_per_day_as_reported"
            ],
            "government_hospital_beds_only": ["Total Hospitals (Govt.) Beds"],
            "treatment_capacity": [],
        }
        variables = {
            name: {
                "available_columns": [
                    candidate for candidate in candidates if candidate in available
                ],
                "available": any(candidate in available for candidate in candidates),
            }
            for name, candidates in variable_candidates.items()
        }
        variables["treatment_capacity"]["note"] = (
            "No installed kg/day treatment-capacity column is present in the "
            "state-year analysis table. The management-indicator sheet reports "
            "national facility counts, which are not treatment capacity."
        )
        variables["government_hospital_beds_only"]["note"] = (
            "This is government-hospital bed count only; it is not a measure "
            "of all hospital beds."
        )

        report: dict[str, Any] = {
            "workbook": str(workbook_path.relative_to(PROJECT_ROOT))
            if workbook_path.is_relative_to(PROJECT_ROOT)
            else str(workbook_path),
            "sheet_names": workbook.sheetnames,
            "sheets": sheets,
            "analysis_sheet": PRIMARY_SHEET,
            "prediction_target": "BMW_Generated_kg_per_day_as_reported",
            "prediction_target_unit": "kg/day",
            "identified_variables": variables,
            "workbook_quality_notes": [
                "The workbook's Data Quality and Missing Values sheet says the "
                "main panel is intended to contain 216 state-year rows for "
                "2018-2023 and that blanks represent missing values, not zero.",
                "That sheet also says state-level extraction is not fully "
                "audited; results must not be presented as fully verified.",
                "Historical geography is combined where the source reports "
                "combined territories.",
            ],
        }
    finally:
        workbook.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "inspection_report.json"
    text_path = output_dir / "inspection_report.txt"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=_json_value),
        encoding="utf-8",
    )
    text_path.write_text(_render_report(report), encoding="utf-8")
    print(f"Inspection JSON: {json_path}")
    print(f"Inspection report: {text_path}")
    print(f"Analysis sheet: {PRIMARY_SHEET}")
    print(f"Target: {report['prediction_target']} ({report['prediction_target_unit']})")
    print(f"Rows: {primary['record_count']}; columns: {len(columns)}")
    print(f"Duplicate records: {primary['duplicate_records']}")
    return report


def _render_report(report: dict[str, Any]) -> str:
    lines = [
        "BIOMEDICAL WASTE INTELLIGENCE — DATASET INSPECTION",
        f"Workbook: {report['workbook']}",
        "",
        "SHEETS",
    ]
    for name in report["sheet_names"]:
        summary = report["sheets"][name]
        lines.append(
            f"- {name}: dimensions {summary['dimensions'][0]} x "
            f"{summary['dimensions'][1]}, {summary['record_count']} non-empty "
            f"records, {summary['duplicate_records']} duplicate records"
        )
        lines.append(f"  Columns: {', '.join(summary['columns'])}")
        lines.append(
            "  Missing values: "
            + (
                "; ".join(
                    f"{column}={count}"
                    for column, count in summary["missing_by_column"].items()
                )
                or "none"
            )
        )
        if summary["numeric_summary"]:
            lines.append("  Numeric summary (count, mean, median, min, max):")
            for column, values in summary["numeric_summary"].items():
                lines.append(
                    f"    {column}: {values['count']}, {values['mean']:.4g}, "
                    f"{values['median']:.4g}, {values['min']:.4g}, "
                    f"{values['max']:.4g}"
                )

    lines.extend(
        [
            "",
            f"SELECTED ANALYSIS SHEET: {report['analysis_sheet']}",
            f"PREDICTION TARGET: {report['prediction_target']} "
            f"({report['prediction_target_unit']})",
            "IDENTIFIED VARIABLES",
        ]
    )
    for name, value in report["identified_variables"].items():
        columns = ", ".join(value["available_columns"]) or "not available"
        lines.append(f"- {name}: {columns}. {value.get('note', '')}".rstrip())
    lines.extend(["", "WORKBOOK QUALITY NOTES"])
    lines.extend(f"- {note}" for note in report["workbook_quality_notes"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    inspect_workbook()