from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.external_data.adapters import (
    KEYBOARD_COLUMNS,
    MOUSE_COLUMNS,
    adapt_cmu_wide,
    adapt_keystroke_events,
    adapt_mouse_events,
)
from src.external_data.experiments import (
    PAD_PLANS,
    DatasetUse,
    ExperimentGateError,
    ExperimentPlan,
    behavioral_metrics,
    pad_metrics,
    validate_experiment_plan,
)
from src.external_data.frames import validate_frames_per_second
from src.external_data.manifests import (
    PAD_MANIFEST_COLUMNS,
    build_external_pad_manifest,
)
from src.external_data.registry import (
    DatasetEntry,
    DatasetNotApprovedError,
    LicenseGateError,
    RegistryError,
    assert_download_allowed,
    assert_raw_unchanged,
    load_registry,
    raw_snapshot,
)
from src.external_data.reporting import (
    build_comparison,
    generate_readiness_report,
)
from src.external_data.downloads import write_access_instructions
from src.external_data.validation import (
    assert_group_isolation,
    assert_subject_isolation_when_required,
    duplicate_checksums,
    validate_raw_directory,
    validate_pad_labels,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = PROJECT_ROOT / "external-data" / "registry" / "datasets.yaml"


def _pad_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "dataset_version": "v1",
        "source_dataset": "replay_attack",
        "source_subject_id": "s1",
        "source_session_id": "session1",
        "source_video_id": "video1",
        "source_capture_id": "capture1",
        "file_path": "interim/pad_frames/frame.jpg",
        "checksum": "a" * 64,
        "presentation_label": "bona_fide",
        "attack_type": "none",
        "capture_device": None,
        "presentation_device": None,
        "illumination": None,
        "environment": None,
        "split_original": "train",
        "split_project": "train",
        "quality_status": "accepted",
        "rejection_reasons": [],
        "license_status": "downloaded",
    }
    row.update(updates)
    return row


def _approved_entry(**updates: object) -> DatasetEntry:
    payload: dict[str, object] = {
        "dataset_id": "sample",
        "official_name": "Sample",
        "official_url": "https://example.org/data",
        "download_url": "https://example.org/data.zip",
        "version": "1",
        "modality": "pad",
        "intended_use": ["test"],
        "license_name": "Research License",
        "license_url": "https://example.org/license",
        "license_reviewed_at": "2026-07-26",
        "license_copy_path": "registry/licenses/sample.txt",
        "commercial_use_allowed": False,
        "derived_models_allowed": True,
        "redistribution_allowed": False,
        "agreement_required": False,
        "agreement_evidence_path": None,
        "citation": "Sample",
        "downloaded_at": None,
        "checksum": None,
        "storage_path": "external-data/raw/sample",
        "status": "approved",
        "access_instructions": ["Review"],
        "approved_download_hosts": ["example.org"],
    }
    payload.update(updates)
    return DatasetEntry.model_validate(payload)


def test_registry_has_all_authorized_datasets() -> None:
    registry = load_registry(REGISTRY)
    assert len(registry.datasets) == 11
    assert len({entry.dataset_id for entry in registry.datasets}) == 11


def test_nonapproved_dataset_cannot_download() -> None:
    entry = load_registry(REGISTRY).get("replay_attack")
    with pytest.raises(DatasetNotApprovedError, match="descarga bloqueada"):
        assert_download_allowed(entry, REGISTRY)


def test_missing_license_copy_stops_approved_dataset(tmp_path: Path) -> None:
    with pytest.raises(LicenseGateError, match="no existe la copia"):
        assert_download_allowed(_approved_entry(), tmp_path / "datasets.yaml")


