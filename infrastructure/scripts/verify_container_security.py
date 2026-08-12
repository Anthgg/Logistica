from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(command: Sequence[str]) -> str:
    result = subprocess.run(
        list(command),
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Falló {' '.join(command)}: {detail}")
    return result.stdout.strip()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} no es un objeto JSON")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RuntimeError(f"{label} no es una lista JSON")
    return value


def _assert_non_root(image: str) -> None:
    user = _run(
        ["docker", "image", "inspect", image, "--format", "{{.Config.User}}"]
    )
    if not user or user in {"0", "root", "0:0"}:
        raise RuntimeError(f"{image} se ejecuta como root ({user or 'vacío'})")


def _assert_image_contents(image: str, paths: Sequence[str]) -> None:
    assertions = " && ".join(f"test ! -e {path}" for path in paths)
    _run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "sh",
            image,
            "-c",
            assertions,
        ]
    )


def _assert_no_runtime_secrets(image: str) -> None:
    raw = _run(
        ["docker", "image", "inspect", image, "--format", "{{json .Config.Env}}"]
    )
    environment = json.loads(raw)
    for item in _sequence(environment, f"variables de {image}"):
        if not isinstance(item, str):
            continue
        name = item.partition("=")[0].upper()
        if name in {"SECRET_KEY", "POSTGRES_PASSWORD", "DATABASE_URL"}:
            raise RuntimeError(f"{image} contiene la variable sensible {name}")


def _assert_compose_contract() -> None:
    raw = _run(
        [
            "docker",
            "compose",
            "--profile",
            "evaluation",
            "config",
            "--format",
            "json",
        ]
    )
    compose = _mapping(json.loads(raw), "compose")
    services = _mapping(compose.get("services"), "services")

    for service_name in ("postgres", "backend", "frontend"):
        service = _mapping(services.get(service_name), service_name)
        if "healthcheck" not in service:
            raise RuntimeError(f"{service_name} no define healthcheck")

    evaluation = _mapping(services.get("evaluation"), "evaluation")
    profiles = _sequence(evaluation.get("profiles"), "profiles de evaluation")
    if "evaluation" not in profiles:
        raise RuntimeError("evaluation no está aislado detrás de su profile")

    expected_read_only = {
        "backend": {"/app/models", "/app/data/processed"},
        "evaluation": {
            "/workspace/models",
            "/workspace/data/manifests",
            "/workspace/data/processed",
        },
    }
    for service_name, targets in expected_read_only.items():
        service = _mapping(services.get(service_name), service_name)
        volumes = _sequence(service.get("volumes"), f"volúmenes de {service_name}")
        mounted_read_only: set[str] = set()
        for raw_volume in volumes:
            volume = _mapping(raw_volume, f"volumen de {service_name}")
            target = volume.get("target")
            if isinstance(target, str) and volume.get("read_only") is True:
                mounted_read_only.add(target)
        missing = targets - mounted_read_only
        if missing:
            raise RuntimeError(
                f"{service_name} tiene montajes que no son read-only: "
                + ", ".join(sorted(missing))
            )


def verify(backend: str, frontend: str, evaluation: str) -> None:
    images = (backend, frontend, evaluation)
    for image in images:
        _assert_non_root(image)
        _assert_no_runtime_secrets(image)

    _assert_image_contents(
        backend,
        (
            "/app/.env",
            "/app/data/raw",
            "/app/tests",
            "/app/.git",
        ),
    )
    _assert_image_contents(
        frontend,
        (
            "/app/.env",
            "/app/node_modules",
            "/usr/share/nginx/html/node_modules",
            "/usr/share/nginx/html/.git",
        ),
    )
    _assert_image_contents(
        evaluation,
        (
            "/workspace/.env",
            "/workspace/data/raw",
            "/workspace/data/manifests/frozen_test_manifest.parquet",
            "/workspace/models/registry/model_registry.json",
            "/workspace/.git",
        ),
    )
    _assert_compose_contract()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica usuario, contenido y montajes de las imágenes."
    )
    parser.add_argument(
        "--backend-image",
        default="continuous-authentication-backend:latest",
    )
    parser.add_argument(
        "--frontend-image",
        default="continuous-authentication-frontend:latest",
    )
    parser.add_argument(
        "--evaluation-image",
        default="continuous-authentication-evaluation:latest",
    )
    arguments = parser.parse_args()

    try:
        verify(
            arguments.backend_image,
            arguments.frontend_image,
            arguments.evaluation_image,
        )
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Contrato de seguridad de contenedores verificado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
