"""Multi-benchmark validation, fusion ablation and held-out evaluation."""

from __future__ import annotations

import csv
import gc
import itertools
import json
import time
from pathlib import Path

from .bm25 import BM25Config, BM25Retriever
from .data import compose_document_text
from .evaluation import evaluate_run
from .research_fusion import combine, validate_run
from .research_stats import comparison_report, paired_effect
from .tfidf import TfidfConfig, TfidfRetriever


def choose(trials, qrels, evaluator=evaluate_run):
    """Select with dev qrels only; preserve a trace, deterministic first-trial ties."""
    if not qrels:
        raise ValueError("Selection requires development judgments")
    trace, selected, best = [], None, float("-inf")
    for parameters, run in trials:
        score = evaluator(run, qrels)["summary"]["nDCG@10"]
        trace.append({"parameters": parameters, "dev_nDCG@10": score})
        if score > best:
            selected, best = parameters, score
    if selected is None:
        raise ValueError("Empty tuning grid")
    return selected, trace


def pinned_model(repo, provenance):
    from huggingface_hub import HfApi, snapshot_download
    sha = provenance.get(repo) or HfApi().model_info(repo).sha
    path = snapshot_download(repo, revision=sha, allow_patterns=[
        "*.json", "*.safetensors", "pytorch_model.bin", "*.txt", "*.model", "*/*.json"])
    provenance[repo] = sha
    return path


def dense_runs(name, data, partitions, depth, provenance, device):
    if name == "bge":
        from .dense import DenseModelConfig, DenseRetriever
        path = pinned_model("BAAI/bge-base-en-v1.5", provenance)
        retriever = DenseRetriever(DenseModelConfig(name=path, top_k=depth), device=device)
        corpus = {d: compose_document_text(**text) for d, text in data.corpus.items()}
    elif name == "medcpt":
        from .medcpt import MedCPTConfig, MedCPTRetriever
        config = MedCPTConfig(
            query_encoder=pinned_model("ncbi/MedCPT-Query-Encoder", provenance),
            article_encoder=pinned_model("ncbi/MedCPT-Article-Encoder", provenance), top_k=depth)
        retriever = MedCPTRetriever(config, device=device)
        corpus = data.corpus
    else:
        raise ValueError(f"Unknown dense method: {name}")
    start = time.perf_counter()
    retriever.build_index(corpus)
    indexing = time.perf_counter() - start
    runs, timings = {}, {"index_seconds": indexing}
    for split, queries in partitions.items():
        start = time.perf_counter()
        runs[split] = retriever.rank_all(queries, top_k=depth)
        timings[f"{split}_query_seconds"] = time.perf_counter() - start
    del retriever
    gc.collect()
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return runs, timings


def query_conditions(queries, lexical, dense, gains):
    """Predefined descriptive strata; no post-hoc significance claims."""
    groups = {"short_le8_tokens": [], "long_gt8_tokens": [],
              "low_top10_overlap_le0.2": [], "other_top10_overlap": []}
    for q in sorted(gains):
        groups["short_le8_tokens" if len(queries[q].split()) <= 8 else "long_gt8_tokens"].append(q)
        a = {d for d, _ in lexical[q][:10]}
        b = {d for d, _ in dense[q][:10]}
        overlap = len(a & b) / len(a | b) if a | b else 0.0
        groups["low_top10_overlap_le0.2" if overlap <= 0.2 else "other_top10_overlap"].append(q)
    return {name: {"queries": len(ids), "mean_nDCG_gain":
                  sum(gains[q] for q in ids) / len(ids) if ids else None,
                  "wins": sum(gains[q] > 1e-12 for q in ids),
                  "losses": sum(gains[q] < -1e-12 for q in ids)}
            for name, ids in groups.items()}


