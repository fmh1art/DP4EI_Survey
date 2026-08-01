#!/usr/bin/env python3
"""Fetch verified arXiv metadata and emit deterministic BibTeX entries.

The script is intentionally small and dependency-free.  It is used to build the
survey bibliography from arXiv's Atom API instead of copying unverified citation
strings from secondary pages.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def fetch(ids: list[str]) -> bytes:
    query = urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    result = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--max-time",
            "60",
            "--retry",
            "2",
            "--retry-delay",
            "3",
            f"https://export.arxiv.org/api/query?{query}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def text(node: ET.Element, path: str) -> str:
    child = node.find(path, NS)
    if child is None or child.text is None:
        return ""
    return " ".join(html.unescape(child.text).split())


def tex(value: str) -> str:
    """Escape characters that commonly break BibTeX while retaining math."""
    value = value.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    # arXiv titles commonly place pi symbols inside an existing math span.
    return value.replace("π", r"\pi")


def key_for(entry: ET.Element, arxiv_id: str) -> str:
    first_author = entry.find("atom:author/atom:name", NS)
    surname = "paper"
    if first_author is not None and first_author.text:
        surname = re.sub(r"[^A-Za-z]", "", first_author.text.split()[-1]).lower()
    year = text(entry, "atom:published")[:4]
    title_words = re.findall(r"[A-Za-z0-9]+", text(entry, "atom:title"))
    stop = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "to", "via", "with"}
    token = next((word.lower() for word in title_words if word.lower() not in stop), "paper")
    return f"{surname}{year}{token}_{arxiv_id.replace('.', '_')}"


def entry_to_bib(entry: ET.Element) -> tuple[str, str]:
    arxiv_id = text(entry, "atom:id").rsplit("/", 1)[-1].split("v", 1)[0]
    key = key_for(entry, arxiv_id)
    authors = []
    for author in entry.findall("atom:author", NS):
        name = text(author, "atom:name")
        if name:
            authors.append(name)
    title = tex(text(entry, "atom:title"))
    year = text(entry, "atom:published")[:4]
    doi = text(entry, "arxiv:doi")
    journal_ref = tex(text(entry, "arxiv:journal_ref"))
    primary_node = entry.find("arxiv:primary_category", NS)
    primary_class = "" if primary_node is None else primary_node.attrib.get("term", "")
    fields = [
        f"  author = {{{' and '.join(tex(author) for author in authors)}}}",
        f"  title = {{{{{title}}}}}",
        f"  year = {{{year}}}",
        f"  eprint = {{{arxiv_id}}}",
        "  archivePrefix = {arXiv}",
        f"  primaryClass = {{{primary_class}}}",
        f"  url = {{https://arxiv.org/abs/{arxiv_id}}}",
    ]
    if journal_ref:
        fields.insert(3, f"  journal = {{{journal_ref}}}")
    if doi:
        fields.insert(3, f"  doi = {{{doi}}}")
    return key, "@article{" + key + ",\n" + ",\n".join(fields) + "\n}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    entries: dict[str, str] = {}
    for offset in range(0, len(args.ids), args.batch_size):
        batch = args.ids[offset : offset + args.batch_size]
        root = ET.fromstring(fetch(batch))
        for entry in root.findall("atom:entry", NS):
            key, bib = entry_to_bib(entry)
            entries[key] = bib
        if offset + args.batch_size < len(args.ids):
            time.sleep(3.2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(entries[key] for key in sorted(entries)) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} verified entries to {args.output}")


if __name__ == "__main__":
    main()
