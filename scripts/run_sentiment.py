#!/usr/bin/env python
"""Evaluate TF-IDF/LR and optional pretrained RoBERTa on drug reviews."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from biomedical_ir.sentiment import LABELS, prepare_reviews


def main():
    from datasets import load_dataset
    from huggingface_hub import HfApi
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="lewtun/drug-reviews")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--model", default="cardiffnlp/twitter-roberta-base-sentiment-latest")
    parser.add_argument("--model-revision", default="main")
    parser.add_argument("--transformer", action="store_true")
    parser.add_argument("--max-train", type=int, default=10000)
    parser.add_argument("--max-eval", type=int, default=1000)
    parser.add_argument("--output", default="results/sentiment")
    args = parser.parse_args()
    if args.max_train < 30 or args.max_eval < 3:
        parser.error("Use at least 30 training and 3 evaluation rows")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"status": "running", "started": datetime.now(timezone.utc).isoformat(),
                "arguments": vars(args), "label_source": "rating proxy: 1-4 negative, 5-6 neutral, 7-10 positive",
                "python": platform.python_version(), "seed": 42,
                "limitations": ["Exact-text deduplication does not remove near duplicates or patient overlap",
                                "Ratings are satisfaction proxies, not human sentiment annotations",
                                "Pretrained model is Twitter-domain; training contamination is unknown"]}
    try:
        api = HfApi()
        revision = api.dataset_info(args.dataset, revision=args.revision).sha
        manifest["dataset_sha"] = revision
        ds = load_dataset(args.dataset, revision=revision)
        if not {"train", "test"}.issubset(ds):
            raise ValueError("Dataset needs official train and test splits")
        train, train_audit = prepare_reviews(ds["train"])
        test, test_audit = prepare_reviews(ds["test"], [r["hash"] for r in train])
        fit, dev = train_test_split(train, test_size=0.2, random_state=42,
                                    stratify=[r["label"] for r in train])
        # Limits apply after split/deduplication; fixed seeded order, no test tuning.
        import random
        rng = random.Random(42)
        for partition in (fit, dev, test):
            rng.shuffle(partition)
        fit, dev, test = fit[:args.max_train], dev[:args.max_eval], test[:args.max_eval]
        for name, rows in (("train", fit), ("dev", dev), ("test", test)):
            if set(r["label"] for r in rows) != set(LABELS):
                raise ValueError(f"{name} sample lacks a class; increase sample limits")
        manifest["audit"] = {"train": train_audit, "test": test_audit}
        manifest["partitions"] = {name: {"count": len(rows),
            "labels": dict(Counter(r["label"] for r in rows)),
            "hashes": [r["hash"] for r in rows]}
            for name, rows in (("train", fit), ("dev", dev), ("test", test))}
        manifest["packages"] = {p: version(p) for p in ("datasets", "scikit-learn", "transformers", "torch")}
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        manifest["git_commit"] = git.stdout.strip() if git.returncode == 0 else None
        models = {}
        selected, best = None, -1
        for c in (0.1, 1.0, 10.0):
            model = make_pipeline(TfidfVectorizer(max_features=50000, ngram_range=(1, 2)),
                                  LogisticRegression(C=c, max_iter=1000, random_state=42))
            model.fit([r["text"] for r in fit], [r["label"] for r in fit])
            report = classification_report([r["label"] for r in dev],
                model.predict([r["text"] for r in dev]), labels=LABELS,
                output_dict=True, zero_division=0)
            models[str(c)] = report["macro avg"]["f1-score"]
            if models[str(c)] > best:
                best, selected = models[str(c)], model
                manifest["selected_C"] = c
        manifest["dev_macro_f1_by_C"] = models
        start = time.perf_counter()
        predictions = {"tfidf_lr": list(selected.predict([r["text"] for r in test]))}
        manifest["lr_prediction_seconds"] = time.perf_counter() - start
        if args.transformer:
            import torch
            from transformers import pipeline
            model_sha = api.model_info(args.model, revision=args.model_revision).sha
            manifest["model_sha"] = model_sha
            clf = pipeline("text-classification", model=args.model, revision=model_sha,
                           device=0 if torch.cuda.is_available() else -1)
            start = time.perf_counter()
            predicted = clf([r["text"] for r in test], batch_size=16,
                            truncation=True, max_length=512)
            labels = [r["label"].lower() for r in predicted]
            if not set(labels).issubset(LABELS):
                raise ValueError("Model must expose negative/neutral/positive label names")
            predictions["pretrained_roberta"] = labels
            manifest["transformer_prediction_seconds"] = time.perf_counter() - start
        actual = [r["label"] for r in test]
        metrics = {name: {"report": classification_report(actual, pred, labels=LABELS,
                            output_dict=True, zero_division=0),
                         "confusion_matrix": confusion_matrix(actual, pred, labels=LABELS).tolist(),
                         "label_order": LABELS} for name, pred in predictions.items()}
        (output / "metrics.json").write_text(json.dumps(metrics, indent=2))
        # Store hashes and predictions; avoid redistributing review text.
        records = [{"hash": row["hash"], "actual": row["label"],
                    **{name: pred[i] for name, pred in predictions.items()}}
                   for i, row in enumerate(test)]
        (output / "predictions.json").write_text(json.dumps(records, indent=2))
        manifest["status"] = "complete"
        print(json.dumps(metrics, indent=2))
    except Exception as exc:
        manifest.update(status="failed", error=repr(exc))
        raise
    finally:
        manifest["finished"] = datetime.now(timezone.utc).isoformat()
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
