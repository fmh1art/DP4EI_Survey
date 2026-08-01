#!/usr/bin/env python3
"""Run and archive reproducible DBLP/arXiv searches for the DP4EI survey.

The script deliberately performs discovery only. Inclusion decisions are made in
the review protocol and recorded separately so that search results are not
silently equated with evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path


DBLP_QUERIES = [
    "robot data curation",
    "robot demonstration selection",
    "robot data quality",
    "robot data filtering",
    "robot data mixing",
    "robot trajectory annotation segmentation",
    "robot instruction relabeling",
    "robot demonstration augmentation",
    "robot synthetic demonstration generation",
    "robot world model data generation",
    "robot self improvement data",
    "robot online post training",
    "robot autonomous data collection",
    "cross embodiment action alignment",
    "vision language action data engine",
    "embodied data preparation",
]

ARXIV_QUERIES = [
    'cat:cs.RO AND all:"data curation"',
    'cat:cs.RO AND all:"demonstration selection"',
    'cat:cs.RO AND all:"data quality"',
    'cat:cs.RO AND all:"data filtering"',
    'cat:cs.RO AND all:"data mixing"',
    'cat:cs.RO AND (all:"automatic annotation" OR all:relabeling OR all:segmentation)',
    'cat:cs.RO AND (all:"data augmentation" OR all:"synthetic demonstrations")',
    'cat:cs.RO AND (all:"world model" AND all:"data generation")',
    'cat:cs.RO AND (all:"self-improvement" OR all:"online post-training")',
    'cat:cs.RO AND all:"autonomous data collection"',
    'cat:cs.RO AND (all:"cross-embodiment" OR all:"action alignment")',
    'cat:cs.RO AND all:"data engine"',
]

USER_AGENT = "DP4EI-literature-audit/1.0 (reproducible academic search)"


@dataclass
class Record:
    source: str
    source_id: str
    title: str
    authors: str
    year: str
    venue: str
    doi: str
    url: str
    query: str


def slug(text: str, limit: int = 72) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value[:limit] or "query"


def norm_title(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


def request_bytes(url: str, retries: int = 2, timeout: int = 45) -> bytes:
    """Fetch through curl, which respects the proxy configuration on our runner."""
    # Retry at the process level.  Curl's built-in retry can concatenate a
    # truncated response with the next XML response when stdout is captured,
    # producing a syntactically invalid archive even though the retry succeeds.
    last_error = ""
    for attempt in range(retries + 1):
        completed = subprocess.run(
            [
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                str(timeout),
                "--user-agent",
                USER_AGENT,
                url,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode == 0:
            return completed.stdout
        last_error = completed.stderr.decode("utf-8", errors="replace").strip()
        if attempt < retries:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(last_error)


def listify(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def search_dblp(query: str, limit: int) -> tuple[int, list[Record], dict]:
    params = urllib.parse.urlencode({"q": query, "h": limit, "format": "json"})
    payload = json.loads(request_bytes(f"https://dblp.org/search/publ/api?{params}"))
    result = payload.get("result", {})
    hits_obj = result.get("hits", {})
    total = int(hits_obj.get("@total", 0))
    records: list[Record] = []
    for hit in listify(hits_obj.get("hit")):
        info = hit.get("info", {})
        author_obj = info.get("authors", {}).get("author", [])
        authors = []
        for author in listify(author_obj):
            authors.append(author.get("text", "") if isinstance(author, dict) else str(author))
        records.append(
            Record(
                source="DBLP",
                source_id=str(hit.get("@id", "")),
                title=re.sub(r"<[^>]+>", "", info.get("title", "")).rstrip("."),
                authors="; ".join(a for a in authors if a),
                year=str(info.get("year", "")),
                venue=str(info.get("venue", "")),
                doi=str(info.get("doi", "")),
                url=str(info.get("ee") or info.get("url") or ""),
                query=query,
            )
        )
    return total, records, payload


def atom_text(node: ET.Element, name: str, ns: dict[str, str]) -> str:
    child = node.find(name, ns)
    return "" if child is None or child.text is None else " ".join(child.text.split())


def search_arxiv(query: str, limit: int) -> tuple[int, list[Record], bytes]:
    params = urllib.parse.urlencode(
        {"search_query": query, "start": 0, "max_results": limit, "sortBy": "submittedDate", "sortOrder": "descending"}
    )
    raw = request_bytes(f"https://export.arxiv.org/api/query?{params}")
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
    total = int(atom_text(root, "o:totalResults", ns) or 0)
    records: list[Record] = []
    for entry in root.findall("a:entry", ns):
        identifier = atom_text(entry, "a:id", ns)
        authors = [atom_text(a, "a:name", ns) for a in entry.findall("a:author", ns)]
        published = atom_text(entry, "a:published", ns)
        records.append(
            Record(
                source="arXiv",
                source_id=identifier.rsplit("/", 1)[-1],
                title=atom_text(entry, "a:title", ns),
                authors="; ".join(authors),
                year=published[:4],
                venue="arXiv",
                doi="",
                url=identifier,
                query=query,
            )
        )
    return total, records, raw


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--source", choices=("all", "dblp", "arxiv"), default="all")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--sleep", type=float, default=3.2)
    parser.add_argument("--year-start", type=int, default=2018)
    parser.add_argument("--year-end", type=int, default=2026)
    parser.add_argument(
        "--query-indexes",
        help="optional comma-separated 1-based query indexes for targeted retries",
    )
    parser.add_argument("--tag", help="optional filename suffix, e.g. retry")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    selected_indexes = None
    if args.query_indexes:
        selected_indexes = {int(value) for value in args.query_indexes.split(",")}

    summaries: list[dict] = []
    all_records: list[Record] = []
    sources = []
    if args.source in ("all", "dblp"):
        sources.append(("DBLP", DBLP_QUERIES))
    if args.source in ("all", "arxiv"):
        sources.append(("arXiv", ARXIV_QUERIES))

    for source, queries in sources:
        raw_dir = args.out_dir / "raw" / source.lower()
        raw_dir.mkdir(parents=True, exist_ok=True)
        selected = [
            (index, query)
            for index, query in enumerate(queries, 1)
            if selected_indexes is None or index in selected_indexes
        ]
        for position, (index, query) in enumerate(selected, 1):
            print(f"[{source} {position:02d}/{len(selected):02d}; query {index:02d}] {query}", flush=True)
            error = ""
            try:
                if source == "DBLP":
                    total, records, raw = search_dblp(query, args.limit)
                    (raw_dir / f"{index:02d}_{slug(query)}.json").write_text(
                        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                else:
                    total, records, raw = search_arxiv(query, args.limit)
                    (raw_dir / f"{index:02d}_{slug(query)}.xml").write_bytes(raw)
            except Exception as exc:
                total, records = 0, []
                error = f"{type(exc).__name__}: {exc}"
                print(f"  warning: {error}", flush=True)
            kept = [r for r in records if r.year.isdigit() and args.year_start <= int(r.year) <= args.year_end]
            all_records.extend(kept)
            summaries.append(
                {
                    "source": source,
                    "query": query,
                    "reported_total": total,
                    "retrieved": len(records),
                    "within_year_range": len(kept),
                    "error": error,
                }
            )
            time.sleep(args.sleep)

    dedup: dict[str, Record] = {}
    query_sets: dict[str, set[str]] = {}
    for record in all_records:
        key = norm_title(record.title)
        if not key:
            continue
        query_sets.setdefault(key, set()).add(record.query)
        if key not in dedup or (dedup[key].source == "arXiv" and record.source == "DBLP"):
            dedup[key] = record

    record_fields = list(Record.__dataclass_fields__) + ["matched_queries"]
    rows = []
    for key, record in sorted(dedup.items(), key=lambda item: (item[1].year, item[1].title), reverse=True):
        row = asdict(record)
        row["matched_queries"] = " || ".join(sorted(query_sets[key]))
        rows.append(row)
    suffix = "" if args.source == "all" else f"_{args.source}"
    if args.tag:
        suffix += f"_{slug(args.tag)}"
    write_csv(args.out_dir / f"discovery_records{suffix}.csv", rows, record_fields)
    write_csv(
        args.out_dir / f"search_summary{suffix}.csv",
        summaries,
        ["source", "query", "reported_total", "retrieved", "within_year_range", "error"],
    )
    print(json.dumps({"queries": len(summaries), "retrieved_rows": len(all_records), "deduplicated_titles": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
