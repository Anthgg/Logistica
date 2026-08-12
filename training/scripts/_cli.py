import argparse
import json
from dataclasses import asdict

import _bootstrap  # noqa: F401

from src.pipeline import run_preparation_pipeline


def parser_for(description: str, *, supports_freeze: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", help="Directorio o archivo dentro de configs.")
    parser.add_argument("--dataset-version", help="Sobrescribe dataset_version.")
    parser.add_argument("--participant-id", help="UUID seudonimizado del participante.")
    parser.add_argument("--session-id", help="UUID de la sesión experimental.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida sin escribir salidas finales.",
    )
    if supports_freeze:
        parser.add_argument(
            "--freeze-test",
            action="store_true",
            help="Congela los registros asignados a test.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite reemplazar un test congelado.",
        )
        parser.add_argument(
            "--force-reason",
            help="Motivo auditable requerido cuando se usa --force.",
        )
    return parser


def run_stage(
    *,
    description: str,
    stop_after: str,
    freeze_by_default: bool = False,
    full_pipeline: bool = False,
) -> None:
    parser = parser_for(
        description, supports_freeze=freeze_by_default or full_pipeline
    )
    arguments = parser.parse_args()
    requested_freeze = (
        freeze_by_default or bool(getattr(arguments, "freeze_test", False))
    )
    result = run_preparation_pipeline(
        config_path=arguments.config,
        dataset_version=arguments.dataset_version,
        participant_id=arguments.participant_id,
        session_id=arguments.session_id,
        freeze_test=requested_freeze,
        force=bool(getattr(arguments, "force", False)),
        force_reason=getattr(arguments, "force_reason", None),
        dry_run=arguments.dry_run,
        stop_after=stop_after,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))
