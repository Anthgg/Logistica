from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING_ROOT = PROJECT_ROOT / "training"
if str(TRAINING_ROOT) not in sys.path:
    sys.path.insert(0, str(TRAINING_ROOT))

from src.common.serialization import write_json_atomic
from src.common.hashing import sha256_file
from src.datasets.manifest_builder import write_manifest
from src.external_data.adapters import (
    KEYBOARD_COLUMNS,
    MOUSE_COLUMNS,
    adapt_cmu_wide,
    adapt_keystroke_events,
    adapt_mouse_events,
    read_tabular,
)
from src.external_data.downloads import (
    download_audit_record,
    download_registered_dataset,
    write_access_instructions,
    write_download_audit,
)
from src.external_data.experiments import (
    PAD_PLANS,
    ExperimentGateError,
    assert_manifest_supports_plan,
    validate_experiment_plan,
    write_experiment_plans,
)
from src.external_data.frames import discover_videos, extract_video_frames
from src.external_data.manifests import (
    PAD_MANIFEST_COLUMNS,
    build_behavioral_manifest,
    write_external_pad_manifest,
)
from src.external_data.registry import (
    assert_license_ready,
    assert_raw_unchanged,
    load_registry,
    mark_dataset_downloaded,
    raw_snapshot,
    verify_registry_licenses,
    write_download_status,
)
from src.external_data.reporting import build_comparison, generate_readiness_report
from src.external_data.validation import validate_raw_directory, validation_payload

EXTERNAL_ROOT = PROJECT_ROOT / "external-data"
REGISTRY_PATH = EXTERNAL_ROOT / "registry" / "datasets.yaml"


def _read_frame(path: Path) -> pd.DataFrame:
    return read_tabular(path)


def _require_downloaded(dataset_id: str):
    entry = load_registry(REGISTRY_PATH).get(dataset_id)
    if entry.status != "downloaded":
        raise RuntimeError(
            f"{dataset_id}: status={entry.status}; se requiere status=downloaded."
        )
    assert_license_ready(entry, REGISTRY_PATH)
    return entry