def test_raw_modification_is_detected(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    before = raw_snapshot(raw)
    (raw / "changed.bin").write_bytes(b"changed")
    with pytest.raises(RegistryError, match="raw fue modificada"):
        assert_raw_unchanged(before, raw)


def test_placeholder_does_not_count_as_downloaded_data(tmp_path: Path) -> None:
    entry = load_registry(REGISTRY).get("cmu_keystroke")
    placeholder = tmp_path / entry.storage_path
    placeholder.mkdir(parents=True)
    (placeholder / ".gitkeep").write_text("", encoding="utf-8")
    result = validate_raw_directory(entry, tmp_path)
    assert not result.valid
    assert "raw_directory_empty" in result.issues


def test_video_cannot_cross_splits() -> None:
    frame = pd.DataFrame(
        [
            _pad_row(split_project="train"),
            _pad_row(file_path="b.jpg", checksum="b" * 64, split_project="test"),
        ]
    )
    with pytest.raises(ValueError, match="source_video_id"):
        assert_group_isolation(frame)


def test_subject_cannot_cross_splits_when_protocol_requires_it() -> None:
    frame = pd.DataFrame(
        [
            _pad_row(source_video_id="v1", split_project="train"),
            _pad_row(
                source_video_id="v2",
                file_path="b.jpg",
                checksum="b" * 64,
                split_project="test",
            ),
        ]
    )
    with pytest.raises(ValueError, match="source_subject_id"):
        assert_subject_isolation_when_required(
            frame, protocol_requires_subject_disjoint=True
        )


def test_duplicate_frames_are_detected() -> None:
    frame = pd.DataFrame(
        [
            _pad_row(source_video_id="v1"),
            _pad_row(source_video_id="v2", file_path="b.jpg"),
        ]
    )
    assert len(duplicate_checksums(frame)) == 2


def test_pad_labels_are_validated() -> None:
    frame = pd.DataFrame([_pad_row(presentation_label="fake")])
    with pytest.raises(ValueError, match="Etiquetas PAD inválidas"):
        validate_pad_labels(frame)


def test_pad_label_and_attack_type_must_be_consistent() -> None:
    frame = pd.DataFrame([_pad_row(attack_type="printed_photo")])
    with pytest.raises(ValueError, match="inconsistentes"):
        validate_pad_labels(frame)


def test_keystroke_adapter_removes_text_and_key_identity() -> None:
    source = pd.DataFrame(
        {
            "key": ["A"],
            "text": ["secret"],
            "code": ["KeyA"],
            "password": ["secret"],
            "dwell_time": [0.1],
            "subject": ["s1"],
            "session": ["x1"],
        }
    )
    adapted = adapt_keystroke_events(source)
    assert list(adapted.columns) == KEYBOARD_COLUMNS
    assert not {"key", "text", "code", "password"} & set(adapted.columns)
    assert "secret" not in adapted.astype(str).to_string()


def test_cmu_wide_adapter_does_not_persist_feature_key_names() -> None:
    source = pd.DataFrame(
        {
            "subject": ["s1"],
            "sessionIndex": [1],
            "rep": [1],
            "H.period": [0.1],
            "DD.period.t": [0.2],
        }
    )
    adapted = adapt_cmu_wide(source)
    assert set(adapted.columns) == set(KEYBOARD_COLUMNS)
    assert "period" not in adapted.astype(str).to_string().casefold()


def test_mouse_coordinates_are_normalized() -> None:
    source = pd.DataFrame(
        {
            "timestamp": [0.0, 1.0, 2.0],
            "x": [100, 200, 300],
            "y": [400, 500, 600],
            "subject": ["s1"] * 3,
            "session": ["x1"] * 3,
        }
    )
    adapted = adapt_mouse_events(source)
    assert adapted["normalized_x"].between(0, 1).all()
    assert adapted["normalized_y"].between(0, 1).all()
    assert list(adapted.columns) == MOUSE_COLUMNS


def test_mouse_adapter_drops_sensitive_ui_metadata() -> None:
    source = pd.DataFrame(
        {
            "timestamp": [0.0],
            "x": [1],
            "y": [1],
            "subject": ["s1"],
            "session": ["x1"],
            "button_text": ["Delete shipment"],
            "css_selector": ["#danger"],
            "html": ["<button>"],
            "window_name": ["Admin"],
        }
    )
    adapted = adapt_mouse_events(source)
    assert not {"button_text", "css_selector", "html", "window_name"} & set(
        adapted.columns
    )
    assert adapted.loc[0, "event_type"] == "other"
    assert adapted.loc[0, "button_category"] == "none"


def test_cross_dataset_never_calibrates_on_test_split() -> None:
    plan = ExperimentPlan(
        experiment_id="invalid",
        family="pad",
        training=(DatasetUse("a", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("b", "test"),),
        test=(DatasetUse("b", "test"),),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=(),
    )
    with pytest.raises(ExperimentGateError, match="calibrar"):
        validate_experiment_plan(plan)


def test_fine_tuning_uses_only_own_train() -> None:
    plan = ExperimentPlan(
        experiment_id="invalid",
        family="pad",
        training=(DatasetUse("public", "train"),),
        fine_tuning=(DatasetUse("own_pad", "validation"),),
        validation=(DatasetUse("own_pad", "validation"),),
        test=(),
        calibration_source="validation",
        selection_source="validation",
        protocol_notes=(),
    )
    with pytest.raises(ExperimentGateError, match="Fine-tuning"):
        validate_experiment_plan(plan)


def test_model_selection_must_use_validation() -> None:
    plan = ExperimentPlan(
        experiment_id="invalid",
        family="pad",
        training=(DatasetUse("public", "train"),),
        fine_tuning=(),
        validation=(DatasetUse("public", "validation"),),
        test=(),
        calibration_source="validation",
        selection_source="test",  # type: ignore[arg-type]
        protocol_notes=(),
    )
    with pytest.raises(ExperimentGateError, match="selección"):
        validate_experiment_plan(plan)


def test_own_frozen_test_stays_blocked() -> None:
    own_only = next(plan for plan in PAD_PLANS if plan.experiment_id == "PAD-B-own-only")
    with pytest.raises(ExperimentGateError, match="congelado"):
        validate_experiment_plan(own_only, frozen_test_approval=False)


def test_pad_metrics_are_calculated() -> None:
    metrics = pad_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], threshold=0.5)
    assert metrics["accuracy"] == 1.0
    assert metrics["ACER"] == 0.0
    assert metrics["EER"] == 0.0


