#!/usr/bin/env python3
"""Validate archived PDFs and rebuild their machine-readable manifests."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF_ROOT = ROOT / "_pdfs" / "papers"
MANIFEST = ROOT / "_pdfs" / "manifests"
NOTES = MANIFEST / "evidence_map.csv"

SURVEYS = {
    "2607.24744": ("SUP01", "Data Pyramid for Embodied Manipulation"),
    "2604.23001": ("SUP02", "Vision-Language-Action in Robotics: A Survey of Datasets, Benchmarks, and Data Engines"),
    "2604.27621": ("SUP03", "Robot Learning from Human Videos: A Survey"),
}
TITLE_OVERRIDES = {
    "P204a": "DataComp: In Search of the Next Generation of Multimodal Datasets",
    "P204b": "Data Curation via Joint Example Selection Further Accelerates Multimodal Learning",
}


def pdf_pages(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True
    )
    if result.returncode:
        raise RuntimeError(f"invalid PDF {path}: {result.stderr.strip()}")
    match = re.search(r"^Pages:\s+(\d+)", result.stdout, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"page count missing for {path}")
    return int(match.group(1))


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    with NOTES.open(encoding="utf-8-sig", newline="") as handle:
        note_rows = list(csv.DictReader(handle))
    titles = {row["note_id"]: row["title"] for row in note_rows}

    rows = []
    included_ids: set[str] = set()
    checksum_lines = []
    for path in sorted(PDF_ROOT.rglob("*.pdf")):
        arxiv_match = re.search(r"(\d{4}\.\d{5})", path.name)
        if not arxiv_match:
            raise RuntimeError(f"arXiv ID missing from filename: {path}")
        arxiv_id = arxiv_match.group(1)
        prefix = re.match(r"(P\d{3}[a-z]?)_", path.name)
        if arxiv_id in SURVEYS:
            note_id, title = SURVEYS[arxiv_id]
        elif prefix:
            note_id = prefix.group(1)
            title = TITLE_OVERRIDES.get(note_id, titles.get(note_id, ""))
            included_ids.add(note_id[:4])
        else:
            raise RuntimeError(f"note ID missing from filename: {path}")
        if not title:
            raise RuntimeError(f"title not found for {note_id}: {path}")
        sha = digest(path)
        rel = path.relative_to(PDF_ROOT)
        rows.append(
            {
                "note_id": note_id,
                "title": title,
                "arxiv_id": arxiv_id,
                "category": rel.parent.as_posix(),
                "filename": path.name,
                "pages": str(pdf_pages(path)),
                "size_mb": f"{path.stat().st_size / (1024 * 1024):.2f}",
                "sha256": sha,
                "source_url": f"https://arxiv.org/abs/{arxiv_id}",
            }
        )
        checksum_lines.append(f"{sha}  papers/{rel.as_posix()}")

    fields = ["note_id", "title", "arxiv_id", "category", "filename", "pages", "size_mb", "sha256", "source_url"]
    write_csv(MANIFEST / "included_pdfs.csv", fields, rows)

    for row in note_rows:
        row["pdf_included"] = "yes" if row["note_id"] in included_ids else "no"
    note_fields = ["note_id", "title", "year", "depth", "pdf_included"]
    write_csv(NOTES, note_fields, note_rows)
    write_csv(
        MANIFEST / "not_bundled_in_this_pass.csv",
        note_fields,
        [row for row in note_rows if row["pdf_included"] == "no"],
    )
    (MANIFEST / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"validated and indexed {len(rows)} PDFs; {len(included_ids)} note records have local primary text")


if __name__ == "__main__":
    main()
