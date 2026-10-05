# Engineering review — October 4, 2026

## Scope

Source review of `src/biomedical_ir/evaluation.py`, fusion/statistical helpers, metric tests and README. This review addresses a bounded correctness issue; it does not certify the entire application, rerun all research experiments, or establish production readiness.

## Finding and repair

Both the trusted evaluator and educational mean helpers used queries present in the run to choose the evaluation population. Omitting a failed query could inflate reported averages.

Use all qrels query IDs as the denominator, with missing runs contributing zero. Ignore unjudged queries as before. Load pytrec_eval only when the trusted evaluator is called, allowing pure educational metric checks without that dependency.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests -p test_missing_query_regressions.py -v` — 2 tests passed. The new pytrec_eval regression is included in `tests/test_metrics.py`; it requires GitHub CI because pytrec_eval is unavailable locally.

All changed Python files were syntax-compiled. Package installation from this workspace is blocked, so full dependency-backed suites and production builds are not described as passed. GitHub checks on the pull request provide the remaining integration validation.

## Next implementation work

Confirm that every stored run covers the intended 323 test queries before regenerating tables. Expand to additional benchmark datasets, validation-based hyperparameter tuning, fusion comparisons, and multiple-testing correction. Existing published tables were not rewritten by this repair.

## Evidence boundary

No raw benchmark data, measured research results, corpus approval records, model releases or production deployments were changed. Any affected scientific output must be re-executed and linked to the accepted source commit before updating manuscript claims.
