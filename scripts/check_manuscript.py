#!/usr/bin/env python3
"""Static consistency checks for the active survey manuscript."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def active_tex(path: Path, seen: set[Path]) -> list[Path]:
    path = path.resolve()
    if path in seen:
        return []
    if not path.exists():
        raise SystemExit(f"missing input: {path.relative_to(ROOT)}")
    seen.add(path)
    text = path.read_text(encoding="utf-8")
    files = [path]
    for name in re.findall(r"\\input\{([^}]+)\}", text):
        child = ROOT / (name if name.endswith(".tex") else name + ".tex")
        files.extend(active_tex(child, seen))
    return files


def main() -> None:
    files = active_tex(ROOT / "main.tex", set())
    content = "\n".join(path.read_text(encoding="utf-8") for path in files)

    cite_groups = re.findall(
        r"\\cite[a-zA-Z*]*\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]+)\}", content
    )
    cited = {key.strip() for group in cite_groups for key in group.split(",") if key.strip()}
    bibliography_files = sorted((ROOT / "citations").glob("survey_*.bib"))
    bib_text = "\n".join(path.read_text(encoding="utf-8") for path in bibliography_files)
    bib_keys = re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib_text)
    duplicates = sorted(key for key, count in Counter(bib_keys).items() if count > 1)
    missing_citations = sorted(cited - set(bib_keys))

    local_pdf_names = [path.name for path in (ROOT / "_pdfs" / "papers").rglob("*.pdf")]
    cited_arxiv_ids = {}
    for key in cited:
        match = re.search(r"_(\d{4})_(\d{5})$", key)
        if match:
            cited_arxiv_ids[key] = f"{match.group(1)}.{match.group(2)}"
    missing_primary_text = sorted(
        f"{key} ({arxiv_id})"
        for key, arxiv_id in cited_arxiv_ids.items()
        if not any(arxiv_id in name for name in local_pdf_names)
    )

    labels = re.findall(r"\\label\{([^}]+)\}", content)
    refs = set(re.findall(r"\\(?:ref|eqref|autoref|pageref)\{([^}]+)\}", content))
    duplicate_labels = sorted(key for key, count in Counter(labels).items() if count > 1)
    missing_labels = sorted(refs - set(labels))

    placeholders = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b(?:TODO|FIXME|TBD)\b|\\reminder\{|\\fmh\{|\\jie\{|\\peng\{", line):
                placeholders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

    errors = []
    if duplicates:
        errors.append(f"duplicate BibTeX keys: {', '.join(duplicates)}")
    if missing_citations:
        errors.append(f"undefined citations: {', '.join(missing_citations)}")
    if missing_primary_text:
        errors.append(f"cited works without a local primary PDF: {', '.join(missing_primary_text)}")
    if duplicate_labels:
        errors.append(f"duplicate labels: {', '.join(duplicate_labels)}")
    if missing_labels:
        errors.append(f"undefined references: {', '.join(missing_labels)}")
    if placeholders:
        errors.append("active placeholders:\n  " + "\n  ".join(placeholders))

    plain = re.sub(r"%.*", "", content)
    plain = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", plain)
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", plain)
    print(
        f"checked {len(files)} active TeX files; {len(words)} approximate words; "
        f"{len(cited)} cited works ({len(cited_arxiv_ids)} locally archived); {len(labels)} labels"
    )
    if errors:
        raise SystemExit("\n".join(errors))
    print("manuscript consistency checks passed")


if __name__ == "__main__":
    main()
