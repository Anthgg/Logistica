import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.behavioral.behavioral_manifest import build_behavioral_manifest
from src.behavioral.combined_features import extract_combined_features
from src.behavioral.event_loader import (
    capture_file_path,
    create_database_engine,
    iter_batch_rows,
    load_behavioral_batches,
    load_captures,
    load_sessions,
)
from src.behavioral.event_validator import validate_batch
from src.behavioral.window_builder import build_windows, flatten_valid_batches
from src.common.config import PreparationConfig, load_config
from src.common.hashing import (
    canonical_json_hash,
    directory_fingerprint,
    sha256_file,
)
from src.common.logging import configure_logging, safe_database_description
from src.common.paths import PROJECT_ROOT
from src.datasets.dataset_version import (
    build_dataset_metadata,
    write_dataset_metadata,
)
from src.datasets.freeze_test_set import FrozenTestSetExistsError, freeze_test_set
from src.datasets.leakage_checker import check_manifest_collection
from src.datasets.manifest_builder import write_manifest
from src.datasets.split_strategy import (
    assign_group_splits,
    assign_pad_splits,
)
from src.facial.duplicate_detector import DuplicateDetector
from src.facial.facial_manifest import build_facial_identity_manifest
from src.facial.pad_manifest import build_pad_manifest
from src.facial.quality_analyzer import FaceQualityAnalyzer
from src.pilot.pilot_summary import build_session_summary
from src.pilot.readiness import evaluate_readiness
from src.pilot.session_audit import audit_sessions, write_raw_audit
from src.reports.pilot_report import build_pilot_report, write_pilot_report
from src.reports.quality_charts import generate_quality_charts
from src.reports.quality_tables import (
    behavioral_quality_table,
    facial_quality_table,
    feature_statistics_table,
    split_distribution_table,
    write_quality_tables,
)

STAGES = (
    "audit",
    "face_quality",
    "event_validation",
    "windows",
    "features",
    "manifests",
    "splits",
    "freeze",
    "report",
)


@dataclass(frozen=True)
class PipelineResult:
    dataset_version: str
    readiness_status: str
    participants: int
    sessions: int
    face_captures: int
    behavioral_batches: int
    windows: int
    report_path: Path
    readiness_path: Path
    dry_run: bool


def _stage_enabled(stop_after: str, stage: str) -> bool:
    return STAGES.index(stage) <= STAGES.index(stop_after)


def _override_dataset_version(
    config: PreparationConfig, dataset_version: str | None
) -> PreparationConfig:
    if not dataset_version:
        return config
    return config.model_copy(
        update={
            "pipeline": config.pipeline.model_copy(
                update={"dataset_version": dataset_version}
            )
        }
    )


