#!/usr/bin/env python3
"""Aggregate multiple coverage XML reports and enforce a global threshold.

Supports both Python (Cobertura format) and JavaScript (LCOV/Vitest format) coverage reports.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_cobertura_report(path: Path) -> tuple[int, int]:
    """Parse a Cobertura-format XML coverage report (Python/pytest-cov)."""
    tree = ET.parse(path)
    root = tree.getroot()

    lines_valid = int(root.attrib.get("lines-valid") or root.attrib.get("lines_valid", 0))
    lines_covered = int(root.attrib.get("lines-covered") or root.attrib.get("lines_covered", 0))
    return lines_valid, lines_covered


def parse_vitest_json_report(path: Path) -> tuple[int, int]:
    """Parse a Vitest/V8 JSON coverage summary."""
    with open(path) as f:
        data = json.load(f)
    
    # Vitest coverage-v8 format
    if "total" in data:
        total = data["total"]
        lines_valid = total.get("lines", {}).get("total", 0)
        lines_covered = total.get("lines", {}).get("covered", 0)
        return lines_valid, lines_covered
    
    # Alternative format (coverage-summary.json)
    lines_valid = 0
    lines_covered = 0
    for file_data in data.values():
        if isinstance(file_data, dict) and "lines" in file_data:
            lines_valid += file_data["lines"].get("total", 0)
            lines_covered += file_data["lines"].get("covered", 0)
    
    return lines_valid, lines_covered


def parse_lcov_report(path: Path) -> tuple[int, int]:
    """Parse an LCOV-format coverage report."""
    lines_valid = 0
    lines_covered = 0
    
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LF:"):
                lines_valid += int(line[3:])
            elif line.startswith("LH:"):
                lines_covered += int(line[3:])
    
    return lines_valid, lines_covered


def parse_report(path: Path) -> tuple[int, int]:
    """Parse a coverage report, auto-detecting format."""
    if not path.exists():
        print(f"Warning: Coverage report not found: {path}", file=sys.stderr)
        return 0, 0

    suffix = path.suffix.lower()
    name = path.name.lower()
    
    # Try to detect format
    if suffix == ".xml":
        return parse_cobertura_report(path)
    elif suffix == ".json":
        return parse_vitest_json_report(path)
    elif suffix == ".info" or name == "lcov.info":
        return parse_lcov_report(path)
    else:
        # Try XML first (most common)
        try:
            return parse_cobertura_report(path)
        except Exception:
            pass
        
        # Try JSON
        try:
            return parse_vitest_json_report(path)
        except Exception:
            pass
        
        # Try LCOV
        try:
            return parse_lcov_report(path)
        except Exception:
            pass
    
    print(f"Warning: Could not parse coverage report: {path}", file=sys.stderr)
    return 0, 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "reports",
        nargs="+",
        type=Path,
        help="Paths to coverage reports to combine (XML, JSON, or LCOV format).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum combined coverage ratio (0-1). Default: 0.5 (50%%).",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Ignore missing report files instead of failing.",
    )
    args = parser.parse_args()

    total_lines = 0
    total_covered = 0
    reports_found = 0
    
    for report in args.reports:
        if not report.exists():
            if args.ignore_missing:
                print(f"Skipping missing report: {report}")
                continue
            else:
                print(f"ERROR: Coverage report not found: {report}", file=sys.stderr)
                sys.exit(1)
        
        lines_valid, lines_covered = parse_report(report)
        
        if lines_valid > 0:
            pct = (lines_covered / lines_valid) * 100
            print(f"{report}: {lines_covered}/{lines_valid} lines covered ({pct:.2f}%)")
            total_lines += lines_valid
            total_covered += lines_covered
            reports_found += 1
        else:
            print(f"{report}: No coverage data found")

    if total_lines == 0:
        print("No lines found across coverage reports.", file=sys.stderr)
        sys.exit(1)

    combined_ratio = total_covered / total_lines
    combined_pct = combined_ratio * 100
    threshold_pct = args.threshold * 100

    print("\n==============================================")
    print("             FINAL COVERAGE REPORT            ")
    print("==============================================")
    print(f"Reports processed : {reports_found}")
    print(f"Total lines       : {total_lines}")
    print(f"Lines covered     : {total_covered}")
    print(f"Combined coverage : {combined_pct:.2f}%")
    print(f"Required minimum  : {threshold_pct:.0f}%")

    if combined_ratio < args.threshold:
        print("----------------------------------------------")
        print(
            f"RESULT: ❌ FAIL – coverage {combined_pct:.2f}% "
            f"is below required {threshold_pct:.0f}%.",
            file=sys.stderr,
        )
        print("==============================================")
        sys.exit(1)
    else:
        print("----------------------------------------------")
        print(f"RESULT: ✅ PASS – coverage threshold met.")
        print("==============================================")



if __name__ == "__main__":
    main()
