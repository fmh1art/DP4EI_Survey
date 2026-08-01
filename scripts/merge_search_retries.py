#!/usr/bin/env python3
"""Resolve archived query failures without erasing the initial search record."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    return re.sub(r"[^a-z0-9]+", "", value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    base_summary = read_rows(args.run_dir / "search_summary.csv")
    retry_summaries = []
    for path in sorted(args.run_dir.glob("search_summary_*_retry.csv")):
        retry_summaries.extend(read_rows(path))
    retry_by_query = {(row["source"], row["query"]): row for row in retry_summaries}

    resolved_summary = []
    for initial in base_summary:
        initial_error = initial["error"]
        final = dict(initial)
        resolution = "initial_succeeded"
        if initial_error:
            retry = retry_by_query.get((initial["source"], initial["query"]))
            if retry is None:
                resolution = "unretried_error"
            else:
                final = dict(retry)
                resolution = "retry_succeeded" if not retry["error"] else "retry_failed"
        final["initial_error"] = initial_error
        final["resolution"] = resolution
        resolved_summary.append(final)

    summary_fields = [
        "source", "query", "reported_total", "retrieved", "within_year_range",
        "error", "initial_error", "resolution",
    ]
    write_rows(args.run_dir / "search_summary_resolved.csv", resolved_summary, summary_fields)

    discovery_paths = [args.run_dir / "discovery_records.csv"]
    discovery_paths.extend(sorted(args.run_dir.glob("discovery_records_*_retry.csv")))
    merged: dict[str, dict[str, str]] = {}
    matched: dict[str, set[str]] = {}
    for path in discovery_paths:
        for row in read_rows(path):
            key = normalize_title(row["title"])
            if not key:
                continue
            matched.setdefault(key, set()).update(
                value for value in row["matched_queries"].split(" || ") if value
            )
            incumbent = merged.get(key)
            if incumbent is None or (incumbent["source"] == "arXiv" and row["source"] == "DBLP"):
                merged[key] = dict(row)

    discovery_fields = list(read_rows(discovery_paths[0])[0].keys())
    resolved_records = []
    for key, row in sorted(
        merged.items(), key=lambda item: (item[1]["year"], item[1]["title"]), reverse=True
    ):
        row["matched_queries"] = " || ".join(sorted(matched[key]))
        resolved_records.append(row)
    write_rows(args.run_dir / "discovery_records_resolved.csv", resolved_records, discovery_fields)

    final_errors = sum(bool(row["error"]) for row in resolved_summary)
    recovered = sum(row["resolution"] == "retry_succeeded" for row in resolved_summary)
    print(
        f"resolved {len(resolved_summary)} queries; recovered {recovered} transient failures; "
        f"remaining errors {final_errors}; {len(resolved_records)} deduplicated discovery records"
    )


if __name__ == "__main__":
    main()