def _analyze_faces(
    captures: pd.DataFrame,
    config: PreparationConfig,
    capture_root: Path,
) -> pd.DataFrame:
    columns = [
        "participant_id",
        "session_id",
        "capture_id",
        "quality_status",
        "rejection_reasons",
    ]
    if captures.empty:
        return pd.DataFrame(columns=columns)
    analyzer = FaceQualityAnalyzer(config.face_quality)
    duplicates = DuplicateDetector()
    previous_by_session: dict[str, object] = {}
    rows: list[dict[str, object]] = []
    ordered = captures.sort_values(
        ["session_id", "captured_at", "sequence_number"], kind="stable"
    )
    for capture in ordered.to_dict(orient="records"):
        session_id = str(capture["session_id"])
        capture_id = str(capture["capture_id"])
        checksum_value = capture.get("checksum")
        checksum = (
            str(checksum_value)
            if checksum_value is not None and pd.notna(checksum_value)
            else ""
        )
        try:
            source = capture_file_path(capture_root, str(capture["storage_path"]))
        except ValueError:
            source = capture_root / "__invalid_storage_path__"
        is_duplicate = duplicates.add(capture_id, checksum) if checksum else False
        metrics = analyzer.analyze(
            source,
            expected_checksum=checksum or None,
            declared_width=(
                int(capture["width"]) if pd.notna(capture.get("width")) else None
            ),
            declared_height=(
                int(capture["height"]) if pd.notna(capture.get("height")) else None
            ),
            declared_file_size=(
                int(capture["file_size"])
                if pd.notna(capture.get("file_size"))
                else None
            ),
            visibility_state=str(capture.get("visibility_state") or ""),
            captured_at=capture.get("captured_at"),
            previous_captured_at=previous_by_session.get(session_id),
            is_duplicate=is_duplicate,
        )
        previous_by_session[session_id] = capture.get("captured_at")
        rows.append(
            {
                "participant_id": str(capture["participant_id"]),
                "session_id": session_id,
                "capture_id": capture_id,
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def _validate_batches(
    batches: pd.DataFrame, config: PreparationConfig
) -> pd.DataFrame:
    columns = [
        "participant_id",
        "session_id",
        "scenario",
        "session_started_at",
        "session_ended_at",
        "identity_label",
        "sample_role",
        "operator_change_at",
        "presentation_label",
        "attack_type",
        "source_device",
        "pad_source_id",
        "annotation_status",
        "record_id",
        "batch_id",
        "sequence_number",
        "valid",
        "rejection_reasons",
        "keyboard_event_count",
        "mouse_event_count",
        "events",
        "checksum",
    ]
    seen_batch_ids: set[str] = set()
    seen_batch_sequences: set[tuple[str, int]] = set()
    seen_event_hashes: set[str] = set()
    rows: list[dict[str, object]] = []
    for batch in iter_batch_rows(batches):
        result = validate_batch(
            batch,
            config.behavioral,
            seen_batch_ids=seen_batch_ids,
            seen_batch_sequences=seen_batch_sequences,
            seen_event_hashes=seen_event_hashes,
        )
        rows.append(
            {
                "participant_id": str(batch["participant_id"]),
                "session_id": str(batch["session_id"]),
                "scenario": str(batch["scenario"]),
                "session_started_at": batch["session_started_at"],
                "session_ended_at": batch["session_ended_at"],
                "identity_label": batch.get("identity_label"),
                "sample_role": batch.get("sample_role"),
                "operator_change_at": batch.get("operator_change_at"),
                "presentation_label": batch.get("presentation_label"),
                "attack_type": batch.get("attack_type"),
                "source_device": batch.get("source_device"),
                "pad_source_id": batch.get("pad_source_id"),
                "annotation_status": batch.get("annotation_status"),
                "record_id": str(batch["record_id"]),
                "batch_id": str(batch["batch_id"]),
                "sequence_number": int(batch["sequence_number"]),
                "valid": result.valid,
                "rejection_reasons": result.rejection_reasons,
                "keyboard_event_count": result.keyboard_event_count,
                "mouse_event_count": result.mouse_event_count,
                "events": result.events,
                "checksum": str(batch.get("checksum") or ""),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _write_interim(
    *,
    config: PreparationConfig,
    face_quality: pd.DataFrame,
    validated_batches: pd.DataFrame,
    windows: pd.DataFrame,
    features: pd.DataFrame,
    stop_after: str,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    paths = config.pipeline.paths
    if _stage_enabled(stop_after, "face_quality"):
        face_status = face_quality.get(
            "quality_status", pd.Series(index=face_quality.index, dtype=str)
        )
        face_quality[face_status == "accepted"].to_parquet(
            paths.interim / "accepted_faces" / "index.parquet", index=False
        )
        face_quality[face_status != "accepted"].to_parquet(
            paths.interim / "rejected_faces" / "index.parquet", index=False
        )
        face_quality.to_parquet(
            paths.processed / "facial" / "facial_quality.parquet", index=False
        )
    if _stage_enabled(stop_after, "event_validation"):
        safe_batches = validated_batches.copy()
        if "events" in safe_batches:
            safe_batches["events_json"] = safe_batches["events"].apply(
                lambda value: json.dumps(
                    value if isinstance(value, list) else [],
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )
            )
            safe_batches = safe_batches.drop(columns=["events"])
        safe_batches.to_parquet(
            paths.interim / "validated_events" / "validated_batches.parquet",
            index=False,
        )
    if _stage_enabled(stop_after, "windows"):
        safe_windows = windows.copy()
        if "events" in safe_windows:
            safe_windows["events_json"] = safe_windows["events"].apply(
                lambda value: json.dumps(
                    value if isinstance(value, list) else [],
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )
            )
            safe_windows = safe_windows.drop(columns=["events"])
        safe_windows.to_parquet(
            paths.interim / "behavioral_windows" / "windows.parquet", index=False
        )
    if _stage_enabled(stop_after, "features"):
        features.to_parquet(
            paths.processed / "behavioral" / "behavioral_features.parquet",
            index=False,
        )


def _split_manifests(
    identity: pd.DataFrame,
    pad: pd.DataFrame,
    behavioral: pd.DataFrame,
    config: PreparationConfig,
) -> dict[str, pd.DataFrame]:
    ratios = config.pipeline.split_ratios
    seed = config.protocol.random_seed
    split_identity = assign_group_splits(
        identity,
        group_column="session_id",
        ratios=ratios,
        random_seed=seed,
    )
    split_pad = assign_pad_splits(pad, ratios=ratios, random_seed=seed)
    split_behavioral = assign_group_splits(
        behavioral,
        group_column="segment_id",
        ratios=ratios,
        random_seed=seed,
    )
    return {
        "facial_identity": split_identity,
        "facial_pad": split_pad,
        "behavioral": split_behavioral,
    }


def _write_splits(
    manifests: dict[str, pd.DataFrame],
    config: PreparationConfig,
    *,
    dry_run: bool,
) -> Path:
    target = config.pipeline.paths.root / config.pipeline.dataset_splits
    summary = split_distribution_table(manifests)
    payload = {
        "dataset_version": config.pipeline.dataset_version,
        "random_seed": config.protocol.random_seed,
        "ratios": config.pipeline.split_ratios.model_dump(),
        "strategies": {
            "facial_identity": "participant/session",
            "facial_pad": "participant/session/device/source",
            "behavioral": "participant/segment",
        },
        "counts": summary.to_dict(orient="records"),
    }
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return target


def _rejection_table(
    facial: pd.DataFrame, behavioral: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for source, table in (("facial", facial), ("behavioral", behavioral)):
        if table.empty:
            continue
        rejected = table[
            (table.get("quality_status") == "rejected")
            & (table.get("reason") != "ALL")
        ]
        for row in rejected.to_dict(orient="records"):
            rows.append(
                {
                    "source": source,
                    "stage": row.get("stage"),
                    "reason": row.get("reason"),
                    "count": int(row.get("count") or 0),
                }
            )
    return pd.DataFrame(rows, columns=["source", "stage", "reason", "count"])


def run_preparation_pipeline(
    *,
    config_path: str | Path | None = None,
    dataset_version: str | None = None,
    participant_id: str | None = None,
    session_id: str | None = None,
    freeze_test: bool = False,
    force: bool = False,
    force_reason: str | None = None,
    dry_run: bool = False,
    stop_after: str = "report",
) -> PipelineResult:
    if stop_after not in STAGES:
        raise ValueError(f"Etapa no válida: {stop_after}.")
    if force and not freeze_test:
        raise ValueError("--force solo puede usarse junto con --freeze-test.")
    if force and (not force_reason or len(force_reason.strip()) < 5):
        raise ValueError("--force requiere --force-reason.")
    started = time.monotonic()
    config = _override_dataset_version(load_config(config_path), dataset_version)
    paths = config.pipeline.paths
    report_root = paths.root / config.pipeline.reports_root
    frozen_target = paths.root / config.pipeline.frozen_test_manifest
    frozen_companions = (
        frozen_target,
        frozen_target.with_suffix(".sha256"),
        frozen_target.with_name("frozen_test_metadata.json"),
    )
    if (
        freeze_test
        and not dry_run
        and not force
        and any(path.exists() for path in frozen_companions)
    ):
        raise FrozenTestSetExistsError(
            "El conjunto de prueba ya está congelado. Use --force con motivo."
        )
    logger = configure_logging(None if dry_run else report_root / "pipeline.log")
    logger.info(
        "Inicio dataset=%s protocol=%s dry_run=%s",
        config.pipeline.dataset_version,
        config.protocol.protocol_version,
        dry_run,
    )
    if not dry_run:
        paths.ensure_output_layout()
    raw_before = directory_fingerprint(paths.raw)
    settings = config.database_settings()
    logger.info(
        "Conexión=%s", safe_database_description(settings.DATABASE_URL)
    )
    engine = create_database_engine(config)
    try:
        sessions = load_sessions(
            engine,
            participant_id=participant_id,
            session_id=session_id,
            consent_version=config.protocol.consent_version,
        )
        captures = load_captures(
            engine, participant_id=participant_id, session_id=session_id
        )
        batches = load_behavioral_batches(
            engine, participant_id=participant_id, session_id=session_id
        )
    finally:
        engine.dispose()
    capture_root = Path(config.pipeline.capture_storage_root)
    if not capture_root.is_absolute():
        capture_root = (config.source_path.parent / capture_root).resolve()
    audit = audit_sessions(sessions, captures, batches, config, capture_root)
    if _stage_enabled(stop_after, "audit"):
        write_raw_audit(audit, report_root, dry_run=dry_run)
    face_quality = (
        _analyze_faces(captures, config, capture_root)
        if _stage_enabled(stop_after, "face_quality")
        else pd.DataFrame()
    )
    validated_batches = (
        _validate_batches(batches, config)
        if _stage_enabled(stop_after, "event_validation")
        else pd.DataFrame()
    )
    events = (
        flatten_valid_batches(validated_batches)
        if _stage_enabled(stop_after, "windows")
        else pd.DataFrame()
    )
    windows = (
        build_windows(events, config.behavioral, config.protocol)
        if _stage_enabled(stop_after, "windows")
        else pd.DataFrame()
    )
    features = (
        extract_combined_features(windows, config)
        if _stage_enabled(stop_after, "features")
        else pd.DataFrame()
    )
    identity = (
        build_facial_identity_manifest(captures, face_quality, config, capture_root)
        if _stage_enabled(stop_after, "manifests")
        else pd.DataFrame()
    )
    pad = (
        build_pad_manifest(captures, face_quality, config, capture_root)
        if _stage_enabled(stop_after, "manifests")
        else pd.DataFrame()
    )
    behavioral = (
        build_behavioral_manifest(features)
        if _stage_enabled(stop_after, "manifests")
        else pd.DataFrame()
    )
    manifests = (
        _split_manifests(identity, pad, behavioral, config)
        if _stage_enabled(stop_after, "splits")
        else {
            "facial_identity": identity,
            "facial_pad": pad,
            "behavioral": behavioral,
        }
    )
    leakage_findings = (
        check_manifest_collection(list(manifests.values()), raise_on_critical=True)
        if _stage_enabled(stop_after, "splits")
        else []
    )
    if _stage_enabled(stop_after, "manifests"):
        targets = {
            "facial_identity": paths.root
            / config.pipeline.facial_identity_manifest,
            "facial_pad": paths.root / config.pipeline.facial_pad_manifest,
            "behavioral": paths.root / config.pipeline.behavioral_manifest,
        }
        for name, target in targets.items():
            write_manifest(
                manifests[name],
                target,
                csv_copy=config.pipeline.write_csv_copies,
                dry_run=dry_run,
            )
    if _stage_enabled(stop_after, "splits"):
        _write_splits(manifests, config, dry_run=dry_run)
    _write_interim(
        config=config,
        face_quality=face_quality,
        validated_batches=validated_batches,
        windows=windows,
        features=features,
        stop_after=stop_after,
        dry_run=dry_run,
    )
    if (
        _stage_enabled(stop_after, "freeze")
        and freeze_test
        and not dry_run
        and any(
            not frame.empty and "split" in frame and (frame["split"] == "test").any()
            for frame in manifests.values()
        )
    ):
        freeze_test_set(
            manifests,
            frozen_target,
            dataset_version=config.pipeline.dataset_version,
            protocol_version=config.protocol.protocol_version,
            force=force,
            force_reason=force_reason,
        )
    raw_after = directory_fingerprint(paths.raw)
    raw_unchanged = raw_before == raw_after
    if not raw_unchanged:
        raise RuntimeError("data/raw fue alterado durante la ejecución.")
    session_summary = build_session_summary(audit)
    facial_table = facial_quality_table(face_quality)
    behavioral_table = behavioral_quality_table(validated_batches, windows)
    split_table = split_distribution_table(manifests)
    feature_statistics = feature_statistics_table(features)
    readiness = evaluate_readiness(
        config=config,
        audit=audit,
        face_quality=face_quality,
        validated_batches=validated_batches,
        windows=windows,
        features=features,
        manifests=manifests,
        leakage_findings=leakage_findings,
        frozen_test_exists=frozen_target.is_file(),
        freeze_requested=freeze_test,
        raw_unchanged=raw_unchanged,
    )
    report = build_pilot_report(
        dataset_version=config.pipeline.dataset_version,
        protocol_version=config.protocol.protocol_version,
        session_summary=session_summary,
        facial_table=facial_table,
        behavioral_table=behavioral_table,
        split_table=split_table,
        readiness=readiness,
        audit=audit,
        validated_batches=validated_batches,
        windows=windows,
    )
    report_path, readiness_path = write_pilot_report(
        report,
        readiness,
        report_root,
        dry_run=dry_run or not _stage_enabled(stop_after, "report"),
    )
    if _stage_enabled(stop_after, "report"):
        rejection_table = _rejection_table(facial_table, behavioral_table)
        write_quality_tables(
            {
                "pilot_session_summary": session_summary,
                "facial_quality_summary": facial_table,
                "behavioral_quality_summary": behavioral_table,
                "dataset_split_summary": split_table,
                "rejection_reasons": rejection_table,
                "behavioral_feature_statistics": feature_statistics,
            },
            report_root,
            dry_run=dry_run,
        )
        generate_quality_charts(
            facial_table,
            behavioral_table,
            split_table,
            report_root,
            audit=audit,
            face_quality=face_quality,
            windows=windows,
            dry_run=dry_run,
        )
    metadata = build_dataset_metadata(
        dataset_version=config.pipeline.dataset_version,
        protocol_version=config.protocol.protocol_version,
        config_values={
            "pipeline": config.pipeline.model_dump(mode="json"),
            "protocol": config.protocol.model_dump(mode="json"),
            "face_quality": config.face_quality.model_dump(mode="json"),
            "behavioral": config.behavioral.model_dump(mode="json"),
        },
        manifests=manifests,
        project_root=PROJECT_ROOT,
    )
    metadata["pilot"] = {
        "participants": int(sessions["participant_id"].nunique())
        if not sessions.empty
        else 0,
        "sessions": len(sessions),
        "captures": len(captures),
        "behavioral_batches": len(batches),
        "raw_files": len(raw_after),
    }
    metadata["raw_fingerprint_hash"] = canonical_json_hash(raw_after)
    manifest_targets = {
        "facial_identity": paths.root / config.pipeline.facial_identity_manifest,
        "facial_pad": paths.root / config.pipeline.facial_pad_manifest,
        "behavioral": paths.root / config.pipeline.behavioral_manifest,
        "dataset_splits": paths.root / config.pipeline.dataset_splits,
    }
    metadata["manifest_hashes"] = {
        name: sha256_file(target)
        for name, target in manifest_targets.items()
        if target.is_file()
    }
    metadata.pop("metadata_hash", None)
    metadata["metadata_hash"] = canonical_json_hash(metadata)
    if not dry_run and _stage_enabled(stop_after, "manifests"):
        write_dataset_metadata(
            metadata, paths.manifests / "dataset_metadata.json"
        )
    logger.info(
        "Fin status=%s participants=%d sessions=%d captures=%d batches=%d "
        "windows=%d duration_seconds=%.3f",
        readiness["status"],
        int(sessions["participant_id"].nunique()) if not sessions.empty else 0,
        len(sessions),
        len(captures),
        len(batches),
        len(windows),
        time.monotonic() - started,
    )
    return PipelineResult(
        dataset_version=config.pipeline.dataset_version,
        readiness_status=str(readiness["status"]),
        participants=(
            int(sessions["participant_id"].nunique()) if not sessions.empty else 0
        ),
        sessions=len(sessions),
        face_captures=len(captures),
        behavioral_batches=len(batches),
        windows=len(windows),
        report_path=report_path,
        readiness_path=readiness_path,
        dry_run=dry_run,
    )
