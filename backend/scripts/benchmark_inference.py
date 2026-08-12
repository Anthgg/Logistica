import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field

from _phase9_common import (
    project_path,
    reject_test_source,
    write_json_atomic,
)

from app.core.config import settings
from app.services.model_loader_service import ModelLoaderService


class BenchmarkRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    split: str
    dataset_version: str
    participant_code: str
    image_path: str | None = None
    behavioral_features: dict[str, float] | None = None
    repeat: int = Field(default=1, ge=1, le=100)


def _statistics(values: list[float]) -> dict[str, float]:
    try:
        import numpy
    except ImportError as exc:
        raise SystemExit("NumPy es obligatorio para benchmark.") from exc
    array = numpy.asarray(values, dtype=float)
    return {
        "mean_ms": float(array.mean()),
        "median_ms": float(numpy.median(array)),
        "std_ms": float(array.std()),
        "p90_ms": float(numpy.percentile(array, 90)),
        "p95_ms": float(numpy.percentile(array, 95)),
        "maximum_ms": float(array.max()),
    }


def _read_records(path: Path, dataset_version: str) -> list[BenchmarkRecord]:
    if not path.is_file():
        raise SystemExit(f"No existe el manifiesto de benchmark: {path}")
    reject_test_source(path)
    records = [
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise SystemExit("El manifiesto de benchmark está vacío.")
    for record in records:
        if record.split.casefold() != "validation":
            raise SystemExit("Benchmark de Fase 9A solo admite validation.")
        if record.dataset_version != dataset_version:
            raise SystemExit("dataset_version no coincide en benchmark.")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument(
        "--input",
        default=(
            "data/reports/integration/"
            "inference_validation_requests.jsonl"
        ),
    )
    parser.add_argument(
        "--output",
        default="data/reports/integration/inference_benchmark.json",
    )
    arguments = parser.parse_args()
    records = _read_records(
        project_path(arguments.input), arguments.dataset_version
    )
    try:
        import psutil
    except ImportError as exc:
        raise SystemExit("psutil es obligatorio para benchmark.") from exc
    strict = settings.model_copy(
        update={
            "REQUIRE_ALL_MODELS": True,
            "MODEL_LOAD_ON_STARTUP": True,
        }
    )
    loader = ModelLoaderService(strict)
    loader.startup()
    process = psutil.Process()
    memory_before = float(process.memory_info().rss)
    cpu_times_before = process.cpu_times()
    process.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None)
    benchmark_started = perf_counter()
    timings: dict[str, list[float]] = {
        "facial": [],
        "pad": [],
        "behavioral": [],
        "total": [],
    }
    try:
        for record in records:
            image = None
            if record.image_path:
                image_path = project_path(record.image_path)
                reject_test_source(image_path)
                image = image_path.read_bytes()
            for _ in range(record.repeat):
                total_started = perf_counter()
                if image is not None:
                    if loader.facial_runtime is None:
                        raise SystemExit("Runtime facial no disponible.")
                    started = perf_counter()
                    loader.facial_runtime.infer(
                        record.participant_code, image
                    )
                    timings["facial"].append(
                        (perf_counter() - started) * 1000
                    )
                    if loader.pad_runtime is None:
                        raise SystemExit("Runtime PAD no disponible.")
                    started = perf_counter()
                    loader.pad_runtime.infer(image)
                    timings["pad"].append(
                        (perf_counter() - started) * 1000
                    )
                if record.behavioral_features is not None:
                    runtime = loader.get_behavioral_runtime(
                        record.participant_code
                    )
                    started = perf_counter()
                    runtime.infer(record.behavioral_features)
                    timings["behavioral"].append(
                        (perf_counter() - started) * 1000
                    )
                timings["total"].append(
                    (perf_counter() - total_started) * 1000
                )
    finally:
        loader.shutdown()
    elapsed_seconds = perf_counter() - benchmark_started
    memory_after = float(process.memory_info().rss)
    cpu_times_after = process.cpu_times()
    payload: dict[str, object] = {
        "benchmark_type": "validation_integration_benchmark",
        "dataset_version": arguments.dataset_version,
        "device": loader.status.device,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "request_count": len(timings["total"]),
        "latency": {
            name: _statistics(values)
            for name, values in timings.items()
            if values
        },
        "memory": {
            "rss_before_bytes": memory_before,
            "rss_after_bytes": memory_after,
            "rss_delta_bytes": memory_after - memory_before,
        },
        "compute": {
            "selected_device": loader.status.device,
            "gpu_runtime_selected": loader.status.device == "gpu",
            "process_cpu_percent": process.cpu_percent(interval=None),
            "system_cpu_percent": psutil.cpu_percent(interval=None),
            "process_user_cpu_seconds": (
                cpu_times_after.user - cpu_times_before.user
            ),
            "process_system_cpu_seconds": (
                cpu_times_after.system - cpu_times_before.system
            ),
            "wall_time_seconds": elapsed_seconds,
        },
        "uses_test": False,
        "is_final_evaluation": False,
    }
    write_json_atomic(project_path(arguments.output), payload)
    print(
        "Benchmark de validation completado | "
        f"requests={len(timings['total'])}"
    )


if __name__ == "__main__":
    main()
