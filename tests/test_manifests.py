"""Tests for experiment manifest schema/validation (Section 20/26 of the spec)."""

from __future__ import annotations

import json

import pytest

from biomedical_ir.manifests import (
    REQUIRED_FIELDS,
    build_manifest,
    save_manifest,
    validate_manifest,
)


def make_manifest(**overrides):
    base = dict(
        experiment_id="exp-test-001",
        dataset="BeIR/nfcorpus",
        split="test",
        model="bm25",
        parameters={"k1": 1.2, "b": 0.75},
        seed=42,
        device="cpu",
        runtime_seconds=1.23,
        status="complete",
    )
    base.update(overrides)
    return build_manifest(**base)


class TestBuildManifest:
    def test_has_all_required_fields(self):
        m = make_manifest()
        for field in REQUIRED_FIELDS:
            assert field in m

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            make_manifest(status="done")

    def test_git_commit_is_a_string(self):
        m = make_manifest()
        assert isinstance(m["git_commit"], str)

    def test_library_versions_populated(self):
        m = make_manifest()
        assert "numpy" in m["library_versions"]


class TestValidateManifest:
    def test_valid_manifest_has_no_problems(self):
        assert validate_manifest(make_manifest()) == []

    def test_missing_field_detected(self):
        m = make_manifest()
        del m["seed"]
        problems = validate_manifest(m)
        assert any("seed" in p for p in problems)

    def test_negative_runtime_flagged(self):
        m = make_manifest()
        m["runtime_seconds"] = -5
        problems = validate_manifest(m)
        assert any("runtime_seconds" in p for p in problems)

    def test_failed_status_requires_error_field(self):
        m = make_manifest(status="failed")
        problems = validate_manifest(m)
        assert any("error" in p for p in problems)

    def test_failed_status_with_error_is_valid(self):
        m = make_manifest(status="failed", error="CUDA OOM")
        assert validate_manifest(m) == []


class TestSaveManifest:
    def test_save_and_reload_roundtrip(self, tmp_path):
        m = make_manifest()
        out_path = save_manifest(m, manifests_dir=tmp_path)
        assert out_path.exists()
        reloaded = json.loads(out_path.read_text())
        assert reloaded["experiment_id"] == "exp-test-001"

    def test_save_invalid_manifest_raises(self, tmp_path):
        m = make_manifest()
        del m["seed"]
        with pytest.raises(ValueError):
            save_manifest(m, manifests_dir=tmp_path)
