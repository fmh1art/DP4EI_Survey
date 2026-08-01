#!/usr/bin/env python3
"""Download primary PDFs cited by the survey but absent from the local archive."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "_pdfs" / "papers"

# arXiv ID, thematic directory, stable descriptive filename, optional primary
# publication/project PDF.  The fallback is the corresponding arXiv PDF.
TARGETS = [
    ("2308.12952", "01_data_foundations_and_engines", "P003_BridgeData_V2_2308.12952.pdf"),
    ("2307.00595", "01_data_foundations_and_engines", "P004_RH20T_2307.00595.pdf"),
    ("2607.21588", "01_data_foundations_and_engines", "P007_AXIS_2607.21588.pdf"),
    ("1811.02790", "01_data_foundations_and_engines", "P019_RoboTurk_1811.02790.pdf"),
    ("2108.03298", "01_data_foundations_and_engines", "P022_RoboMimic_2108.03298.pdf"),
    ("2410.18647", "01_data_foundations_and_engines", "P023_Data_Scaling_Laws_2410.18647.pdf"),
    ("2410.24221", "01_data_foundations_and_engines", "P026_EgoMimic_2410.24221.pdf", "https://egomimic.github.io/static/files/egomimic-supplementary.pdf"),
    ("2409.08273", "01_data_foundations_and_engines", "P027_HOP_2409.08273.pdf"),
    ("2401.08957", "02_data_curation_and_valuation", "P047_SSDF_2401.08957.pdf"),
    ("2503.03707", "02_data_curation_and_valuation", "P051_Demo_SCORE_2503.03707.pdf"),
    ("2604.23000", "02_data_curation_and_valuation", "P057_RINSE_2604.23000.pdf"),
    ("2211.11736", "03_semantic_labeling_and_synthesis", "P075_DIAL_2211.11736.pdf"),
    ("2302.06671", "03_semantic_labeling_and_synthesis", "P095_GenAug_2302.06671.pdf", "https://www.roboticsproceedings.org/rss19/p010.pdf"),
    ("2302.11550", "03_semantic_labeling_and_synthesis", "P096_ROSIE_2302.11550.pdf", "https://www.roboticsproceedings.org/rss19/p027.pdf"),
    ("2503.18738", "03_semantic_labeling_and_synthesis", "P099_RoboEngine_2503.18738.pdf", "https://roboengine.github.io/resources/roboengine-paper.pdf"),
    ("2311.01455", "03_semantic_labeling_and_synthesis", "P111_RoboGen_2311.01455.pdf", "https://raw.githubusercontent.com/mlresearch/v235/main/assets/wang24cc/wang24cc.pdf"),
    ("2310.01361", "03_semantic_labeling_and_synthesis", "P112_GenSim_2310.01361.pdf"),
    ("2409.03403", "03_semantic_labeling_and_synthesis", "P122_RoVi_Aug_2409.03403.pdf", "https://raw.githubusercontent.com/mlresearch/v270/main/assets/chen25a/chen25a.pdf"),
    ("2306.11706", "04_vla_world_model_and_post_training_reports", "P134_RoboCat_2306.11706.pdf"),
    ("2401.12963", "04_vla_world_model_and_post_training_reports", "P135_AutoRT_2401.12963.pdf"),
    ("2212.06817", "04_vla_world_model_and_post_training_reports", "P157_RT1_2212.06817.pdf"),
    ("2307.15818", "04_vla_world_model_and_post_training_reports", "P158_RT2_2307.15818.pdf"),
    ("2405.12213", "04_vla_world_model_and_post_training_reports", "P160_Octo_2405.12213.pdf"),
    ("2304.14108", "05_llm_data_preparation_inspiration", "P204a_DataComp_2304.14108.pdf"),
    ("2406.17711", "05_llm_data_preparation_inspiration", "P204b_JEST_2406.17711.pdf"),
]


def valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 10_000:
        return False
    result = subprocess.run(
        ["pdfinfo", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    )
    return result.returncode == 0


def download(target: tuple[str, ...]) -> str:
    arxiv_id, category, filename = target[:3]
    source_url = target[3] if len(target) == 4 else f"https://arxiv.org/pdf/{arxiv_id}"
    destination = PAPERS / category / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    if valid_pdf(destination):
        return f"ok   {arxiv_id} (already present)"
    partial = destination.with_suffix(".pdf.part")
    last_error = ""
    for attempt in range(5):
        result = subprocess.run(
            [
                "curl", "--fail", "--silent", "--show-error", "--location",
                "--max-time", "600", "--continue-at", "-", source_url,
                "--output", str(partial),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode == 0 and valid_pdf(partial):
            partial.replace(destination)
            return f"ok   {arxiv_id} -> {destination.relative_to(ROOT)}"
        last_error = result.stderr.decode(errors="replace").strip()
        if attempt < 4:
            time.sleep(4 * (attempt + 1))
    return f"FAIL {arxiv_id}: {last_error or 'downloaded file was not a valid PDF'}"


def main() -> None:
    # A single resumable stream is both faster on throttled scholarly endpoints
    # and less burdensome than parallel downloads.
    for target in TARGETS:
        print(download(target), flush=True)


if __name__ == "__main__":
    main()
