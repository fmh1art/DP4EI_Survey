# Data Preparation for Embodied Intelligence Survey

This repository preserves the original ACM-style conference template and uses it
for the survey **“From Raw Interactions to Trainable Distributions: Data
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
├── citations/survey_ref.bib, citations/survey_extra.bib
└── appendix/survey_protocol.tex
    └── appendix/evidence_map.tex  (generated from the 204-work CSV)
```

`\cite{key}` in a section resolves to an entry in
the two `citations/survey_*.bib` databases; `\label{...}` and `\ref{...}` connect sections,
figures, tables, equations, and appendices. Run
`python3 scripts/check_manuscript.py` to detect missing citation keys or local
primary PDFs, duplicate or missing labels, and active TODO markers.

## Folder guide and sample formats

| Path | What belongs here | Active sample |
|---|---|---|
| `secs/` | One logical manuscript section per `.tex` file. Start with `%!TEX root = ../main.tex`, add a stable `\label`, and cite only verified BibTeX keys. | `secs/05semantic_curation.tex` |
| `tables/` | Reusable table environments. The section imports the whole table with `\input{tables/name}`; captions and labels live in the table file. | `tables/curation_comparison.tex` |
| `figures/tex/` | Editable TikZ figures. The file contains the complete `figure`/`figure*` environment and is imported with `\input`. | `figures/tex/data_prep_lifecycle.tex` |
| `figures/fig/` | Legacy PDF figure assets showing the binary-asset convention. These are retained as template samples but are not used by the survey. | `figures/fig/framework_overview.pdf` |
| `citations/` | BibTeX databases. `survey_ref.bib` and `survey_extra.bib` are active; `ref.bib` is the preserved legacy sample. | `citations/survey_ref.bib` |
| `appendix/` | Review protocol and full evidence map. Edit the evidence CSV, then regenerate the table rather than hand-editing it. | `appendix/survey_protocol.tex` |
| `_pdfs/papers/` | Primary PDFs grouped by research theme. Filenames contain the note ID, short title, and arXiv ID. | `_pdfs/papers/02_data_curation_and_valuation/P049_Re-Mix_2408.14037.pdf` |
| `_pdfs/manifests/` | Complete 204-work index, local-PDF metadata/hashes, missing-PDF list, and dated raw search snapshots. | `_pdfs/manifests/included_pdfs.csv` |
| `_pdfs/survey_and_notes/` | The original Chinese survey draft and structured Chinese paper notes. | `embodied_data_prep_survey_zh.md` |
| `scripts/` | Reproducible literature search, arXiv metadata, PDF download/manifest, appendix rendering, and manuscript checks. | `scripts/search_literature.py` |
| `algorithmn/`, `plots/`, `secs/bk/`, `secs/experiment/` | Preserved legacy template examples. They show algorithm, plot-data, backup-section, and nested-section conventions and are intentionally not imported by `main.tex`. | `algorithmn/deepprep.tex` |

The active dependency list is determined by `\input` statements in `main.tex`;
an old `.tex`, figure, or table can therefore remain as a format sample without
affecting the survey build.

## Reproducible commands

```bash
# Regenerate the complete 204-work appendix.
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

# Compile with Tectonic; a standard latexmk installation also works.
mkdir -p build
tectonic --keep-logs --outdir build main.tex
# alternatively: latexmk -pdf -outdir=build main.tex
```

Build products are ignored through `.gitignore`. Submission-specific DOI,
copyright, venue, page-limit, and anonymity metadata are intentionally absent from
the active `main.tex`; add them only after choosing a venue.
