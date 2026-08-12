from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from evaluation.src.common.config import (
    ApprovedVersions,
    EvaluationPaths,
    FinalEvaluationConfig,
    InputSchema,
    LatencyConfig,
)
from evaluation.src.common.io import sha256_file


def _schema() -> InputSchema:
    return InputSchema(
        row_id="sample_id",
        split="split",
        participant_id="participant_id",
        session_id="session_id",
        timestamp="captured_at",
        image_path="relative_path",
        sample_checksum="checksum",
        facial_label="facial_label",
        pad_label="pad_label",
        behavioral_label="behavioral_label",
        fusion_label="fusion_label",
        scenario="scenario",
        attack_type="attack_type",
        source_device="source_device",
        illumination="illumination",
        condition="condition",
        pretest_detected="pretest_detected",
        pretest_latency_ms="pretest_latency_ms",
        pretest_false_alert="pretest_false_alert",
    )


def _ablation_approval() -> dict[str, object]:
    variants = {
        "facial": (["facial"], {"facial": 1.0}, False),
        "pad": (["pad"], {"pad": 1.0}, False),
        "behavioral": (["behavioral"], {"behavioral": 1.0}, False),
        "facial+pad": (
            ["facial", "pad"],
            {"facial": 0.6, "pad": 0.4},
            False,
        ),
        "facial+behavioral": (
            ["facial", "behavioral"],
            {"facial": 0.6, "behavioral": 0.4},
            False,
        ),
        "pad+behavioral": (
            ["pad", "behavioral"],
            {"pad": 0.5, "behavioral": 0.5},
            False,
        ),
        "facial+pad+behavioral+hysteresis": (
            ["facial", "pad", "behavioral"],
            {"facial": 0.4, "pad": 0.3, "behavioral": 0.3},
            True,
        ),
        "facial+pad+behavioral+no_hysteresis": (
            ["facial", "pad", "behavioral"],
            {"facial": 0.4, "pad": 0.3, "behavioral": 0.3},
            False,
        ),
    }
    return {
        name: {
            "components": components,
            "weights": weights,
            "decision_threshold": 0.5,
            "confirmation_count": 2,
            "hysteresis": hysteresis,
        }
        for name, (components, weights, hysteresis) in variants.items()
    }


@pytest.fixture
def synthetic_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> FinalEvaluationConfig:
    import evaluation.src.common.config as config_module
    import evaluation.src.common.integrity as integrity_module

    monkeypatch.setattr(config_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(integrity_module, "PROJECT_ROOT", tmp_path)
    models = tmp_path / "models"
    manifests = tmp_path / "data" / "manifests"
    processed = tmp_path / "data" / "processed"
    reports = tmp_path / "data" / "reports" / "final"
    registry = models / "registry" / "model_registry.json"
    fusion = models / "fusion" / "fusion_config.json"
    normalization = models / "fusion" / "score_normalization.json"
    for path, content in (
        (registry, '{"schema_version":"1.0","models":[]}'),
        (fusion, '{"fusion_version":"fusion-v1"}'),
        (normalization, '{"normalization_version":"normalization-v1"}'),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    sample = processed / "sample-1.bin"
    sample_two = processed / "sample-2.bin"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_bytes(b"synthetic-sample-one")
    sample_two.write_bytes(b"synthetic-sample-two")
    test = pd.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "split": ["test", "test"],
            "participant_id": ["u1", "u2"],
            "session_id": ["session-test-1", "session-test-2"],
            "relative_path": ["sample-1.bin", "sample-2.bin"],
            "checksum": [sha256_file(sample), sha256_file(sample_two)],
        }
    )
    manifest = manifests / "frozen_test_manifest.parquet"
    manifests.mkdir(parents=True, exist_ok=True)
    test.to_parquet(manifest, index=False)
    checksum = manifests / "frozen_test_manifest.sha256"
    checksum.write_text(sha256_file(manifest) + "\n", encoding="utf-8")
    metadata = manifests / "frozen_test_metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "dataset_version": "dataset-v1",
                "protocol_version": "protocol-v1",
            }
        ),
        encoding="utf-8",
    )
    development_paths: list[Path] = []
    for index in range(3):
        path = manifests / f"development-{index}.parquet"
        pd.DataFrame(
            {
                "split": ["train" if index < 2 else "validation"],
                "checksum": [f"development-{index}"],
                "session_id": [f"session-development-{index}"],
            }
        ).to_parquet(path, index=False)
        development_paths.append(path)
    source = tmp_path / "evaluation.yaml"
    source.write_text("synthetic: true\n", encoding="utf-8")
    approval = models / "registry" / "integration_approval.json"
    checksums = {
        path.relative_to(tmp_path).as_posix(): sha256_file(path)
        for path in (source, registry, fusion, normalization)
    }
    approval.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "approved_for_final_evaluation",
                "dataset_version": "dataset-v1",
                "protocol_version": "protocol-v1",
                "model_versions": {
                    "facial": "facial-v1",
                    "pad": "pad-v1",
                    "behavioral": "behavioral-v1",
                },
                "fusion_version": "fusion-v1",
                "normalization_version": "normalization-v1",
                "checksums": checksums,
                "approved_at": "2999-01-01T00:00:00+00:00",
                "git_commit": "synthetic-commit",
                "technical_owner": "synthetic-test",
                "reason": "Aprobación creada solo para pruebas sintéticas.",
                "hysteresis": {"positive_confirmation_count": 2},
                "ablation_configurations": _ablation_approval(),
            }
        ),
        encoding="utf-8",
    )
    ablations = tuple(_ablation_approval())
    return FinalEvaluationConfig(
        source_path=source,
        schema_version="1.0",
        dataset_version="dataset-v1",
        protocol_version="protocol-v1",
        paths=EvaluationPaths(
            frozen_test_manifest=manifest,
            frozen_test_checksum=checksum,
            frozen_test_metadata=metadata,
            integration_approval=approval,
            model_registry=registry,
            fusion_config=fusion,
            normalization_config=normalization,
            test_data_root=processed,
            output_directory=reports,
            development_manifests=tuple(development_paths),
        ),
        approved_versions=ApprovedVersions(
            facial="facial-v1",
            pad="pad-v1",
            behavioral="behavioral-v1",
            fusion="fusion-v1",
            normalization="normalization-v1",
        ),
        random_seed=42,
        confidence_level=0.95,
        bootstrap_iterations=200,
        latency=LatencyConfig(
            warmup_iterations=2,
            measurement_iterations=5,
            concurrency_levels=(1, 5),
        ),
        input_schema=_schema(),
        ablation_configurations=ablations,
        statistical_tests=(
            "mcnemar",
            "paired_t_or_wilcoxon",
            "friedman",
            "holm",
        ),
    )