def command_register(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    target = write_download_status(
        REGISTRY_PATH, EXTERNAL_ROOT / "registry" / "download_status.json"
    )
    manifest_schemas = {
        "external_pad_manifest.parquet": PAD_MANIFEST_COLUMNS,
        "external_keyboard_manifest.parquet": [
            "dataset_version",
            "source_dataset",
            "modality",
            *KEYBOARD_COLUMNS,
            "license_status",
        ],
        "external_mouse_manifest.parquet": [
            "dataset_version",
            "source_dataset",
            "modality",
            *MOUSE_COLUMNS,
            "license_status",
        ],
        "external_combined_manifest.parquet": [
            "dataset_version",
            "source_dataset",
            "modality",
            "subject_id",
            "session_id",
            "legitimate_label",
            "feature_path",
            "license_status",
        ],
    }
    initialized: list[str] = []
    for filename, columns in manifest_schemas.items():
        manifest_path = EXTERNAL_ROOT / "manifests" / filename
        if not manifest_path.exists():
            write_manifest(pd.DataFrame(columns=columns), manifest_path)
            initialized.append(str(manifest_path))
    if args.dataset:
        entry = registry.get(args.dataset)
        if entry.status != "approved":
            raise RuntimeError(
                f"{entry.dataset_id}: status={entry.status}; primero documente y apruebe."
            )
        assert_license_ready(entry, REGISTRY_PATH)
        if not args.manual_file or not args.expected_sha256:
            raise RuntimeError(
                "--manual-file y --expected-sha256 son obligatorios para registrar "
                "una entrega manual."
            )
        manual_file = Path(args.manual_file).resolve()
        manual_file.relative_to((PROJECT_ROOT / entry.storage_path).resolve())
        if not manual_file.is_file():
            raise RuntimeError(f"No existe el archivo manual: {manual_file}")
        actual_checksum = sha256_file(manual_file)
        if actual_checksum.casefold() != args.expected_sha256.casefold():
            raise RuntimeError(
                f"Checksum manual inválido: esperado={args.expected_sha256}, "
                f"real={actual_checksum}"
            )
        mark_dataset_downloaded(
            REGISTRY_PATH,
            dataset_id=entry.dataset_id,
            checksum=actual_checksum,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )
        target = write_download_status(
            REGISTRY_PATH, EXTERNAL_ROOT / "registry" / "download_status.json"
        )
    print(
        f"{len(registry.datasets)} datasets registrados; estado: {target}; "
        f"manifiestos inicializados: {len(initialized)}"
    )
    return 0


def command_verify(_: argparse.Namespace) -> int:
    results = verify_registry_licenses(REGISTRY_PATH)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    approved_failures = [
        result
        for result in results
        if not result["ready"]
        and load_registry(REGISTRY_PATH).get(str(result["dataset_id"])).status
        in {"approved", "downloaded"}
    ]
    return 1 if approved_failures else 0


def command_validate(args: argparse.Namespace) -> int:
    entry = load_registry(REGISTRY_PATH).get(args.dataset)
    result = validate_raw_directory(entry, PROJECT_ROOT)
    target = (
        EXTERNAL_ROOT
        / "interim"
        / "rejected"
        / f"{entry.dataset_id}-validation.json"
    )
    write_json_atomic(target, validation_payload(result))
    print(json.dumps(validation_payload(result), ensure_ascii=False, indent=2))
    return 0 if result.valid else 2


def command_download(args: argparse.Namespace) -> int:
    entry = load_registry(REGISTRY_PATH).get(args.dataset)
    if entry.status != "approved":
        target = (
            EXTERNAL_ROOT
            / "registry"
            / "licenses"
            / f"{entry.dataset_id}-access-instructions.md"
        )
        write_access_instructions(entry.dataset_id, REGISTRY_PATH, target)
        print(target.read_text(encoding="utf-8"))
        return 2
    if not args.expected_sha256:
        raise RuntimeError("--expected-sha256 es obligatorio para una descarga aprobada.")
    downloaded = download_registered_dataset(
        dataset_id=entry.dataset_id,
        registry_path=REGISTRY_PATH,
        project_root=PROJECT_ROOT,
        expected_sha256=args.expected_sha256,
    )
    audit = download_audit_record(entry.dataset_id, downloaded)
    mark_dataset_downloaded(
        REGISTRY_PATH,
        dataset_id=entry.dataset_id,
        checksum=audit["checksum"],
        downloaded_at=audit["downloaded_at"],
    )
    write_download_audit(
        audit,
        EXTERNAL_ROOT / "registry" / f"{entry.dataset_id}-download-audit.json",
    )
    write_download_status(
        REGISTRY_PATH, EXTERNAL_ROOT / "registry" / "download_status.json"
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


def command_extract(args: argparse.Namespace) -> int:
    entry = _require_downloaded(args.dataset)
    raw_dir = PROJECT_ROOT / entry.storage_path
    before = raw_snapshot(raw_dir)
    videos = discover_videos(raw_dir)
    if not videos:
        raise RuntimeError(f"No se encontraron videos en {raw_dir}.")
    frames = [
        extract_video_frames(
            video_path=video,
            raw_root=raw_dir,
            output_root=EXTERNAL_ROOT / "interim" / "pad_frames",
            source_dataset=entry.dataset_id,
            source_video_id=video.relative_to(raw_dir).with_suffix("").as_posix().replace("/", "__"),
            frames_per_second=args.frames_per_second,
        )
        for video in videos
    ]
    manifest = pd.concat(frames, ignore_index=True)
    target = EXTERNAL_ROOT / "interim" / "pad_frames" / f"{entry.dataset_id}-frames.parquet"
    write_manifest(manifest, target, csv_copy=True)
    assert_raw_unchanged(before, raw_dir)
    print(f"{len(manifest)} frames trazables escritos en {target}")
    return 0


def command_build_manifests(args: argparse.Namespace) -> int:
    source = _read_frame(Path(args.input))
    if args.modality == "pad":
        target = EXTERNAL_ROOT / "manifests" / "external_pad_manifest.parquet"
        write_external_pad_manifest(source, target, csv_copy=True)
    else:
        source_dataset = args.dataset
        entry = load_registry(REGISTRY_PATH).get(source_dataset)
        adapted = build_behavioral_manifest(
            source,
            source_dataset=source_dataset,
            modality=args.modality,
            dataset_version=entry.version or "unknown",
            license_status=entry.status,
        )
        filename = {
            "keyboard": "external_keyboard_manifest.parquet",
            "mouse": "external_mouse_manifest.parquet",
            "combined": "external_combined_manifest.parquet",
        }[args.modality]
        target = EXTERNAL_ROOT / "manifests" / filename
        write_manifest(adapted, target, csv_copy=True)
    print(target)
    return 0


def command_adapt_keyboard(args: argparse.Namespace) -> int:
    entry = _require_downloaded(args.dataset)
    source = Path(args.input).resolve()
    raw_root = (PROJECT_ROOT / entry.storage_path).resolve()
    source.relative_to(raw_root)
    before = raw_snapshot(raw_root)
    frame = _read_frame(source)
    adapted = adapt_cmu_wide(frame) if args.cmu_wide else adapt_keystroke_events(frame)
    target = (
        EXTERNAL_ROOT / "processed" / "keyboard" / f"{entry.dataset_id}-keyboard.parquet"
    )
    write_manifest(adapted, target, csv_copy=True)
    assert_raw_unchanged(before, raw_root)
    print(f"{len(adapted)} eventos sin texto escritos en {target}")
    return 0


def command_adapt_mouse(args: argparse.Namespace) -> int:
    entry = _require_downloaded(args.dataset)
    source = Path(args.input).resolve()
    raw_root = (PROJECT_ROOT / entry.storage_path).resolve()
    source.relative_to(raw_root)
    before = raw_snapshot(raw_root)
    adapted = adapt_mouse_events(_read_frame(source))
    target = EXTERNAL_ROOT / "processed" / "mouse" / f"{entry.dataset_id}-mouse.parquet"
    write_manifest(adapted, target, csv_copy=True)
    assert_raw_unchanged(before, raw_root)
    print(f"{len(adapted)} eventos normalizados escritos en {target}")
    return 0


def command_run_pad(_: argparse.Namespace) -> int:
    target = EXTERNAL_ROOT / "experiments" / "pad-experiment-plans.json"
    write_experiment_plans(target, family="pad")
    manifest_path = EXTERNAL_ROOT / "manifests" / "external_pad_manifest.parquet"
    runnable: list[str] = []
    blocked: dict[str, str] = {}
    if manifest_path.is_file():
        manifest = pd.read_parquet(manifest_path)
        for plan in PAD_PLANS:
            try:
                validate_experiment_plan(plan, frozen_test_approval=False)
                assert_manifest_supports_plan(manifest, plan)
            except ExperimentGateError as exc:
                blocked[plan.experiment_id] = str(exc)
            else:
                runnable.append(plan.experiment_id)
    else:
        blocked = {
            plan.experiment_id: "external_pad_manifest_missing" for plan in PAD_PLANS
        }
    print(
        json.dumps(
            {"plans": str(target), "runnable": runnable, "blocked": blocked},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_run_behavioral(_: argparse.Namespace) -> int:
    target = EXTERNAL_ROOT / "experiments" / "behavioral-experiment-plans.json"
    write_experiment_plans(target, family="behavioral")
    print(target)
    return 0


def command_compare(_: argparse.Namespace) -> int:
    results = EXTERNAL_ROOT / "experiments" / "results"
    pad = build_comparison(
        family="pad",
        results_dir=results,
        output_path=EXTERNAL_ROOT / "manifests" / "pad_training_comparison.parquet",
    )
    behavioral = build_comparison(
        family="behavioral",
        results_dir=results,
        output_path=EXTERNAL_ROOT
        / "manifests"
        / "behavioral_external_comparison.parquet",
    )
    print(f"PAD: {pad}\nConductual: {behavioral}")
    return 0


def command_readiness(_: argparse.Namespace) -> int:
    target = EXTERNAL_ROOT / "production_readiness_report.md"
    generate_readiness_report(
        registry_path=REGISTRY_PATH,
        pad_comparison=EXTERNAL_ROOT / "manifests" / "pad_training_comparison.parquet",
        behavioral_comparison=EXTERNAL_ROOT
        / "manifests"
        / "behavioral_external_comparison.parquet",
        output_path=target,
        frozen_test_consumed=False,
    )
    print(target)
    return 0


def build_parser(command: str, fixed_dataset: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AndesLog Fase 7.5")
    if command == "register":
        parser.add_argument("--dataset")
        parser.add_argument("--manual-file")
        parser.add_argument("--expected-sha256")
    elif command == "download":
        parser.add_argument("--expected-sha256")
        parser.set_defaults(dataset=fixed_dataset)
    elif command == "validate":
        parser.add_argument("dataset")
    elif command == "extract":
        parser.add_argument("dataset")
        parser.add_argument("--frames-per-second", type=float, default=2.0)
    elif command == "build":
        parser.add_argument("--input", required=True)
        parser.add_argument(
            "--modality", choices=["pad", "keyboard", "mouse", "combined"], required=True
        )
        parser.add_argument("--dataset", default="")
    elif command in {"adapt-keyboard", "adapt-mouse"}:
        parser.add_argument("dataset")
        parser.add_argument("--input", required=True)
        if command == "adapt-keyboard":
            parser.add_argument("--cmu-wide", action="store_true")
    return parser


COMMANDS = {
    "register": command_register,
    "verify": command_verify,
    "validate": command_validate,
    "download": command_download,
    "extract": command_extract,
    "build": command_build_manifests,
    "adapt-keyboard": command_adapt_keyboard,
    "adapt-mouse": command_adapt_mouse,
    "run-pad": command_run_pad,
    "run-behavioral": command_run_behavioral,
    "compare": command_compare,
    "readiness": command_readiness,
}


def run(command: str, fixed_dataset: str | None = None) -> None:
    parser = build_parser(command, fixed_dataset)
    args = parser.parse_args()
    raise SystemExit(COMMANDS[command](args))
