# Data Preparation for Embodied Intelligence Survey

This repository preserves the original ACM-style conference template and uses it
for the survey **“From Raw Records to Continually Updated Training Data: Data
Preparation for Embodied Intelligence.”** The active manuscript is written in
English; the source survey and structured paper notes remain available in Chinese.

## Dependency and citation flow

```text
main.tex
├── _authors.tex, _commands.tex, _notations.tex
├── secs/00abstract.tex
├── secs/01introduction.tex ... secs/09conclusion.tex
│   ├── tables/*.tex
│   └── figures/tex/*.tex
├── citations/survey_ref.bib, citations/survey_extra.bib,
│   citations/survey_industry.bib
└── appendix/survey_protocol.tex
    └── appendix/evidence_map.tex  (generated from the 211-work CSV)
```

`\cite{key}` in a section resolves to an entry in one of the three active
`citations/survey_*.bib` databases; `\label{...}` and `\ref{...}` connect sections,
figures, tables, equations, and appendices. Run
`python3 scripts/check_manuscript.py` to detect missing citation keys or local
primary PDFs, duplicate or missing labels, and active TODO markers.

## Folder guide and sample formats

| Path | What belongs here | Active sample |
|---|---|---|
| `secs/` | One logical manuscript section per `.tex` file. Start with `%!TEX root = ../main.tex`, add a stable `\label`, and cite only verified BibTeX keys. | `secs/05semantic_curation.tex` |
| `tables/` | Reusable table environments. The section imports the whole table with `\input{tables/name}`; captions and labels live in the table file. | `tables/curation_comparison.tex` |
| `figures/tex/` | Editable TikZ figures. The file contains the complete `figure`/`figure*` environment and is imported with `\input`. | `figures/tex/data_prep_lifecycle.tex` |
| `figures/fig/` | Binary figure assets. The retained PDF demonstrates the expected asset format but is not imported by the survey. | `figures/fig/sample_figure.pdf` |
| `citations/` | Active BibTeX databases. Citation keys in the manuscript resolve against the three `survey_*.bib` files. | `citations/survey_industry.bib` |
| `appendix/` | Review protocol and full evidence map. Edit the evidence CSV, then regenerate the table rather than hand-editing it. | `appendix/survey_protocol.tex` |
| `_pdfs/papers/` | Primary PDFs grouped by research theme. Filenames contain the note ID, short title, and arXiv ID. | `_pdfs/papers/02_data_curation_and_valuation/P049_Re-Mix_2408.14037.pdf` |
| `_pdfs/manifests/` | Complete 211-work evidence map, local-PDF metadata/hashes, missing-PDF list, and dated raw search snapshots. | `_pdfs/manifests/evidence_map.csv` |
| `_pdfs/survey_and_notes/` | The original Chinese survey draft and structured Chinese paper notes. | `embodied_data_prep_survey_zh.md` |
| `scripts/` | Reproducible literature search, arXiv metadata, PDF download/manifest, appendix rendering, and manuscript checks. | `scripts/search_literature.py` |
| `algorithmn/` | A minimal algorithm template that documents its input path and label convention. It is not imported by `main.tex`. | `algorithmn/sample_algorithm.tex` |
| `plots/data/`, `plots/plot/`, `plots/tex/` | One plot example split into source data, rendered asset, and LaTeX wrapper. These files are not imported by `main.tex`. | `plots/tex/sample_plot.tex` |
| `secs/bk/`, `secs/experiment/` | Minimal examples for an archived section and a nested section. They are not imported by `main.tex`. | `secs/experiment/sample_nested_section.tex` |
| `appendix/figures/`, `appendix/previous/`, `appendix/tables/` | Minimal appendix asset, archived-section, and table examples. They document file placement and `\input` relationships. | `appendix/tables/sample_table.tex` |

The active dependency list is determined by `\input` statements in `main.tex`;
an old `.tex`, figure, or table can therefore remain as a format sample without
affecting the survey build.

## Reproducible commands

```bash
# Regenerate the complete 211-work appendix.
python3 scripts/render_evidence_map.py

# Re-run dated DBLP/arXiv discovery (network required).
python3 scripts/search_literature.py --source all \
  --out-dir _pdfs/manifests/searches/YYYY-MM-DD
# After any targeted retry snapshots, preserve the initial log and build a
# resolved query/discovery view.
python3 scripts/merge_search_retries.py \
  --run-dir _pdfs/manifests/searches/YYYY-MM-DD

# Fetch any missing primary papers cited by the manuscript and rebuild hashes.
python3 scripts/download_core_papers.py
python3 scripts/update_pdf_manifests.py

# Check active citations, references, inputs, and placeholders.
python3 scripts/check_manuscript.py

# PDF compilation is performed by the connected Overleaf project.
# Run only the source-level check locally before synchronizing changes.
python3 scripts/check_manuscript.py
```

Build products are ignored through `.gitignore`. Submission-specific DOI,
copyright, venue, page-limit, and anonymity metadata are intentionally absent from
the active `main.tex`; add them only after choosing a venue.
