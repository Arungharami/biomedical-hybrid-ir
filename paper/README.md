# Paper

Working title: **Hybrid Biomedical Information Retrieval with Lexical,
Dense, and Cross-Encoder Reranking: A Reproducible Study on NFCorpus**

Course: CAP 6776 — Information Retrieval

## Sections

| File | Status |
|---|---|
| `abstract.md` | ✅ Complete |
| `introduction.md` | ✅ Complete |
| `related-work.md` | ✅ Complete |
| `methodology.md` | ✅ Complete — RQs, hypotheses, and per-hypothesis verdicts |
| `experimental-setup.md` | ✅ Complete |
| `results.md` | ✅ Complete — all 6 models, statistical analysis, error analysis |
| `discussion.md` | ✅ Complete |
| `limitations.md` | ✅ Complete |
| `conclusion.md` | ✅ Complete |
| `references.bib` | ✅ Complete — verified against primary sources |

Figures: `results/figures/figure{3-9}_*.{png,svg,pdf}` (`scripts/generate_figures.py`).
Figures 1-2 (architecture, pipeline) are the Mermaid diagram in
`docs/architecture.md` rather than a redundant static image.

## Writing rule (Section 31 of the project spec)

The paper distinguishes planned / running / completed experiments from
observed results and interpretation. No claim of the form "X significantly
outperformed Y" is written unless real experimental output and the
corresponding significance test in `results/` support it — and where an
earlier draft's language ran ahead of what a since-completed test actually
showed (the M6 cross-encoder nDCG@10 result), it was corrected in place
rather than left standing; see `results/tables/main_results.md`'s M6
section and `docs/models.md` for that correction's history.
