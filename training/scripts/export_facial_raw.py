import argparse
import json
from dataclasses import asdict
from pathlib import Path

import _bootstrap  # noqa: F401

from src.behavioral.event_loader import create_database_engine, load_captures
from src.common.config import load_config
from src.common.paths import resolve_from_training
from src.facial.raw_exporter import export_facial_raw


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Exporta capturas persistentes verificadas hacia data/raw/facial "
            "sin sobrescribir originales."
        )
    )
    parser.add_argument("--config", help="Directorio o archivo de configuración.")
    parser.add_argument("--bucket", help="Sobrescribe capture_bucket.")
    parser.add_argument("--participant-id", help="UUID seudonimizado.")
    parser.add_argument("--session-id", help="UUID de sesión experimental.")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    config = load_config(arguments.config)
    bucket = arguments.bucket or config.pipeline.capture_bucket
    if not bucket:
        parser.error("Configure capture_bucket o use --bucket.")
    raw_root = resolve_from_training(config.pipeline.capture_storage_root)
    paths = config.pipeline.paths
    engine = create_database_engine(config)
    try:
        captures = load_captures(
            engine,
            participant_id=arguments.participant_id,
            session_id=arguments.session_id,
        )
    finally:
        engine.dispose()
    result = export_facial_raw(
        captures,
        bucket=bucket,
        raw_root=raw_root,
        staging_root=paths.interim / "facial_export_staging",
        report_path=paths.reports / "facial_raw_export.json",
        dry_run=arguments.dry_run,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
