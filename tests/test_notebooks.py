"""Lightweight CI check: every notebook is valid nbformat JSON and imports
from src/biomedical_ir/ rather than duplicating large amounts of logic
(Section 21 of the project spec). Does NOT execute notebooks (that would
require network access / heavy models in CI) -- see
docs/reproducibility.md for the record of which notebooks were executed
for real during development.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_DIR = Path(__file__).resolve().parents[1] / "notebooks"
EXPECTED_NOTEBOOKS = [
    "00_environment_setup.ipynb",
    "01_nfcorpus_dataset_audit.ipynb",
    "02_tfidf_baseline.ipynb",
    "03_bm25_baseline.ipynb",
    "04_bge_dense_retrieval.ipynb",
    "05_medcpt_dense_retrieval.ipynb",
    "06_hybrid_rrf.ipynb",
    "07_cross_encoder_reranking.ipynb",
    "08_evaluation.ipynb",
    "09_statistical_analysis.ipynb",
    "10_error_analysis.ipynb",
    "11_export_research_results.ipynb",
    "Biomedical_Hybrid_IR_Full_Pipeline.ipynb",
]


class TestNotebooksExist:
    def test_all_expected_notebooks_present(self):
        missing = [n for n in EXPECTED_NOTEBOOKS if not (NOTEBOOKS_DIR / n).exists()]
        assert missing == [], f"Missing notebooks: {missing}"


@pytest.mark.parametrize("notebook_name", EXPECTED_NOTEBOOKS)
class TestNotebookValidity:
    def test_is_valid_nbformat(self, notebook_name):
        nb = nbformat.read(NOTEBOOKS_DIR / notebook_name, as_version=4)
        nbformat.validate(nb)  # raises on malformed notebooks

    def test_has_at_least_one_markdown_and_one_code_cell(self, notebook_name):
        nb = nbformat.read(NOTEBOOKS_DIR / notebook_name, as_version=4)
        cell_types = {c.cell_type for c in nb.cells}
        assert "markdown" in cell_types
        assert "code" in cell_types

    def test_imports_from_biomedical_ir_or_calls_scripts(self, notebook_name):
        """Every notebook should reuse project code/artifacts (import
        biomedical_ir, invoke a scripts/*.py entry point, or load a
        results/*.json artifact those scripts produced) rather than
        reimplementing retrieval/evaluation logic inline."""
        nb = nbformat.read(NOTEBOOKS_DIR / notebook_name, as_version=4)
        source = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
        assert "biomedical_ir" in source or "scripts/" in source or "results/" in source