def test_behavioral_metrics_are_calculated() -> None:
    metrics = behavioral_metrics(
        [1, 1, 0, 0], [0.1, 0.2, 0.8, 0.9], threshold=0.5
    )
    assert metrics["accuracy"] == 1.0
    assert metrics["EER"] == 0.0


def test_comparison_requires_protocol_notes(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    (results / "behavioral-invalid.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "experiment_id": "x",
                "artifact_paths": ["artifact.bin"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="protocolo"):
        build_comparison(
            family="behavioral",
            results_dir=results,
            output_path=tmp_path / "comparison.parquet",
        )


def test_readiness_report_is_generated_without_overclaiming(tmp_path: Path) -> None:
    target = tmp_path / "production_readiness_report.md"
    generate_readiness_report(
        registry_path=REGISTRY,
        pad_comparison=tmp_path / "missing-pad.parquet",
        behavioral_comparison=tmp_path / "missing-behavioral.parquet",
        output_path=target,
    )
    report = target.read_text(encoding="utf-8")
    assert "**Estado: `not_ready`**" in report
    assert "no garantiza ausencia de fallos" in report


@pytest.mark.parametrize("value", [0.9, 5.1])
def test_frame_rate_must_remain_between_one_and_five(value: float) -> None:
    with pytest.raises(ValueError, match="entre 1 y 5"):
        validate_frames_per_second(value)


def test_missing_pad_labels_are_null_and_rejected_not_inferred() -> None:
    manifest = build_external_pad_manifest(
        pd.DataFrame(
            [
                _pad_row(
                    presentation_label=None,
                    attack_type=None,
                    quality_status=None,
                )
            ]
        )
    )
    assert list(manifest.columns) == PAD_MANIFEST_COLUMNS
    assert pd.isna(manifest.loc[0, "presentation_label"])
    assert manifest.loc[0, "quality_status"] == "rejected"
    assert "missing_presentation_label" in manifest.loc[0, "rejection_reasons"]


def test_absolute_paths_are_rejected_from_pad_manifest(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="relativo"):
        build_external_pad_manifest(
            pd.DataFrame([_pad_row(file_path=str((tmp_path / "frame.jpg").resolve()))])
        )


def test_unknown_project_split_is_rejected() -> None:
    with pytest.raises(ValueError, match="Splits de proyecto inválidos"):
        build_external_pad_manifest(
            pd.DataFrame([_pad_row(split_project="random-image-split")])
        )


@pytest.mark.parametrize(
    "dataset_id",
    [
        "oulu_npu",
        "replay_attack",
        "replay_mobile",
        "celeba_spoof",
        "siw",
        "siw_mv2",
        "casia_surf_cefa",
        "cmu_keystroke",
        "aalto_keystrokes",
        "balabit_mouse",
        "behaviour_biometrics",
    ],
)
def test_access_instructions_are_generated_for_unapproved_dataset(
    dataset_id: str, tmp_path: Path
) -> None:
    """Todo dataset no aprobado debe generar instrucciones, no descargar."""
    target = tmp_path / f"{dataset_id}-access-instructions.md"
    write_access_instructions(dataset_id, REGISTRY, target)
    content = target.read_text(encoding="utf-8")
    assert dataset_id in content or "Acceso" in content
    assert "https://" in content  # contiene la URL oficial
    # Los datasets con acuerdo deben mencionar que hay que guardar evidencia
    entry = load_registry(REGISTRY).get(dataset_id)
    if entry.agreement_required:
        normalized = content.casefold()
        assert (
            "aprobado" in normalized
            or "aprobacion" in normalized
            or "acuerdo" in normalized
            or "aceptaci" in normalized
        )


def test_agreement_required_datasets_are_not_auto_downloaded() -> None:
    """Los datasets que requieren acuerdo no deben tener download_url ni hosts aprobados."""
    registry = load_registry(REGISTRY)
    for entry in registry.datasets:
        if entry.agreement_required:
            assert entry.download_url is None or entry.status != "approved"
            assert entry.approved_download_hosts == []


def test_pending_review_datasets_have_no_download_url() -> None:
    """Los datasets pending_review no deben tener download_url configurado."""
    registry = load_registry(REGISTRY)
    for entry in registry.datasets:
        if entry.status == "pending_review":
            assert entry.download_url is None


def test_celeba_spoof_is_non_commercial_only() -> None:
    """CelebA-Spoof debe estar marcado como no comercial y sin redistribución."""
    entry = load_registry(REGISTRY).get("celeba_spoof")
    assert entry.commercial_use_allowed is False
    assert entry.redistribution_allowed is False
    assert "noncommercial" in entry.intended_use or "non-commercial" in str(entry.license_name).casefold()