@pytest.fixture
def synthetic_predictions() -> pd.DataFrame:
    count = 12
    labels = [0, 0, 1, 1] * 3
    return pd.DataFrame(
        {
            "sample_id": [f"s-{index}" for index in range(count)],
            "participant_id": [f"participant-{index % 3}" for index in range(count)],
            "session_id": [f"session-{index // 4}" for index in range(count)],
            "captured_at": pd.date_range(
                "2026-01-01", periods=count, freq="5s", tz="UTC"
            ),
            "facial_label": [1 - value for value in labels],
            "facial_similarity": [
                0.9 if value == 0 else 0.2 for value in labels
            ],
            "facial_threshold": [0.5] * count,
            "facial_latency_ms": [10.0 + index for index in range(count)],
            "facial_decode_ms": [2.0] * count,
            "facial_model_inference_ms": [8.0] * count,
            "pad_label": labels,
            "pad_attack_probability": [
                0.1 if value == 0 else 0.9 for value in labels
            ],
            "pad_threshold": [0.5] * count,
            "pad_latency_ms": [8.0 + index for index in range(count)],
            "pad_decode_ms": [2.0] * count,
            "pad_model_inference_ms": [6.0] * count,
            "behavioral_label": [1 - value for value in labels],
            "behavioral_reconstruction_error": [
                0.1 if value == 0 else 0.9 for value in labels
            ],
            "behavioral_threshold": [0.5] * count,
            "behavioral_latency_ms": [3.0 + index / 10 for index in range(count)],
            "fusion_label": labels,
            "facial_risk": [
                0.1 if value == 0 else 0.9 for value in labels
            ],
            "pad_risk": [0.1 if value == 0 else 0.9 for value in labels],
            "behavioral_risk": [
                0.1 if value == 0 else 0.9 for value in labels
            ],
            "fusion_risk": [0.1 if value == 0 else 0.9 for value in labels],
            "fusion_threshold": [0.5] * count,
            "fusion_predicted": labels,
            "fusion_available_components": [
                "behavioral+facial+pad"
            ] * count,
            "fusion_latency_ms": [1.0] * count,
            "total_inference_latency_ms": [24.0 + index for index in range(count)],
            "scenario": ["operator_change"] * count,
            "illumination": ["normal"] * count,
            "attack_type": [
                "printed_photo" if value else "bona_fide"
                for value in labels
            ],
            "source_device": ["synthetic-device"] * count,
            "condition": ["synthetic"] * count,
            "pretest_detected": [0] * count,
            "pretest_latency_ms": [100.0] * count,
            "pretest_false_alert": [0] * count,
        }
    )
