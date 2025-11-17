import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import yaml


class DQConfigError(Exception):
    """Raised for issues with configuration loading or parsing."""


def load_rules(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise DQConfigError(f"Config file not found: {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise DQConfigError(f"Invalid YAML in config: {exc}") from exc

    required_keys = [
        "expected_columns",
        "column_types",
        "value_ranges",
        "missing_value_policy",
        "categorical_values",
        "uniqueness",
    ]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise DQConfigError(f"Missing keys in config: {', '.join(missing_keys)}")
    return config


def _read_dataset(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    return pd.read_csv(dataset_path, dtype=str)


def _detect_missing(series: pd.Series) -> pd.Series:
    series = series.copy()
    missing_mask = series.isna()
    try:
        missing_mask |= series.str.strip().eq("")
    except AttributeError:
        # Non-string dtype fallback
        missing_mask |= series.isna()
    return missing_mask


def validate_dataset(
    dataset_path: Path, rules: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    df = _read_dataset(dataset_path)
    expected_columns = rules.get("expected_columns", [])
    column_types = rules.get("column_types", {})
    value_ranges = rules.get("value_ranges", {})
    allow_missing = rules.get("missing_value_policy", {}).get("allow_missing", True)
    categorical_values = rules.get("categorical_values", {})
    uniqueness = rules.get("uniqueness", [])

    actual_columns = list(df.columns)
    missing_columns = [col for col in expected_columns if col not in actual_columns]
    unexpected_columns = [col for col in actual_columns if col not in expected_columns]

    type_errors: List[Dict[str, Any]] = []
    range_errors: List[Dict[str, Any]] = []
    missing_values: List[Dict[str, Any]] = []
    categorical_errors: List[Dict[str, Any]] = []
    uniqueness_errors: List[Dict[str, Any]] = []

    for col, expected_type in column_types.items():
        if col not in df.columns:
            continue

        series = df[col]
        missing_mask = _detect_missing(series)

        # Handle type checks
        if expected_type in ("int", "float"):
            numeric_series = pd.to_numeric(series, errors="coerce")
            type_error_mask = (~missing_mask) & numeric_series.isna()
            if expected_type == "int":
                non_integer_mask = (~missing_mask) & (~type_error_mask) & (
                    (numeric_series % 1) != 0
                )
                type_error_mask |= non_integer_mask
            error_indices = numeric_series.index[type_error_mask].tolist()
            for idx in error_indices:
                type_errors.append(
                    {
                        "row": int(idx),
                        "column": col,
                        "value": series.iloc[idx],
                        "expected": expected_type,
                    }
                )

            # Range checks
            if col in value_ranges and not type_error_mask.all():
                min_val, max_val = value_ranges[col]
                valid_mask = (~missing_mask) & (~type_error_mask)
                below_min = valid_mask & (numeric_series < min_val)
                above_max = valid_mask & (numeric_series > max_val)
                violating_mask = below_min | above_max
                violating_indices = numeric_series.index[violating_mask].tolist()
                for idx in violating_indices:
                    range_errors.append(
                        {
                            "row": int(idx),
                            "column": col,
                            "value": series.iloc[idx],
                            "expected_range": [min_val, max_val],
                        }
                    )
        else:
            # Generic type check: ensure non-missing values are strings
            non_str_mask = (~missing_mask) & (~series.apply(lambda v: isinstance(v, str)))
            for idx in series.index[non_str_mask].tolist():
                type_errors.append(
                    {
                        "row": int(idx),
                        "column": col,
                        "value": series.iloc[idx],
                        "expected": "string",
                    }
                )

        # Missing value policy
        if not allow_missing:
            missing_indices = series.index[missing_mask].tolist()
            for idx in missing_indices:
                missing_values.append({"row": int(idx), "column": col})

        # Categorical checks
        if col in categorical_values:
            allowed_raw = categorical_values[col]
            allowed_values = {str(v) for v in allowed_raw}
            valid_mask = (~missing_mask)
            invalid_mask = valid_mask & (~series.astype(str).isin(allowed_values))
            invalid_indices = series.index[invalid_mask].tolist()
            for idx in invalid_indices:
                categorical_errors.append(
                    {
                        "row": int(idx),
                        "column": col,
                        "value": series.iloc[idx],
                        "allowed": allowed_raw,
                    }
                )

    # Uniqueness checks
    for unique_cols in uniqueness:
        if isinstance(unique_cols, str):
            unique_cols = [unique_cols]
        missing_unique_cols = [c for c in unique_cols if c not in df.columns]
        if missing_unique_cols:
            continue
        dup_mask = df.duplicated(subset=unique_cols, keep=False)
        dup_indices = df.index[dup_mask].tolist()
        for idx in dup_indices:
            uniqueness_errors.append(
                {"row": int(idx), "columns": list(unique_cols)}
            )

    status = not any(
        [
            missing_columns,
            unexpected_columns,
            type_errors,
            range_errors,
            missing_values,
            categorical_errors,
            uniqueness_errors,
        ]
    )

    report = {
        "status": "pass" if status else "fail",
        "stats": {
            "rows": len(df),
            "columns": len(df.columns),
            "violation_counts": {
                "missing_columns": len(missing_columns),
                "unexpected_columns": len(unexpected_columns),
                "type_violations": len(type_errors),
                "range_violations": len(range_errors),
                "missing_values": len(missing_values),
                "categorical_violations": len(categorical_errors),
                "uniqueness_violations": len(uniqueness_errors),
            },
        },
        "violations": {
            "missing_columns": missing_columns,
            "unexpected_columns": unexpected_columns,
            "type_errors": type_errors,
            "range_errors": range_errors,
            "missing_values": missing_values,
            "categorical_errors": categorical_errors,
            "uniqueness_errors": uniqueness_errors,
        },
    }
    return report, status


def generate_text_report(report: Dict[str, Any]) -> str:
    stats = report.get("stats", {})
    counts = stats.get("violation_counts", {})
    lines = [
        "Data Quality Report",
        "===================",
        f"Rows: {stats.get('rows', 0)}",
        f"Columns: {stats.get('columns', 0)}",
        "",
        f"Missing Columns: {counts.get('missing_columns', 0)}",
        f"Unexpected Columns: {counts.get('unexpected_columns', 0)}",
        f"Type Violations: {counts.get('type_violations', 0)}",
        f"Range Violations: {counts.get('range_violations', 0)}",
        f"Missing Values: {counts.get('missing_values', 0)}",
        f"Categorical Violations: {counts.get('categorical_violations', 0)}",
        f"Uniqueness Violations: {counts.get('uniqueness_violations', 0)}",
        "",
        f"STATUS: {report.get('status', '').upper()}",
    ]
    return "\n".join(lines)


def write_reports(report: Dict[str, Any], report_dir: Path) -> Tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    text_path = report_dir / f"report_{timestamp}.txt"
    json_path = report_dir / f"report_{timestamp}.json"

    text_path.write_text(generate_text_report(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return text_path, json_path


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Data Quality CLI for OfferRanker datasets",
        usage="python dq_cli.py validate path/to/dataset.csv --config dq_rules.yaml",
    )
    subparsers = parser.add_subparsers(dest="command")
    validate_parser = subparsers.add_parser("validate", help="Validate a CSV dataset")
    validate_parser.add_argument("dataset_path", type=str, help="Path to dataset CSV")
    validate_parser.add_argument(
        "--config",
        type=str,
        default="dq_rules.yaml",
        help="Path to YAML rules file",
    )
    validate_parser.add_argument(
        "--report-dir",
        type=str,
        default="dq/reports",
        help="Directory to write reports",
    )
    validate_parser.add_argument(
        "--format",
        type=str,
        choices=["json", "text"],
        default="text",
        help="Format to print to stdout (files are always both json and text)",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if args.command != "validate":
        return 2

    dataset_path = Path(args.dataset_path)
    config_path = Path(args.config)
    report_dir = Path(args.report_dir)

    try:
        rules = load_rules(config_path)
    except (DQConfigError, FileNotFoundError) as exc:
        sys.stderr.write(f"[config error] {exc}\n")
        return 2

    try:
        report, status = validate_dataset(dataset_path, rules)
    except FileNotFoundError as exc:
        sys.stderr.write(f"[file error] {exc}\n")
        return 2
    except Exception as exc:  # unexpected validation errors
        sys.stderr.write(f"[validation error] {exc}\n")
        return 1

    text_path, json_path = write_reports(report, report_dir)

    # Print chosen format to stdout for CLI visibility
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(generate_text_report(report))
    print(f"Reports written to: {text_path} and {json_path}")

    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
