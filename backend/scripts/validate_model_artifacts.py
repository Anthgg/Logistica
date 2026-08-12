import argparse

from _phase9_common import BACKEND_ROOT

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.services.model_loader_service import ModelLoaderService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida y carga artefactos candidatos sin inferir test."
    )
    parser.parse_args()
    strict = settings.model_copy(
        update={
            "MODEL_STRICT_CHECKSUM": True,
            "REQUIRE_ALL_MODELS": True,
            "MODEL_LOAD_ON_STARTUP": True,
            "BEHAVIORAL_MODEL_LOADING_MODE": "eager",
        }
    )
    loader = ModelLoaderService(strict)
    try:
        try:
            status = loader.startup()
        except ApplicationError as exc:
            raise SystemExit(
                f"Validación rechazada | code={exc.code}"
            ) from exc
    finally:
        loader.shutdown()
    print(
        "Artefactos validados | "
        f"status={status.global_status} "
        f"behavioral={status.behavioral_available} "
        f"root={BACKEND_ROOT.name}"
    )


if __name__ == "__main__":
    main()
