import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = (
    BACKEND_ROOT
    if BACKEND_ROOT.parent == Path(BACKEND_ROOT.anchor)
    else BACKEND_ROOT.parent
)
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise SystemExit(
            "Las rutas de Fase 9A deben permanecer dentro del proyecto."
        ) from exc
    return resolved


def reject_test_source(path: Path) -> None:
    tokens = {
        token
        for part in path.parts
        for token in part.casefold().replace("-", "_").split("_")
    }
    if "test" in tokens:
        raise SystemExit(
            "Fase 9A prohíbe usar una fuente identificada como test."
        )


def read_table(path: Path):
    try:
        import pandas
    except ImportError as exc:
        raise SystemExit(
            "Pandas y PyArrow son obligatorios para calibración."
        ) from exc
    if not path.is_file():
        raise SystemExit(f"No existe la fuente de validation: {path}")
    reject_test_source(path)
    try:
        if path.suffix.casefold() == ".parquet":
            return pandas.read_parquet(path)
        if path.suffix.casefold() == ".csv":
            return pandas.read_csv(path)
    except Exception as exc:
        raise SystemExit(
            "No fue posible leer la fuente de calibración."
        ) from exc
    raise SystemExit("La fuente debe ser Parquet o CSV.")


def ensure_validation_only(frame) -> None:
    if "split" not in frame.columns:
        raise SystemExit("La fuente no declara la columna split.")
    splits = set(frame["split"].astype(str).str.casefold())
    if "test" in splits:
        raise SystemExit("La fuente contiene filas test; calibración cancelada.")
    if splits != {"validation"}:
        raise SystemExit(
            "La calibración requiere exclusivamente filas validation."
        )


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