def run_study(data, config, output, frozen=None, evaluator=evaluate_run, dense_provider=dense_runs):
    """All tuning finishes before test evaluation; results are isolated by run ID."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    depth = config["candidate_depth"]
    if depth < 100:
        raise ValueError("Candidate depth must be at least 100 for Recall@100/MAP@100")
    models = config["dense_methods"]
    if not models or set(models) - {"bge", "medcpt"} or len(models) != len(set(models)):
        raise ValueError("Use unique bge/medcpt dense methods")
    dev = data.qrels.get("dev", {})
    if not dev and frozen is None:
        raise ValueError("No dev split: supply frozen settings selected on another benchmark")
    partitions = {s: {q: data.queries[q] for q in sorted(data.qrels[s])}
                  for s in ("dev", "test") if data.qrels.get(s)}
    text = {d: compose_document_text(**fields) for d, fields in data.corpus.items()}
    selected = {"candidate_depth": depth, "dense_methods": models, "fusion": {}}
    if frozen is not None:
        for key in ("candidate_depth", "dense_methods"):
            if frozen[key] != selected[key]:
                raise ValueError(f"Frozen {key} mismatch")
    trace, runs, timing, model_shas = {}, {s: {} for s in partitions}, {}, {}
    if frozen is not None:
        model_shas.update(frozen.get("model_shas", {}))
    start = time.perf_counter()
    bm = BM25Retriever(BM25Config(top_k=depth)).fit(text)
    timing["bm25_index_seconds"] = time.perf_counter() - start
    if frozen is None:
        def trials():
            for k1, b in itertools.product(config["bm25_k1"], config["bm25_b"]):
                bm.config.k1, bm.config.b = k1, b
                yield {"k1": k1, "b": b}, bm.rank_all(partitions["dev"], top_k=depth)
        selected["bm25"], trace["bm25"] = choose(trials(), dev, evaluator)
    else:
        selected["bm25"] = frozen["bm25"]
    bm.config.k1, bm.config.b = selected["bm25"]["k1"], selected["bm25"]["b"]
    start = time.perf_counter()
    tfidf = TfidfRetriever(TfidfConfig(top_k=depth)).fit(text)
    timing["tfidf_index_seconds"] = time.perf_counter() - start
    for split, queries in partitions.items():
        for name, retriever in (("bm25", bm), ("tfidf", tfidf)):
            start = time.perf_counter()
            runs[split][name] = retriever.rank_all(queries, top_k=depth)
            timing[f"{split}/{name}_query_seconds"] = time.perf_counter() - start
    for name in models:
        generated, timing[name] = dense_provider(name, data, partitions, depth, model_shas,
                                                config.get("device", "cpu"))
        for split in partitions:
            validate_run(generated[split], partitions[split], data.corpus)
            runs[split][name] = generated[split]
    comparisons = []
    for dense in models:
        for method, grid in (("rrf", config["rrf_k"]), ("weighted", config["lexical_weights"])):
            name = f"bm25_{dense}_{method}"
            if frozen is None:
                trials = ((p, combine(runs["dev"]["bm25"], runs["dev"][dense], method, p, depth))
                          for p in grid)
                parameter, trace[name] = choose(trials, dev, evaluator)
            else:
                parameter = frozen["fusion"][name]
            selected["fusion"][name] = parameter
            for split in partitions:
                start = time.perf_counter()
                runs[split][name] = combine(runs[split]["bm25"], runs[split][dense], method, parameter, depth)
                timing[f"{split}/{name}_fusion_only_seconds"] = time.perf_counter() - start
            comparisons.extend([(name, "bm25"), (name, dense)])
    if config.get("rerank", False):
        from .reranker import CrossEncoderReranker, RerankerConfig
        path = pinned_model("ncbi/MedCPT-Cross-Encoder", model_shas)
        reranker = CrossEncoderReranker(RerankerConfig(model=path, top_k=depth),
                                      device=config.get("device", "cpu"))
        sources = ["bm25", *models, *selected["fusion"]]
        # Use one common pool for every candidate source, selected by average dev nDCG.
        if frozen is None:
            scores = []
            for pool in config["rerank_pools"]:
                if pool < 10 or pool > depth:
                    raise ValueError("Rerank pool must be between 10 and candidate depth")
                score = sum(evaluator(reranker.rerank_run(runs["dev"][s], partitions["dev"],
                    data.corpus, candidate_pool=pool, top_k=depth), dev)["summary"]["nDCG@10"]
                    for s in sources) / len(sources)
                scores.append({"pool": pool, "average_dev_nDCG@10": score})
            selected["rerank_pool"] = max(scores, key=lambda x: x["average_dev_nDCG@10"])["pool"]
            trace["rerank_pool"] = scores
        else:
            selected["rerank_pool"] = frozen["rerank_pool"]
        if not 10 <= selected["rerank_pool"] <= depth:
            raise ValueError("Frozen rerank pool outside candidate budget")
        for source in sources:
            name = source + "_reranked"
            start = time.perf_counter()
            runs["test"][name] = reranker.rerank_run(runs["test"][source], partitions["test"],
                data.corpus, candidate_pool=selected["rerank_pool"], top_k=depth)
            timing[f"test/{name}_reranking_only_seconds"] = time.perf_counter() - start
            comparisons.append((name, source))
    selected["model_shas"] = model_shas
    # Write frozen settings and trace before any final test metric is computed.
    (output / "selection.json").write_text(json.dumps({"settings": selected, "dev_trials": trace,
        "source_dataset": data.provenance, "frozen_source": frozen}, indent=2))
    metrics, primary = {}, {}
    for name, run in runs["test"].items():
        validate_run(run, partitions["test"], data.corpus)
        result = evaluator(run, data.qrels["test"], include_per_query=True)
        metrics[name] = result
        primary[name] = {q: result["per_query"][q].get("ndcg_cut_10", 0.0) for q in partitions["test"]}
        (output / f"run-{name}.json").write_text(json.dumps(run))
    resamples, seed = config["resamples"], config["seed"]
    stats = comparison_report(primary, comparisons, resamples, seed)
    system_intervals = {name: paired_effect(list(scores.values()), [0.0] * len(scores), resamples, seed)
                        for name, scores in primary.items()}
    # System-vs-zero bootstrap is used only for its mean/interval, not its p-value.
    intervals = {name: {k: value[k] for k in ("mean_difference", "ci95_low", "ci95_high")}
                 for name, value in system_intervals.items()}
    conditions = {}
    for dense in models:
        for method in ("rrf", "weighted"):
            name = f"bm25_{dense}_{method}"
            gains = {q: primary[name][q] - primary[dense][q] for q in primary[name]}
            conditions[name] = query_conditions(partitions["test"], runs["test"]["bm25"],
                                                runs["test"][dense], gains)
    report = {"metrics": metrics, "primary_mean_ci95": intervals, "statistics": stats,
              "conditions_vs_dense": conditions, "timing": timing, "model_shas": model_shas,
              "notes": ["MAP is truncated to retrieved candidate depth; emphasize MAP@100",
                        "Reranked runs are pool-limited; Recall@100/MAP are not full-depth comparisons",
                        "Latency entries are stage-specific batch times, not end-to-end request latency",
                        "Confidence intervals are pointwise; subgroup analysis is descriptive"]}
    (output / "report.json").write_text(json.dumps(report, indent=2))
    fields = ["system", "nDCG@10", "P@10", "Recall@100", "MAP@100", "MRR@10"]
    with (output / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for name, result in metrics.items():
            writer.writerow({"system": name, **{f: result["summary"].get(f) for f in fields[1:]}})
    return report
