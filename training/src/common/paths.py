from dataclasses import dataclass
from pathlib import Path

TRAINING_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = TRAINING_ROOT.parent


def resolve_from_training(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (TRAINING_ROOT / path).resolve()


def relative_to_root(path: str | Path, root: str | Path) -> str:
    resolved_path = Path(path).resolve()
    resolved_root = Path(root).resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError("La ruta debe permanecer dentro del directorio de datos.") from exc


@dataclass(frozen=True)
class DataPaths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def interim(self) -> Path:
        return self.root / "interim"

    @property
    def processed(self) -> Path:
        return self.root / "processed"

    @property
    def manifests(self) -> Path:
        return self.root / "manifests"

    @property
    def reports(self) -> Path:
        return self.root / "reports" / "pilot"

    def ensure_output_layout(self) -> None:
        directories = (
            self.interim / "accepted_faces",
            self.interim / "rejected_faces",
            self.interim / "validated_events",
            self.interim / "behavioral_windows",
            self.processed / "facial",
            self.processed / "pad",
            self.processed / "behavioral",
            self.manifests,
            self.reports,
        )
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
