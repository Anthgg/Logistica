from __future__ import annotations

from pathlib import Path
from time import perf_counter

import pandas as pd
import psutil

from evaluation.src.common.config import FinalEvaluationConfig


class FinalInferenceError(RuntimeError):
    """Raised when approved runtime inference cannot be completed."""


def _available(value: object) -> bool:
    if value is None:
        return False
    try:
        return bool(pd.notna(value))
    except (TypeError, ValueError):
        return False


def _sample_path(config: FinalEvaluationConfig, relative_value: object) -> Path:
    candidate = (config.paths.test_data_root / str(relative_value)).resolve()
    try:
        candidate.relative_to(config.paths.test_data_root.resolve())
    except ValueError as exc:
        raise FinalInferenceError(
            "Una ruta de muestra intenta salir de test_data_root."
        ) from exc
    if not candidate.is_file():
        raise FinalInferenceError("No existe una muestra test registrada.")
    return candidate


def run_approved_inference(
    config: FinalEvaluationConfig,
    test_frame: pd.DataFrame,
    *,
    device: str,
) -> pd.DataFrame:
    from app.core.config import settings
    from app.core.exceptions import ApplicationError
    from app.services.model_loader_service import ModelLoaderService

    strict_settings = settings.model_copy(
        update={
            "MODEL_REGISTRY_PATH": str(config.paths.model_registry),
            "MODEL_PATH": str(config.paths.model_registry.parents[1]),
            "FUSION_CONFIG_PATH": str(config.paths.fusion_config),
            "NORMALIZATION_CONFIG_PATH": str(
                config.paths.normalization_config
            ),
            "MODEL_DEVICE": device,
            "MODEL_LOAD_ON_STARTUP": True,
            "MODEL_STRICT_CHECKSUM": True,
            "REQUIRE_ALL_MODELS": True,
            "BEHAVIORAL_MODEL_LOADING_MODE": "lru",
        }
    )
    loader = ModelLoaderService(strict_settings)
    process = psutil.Process()
    rss_before_models = int(process.memory_info().rss)
    model_load_started = perf_counter()
    try:
        loader.startup()
        model_load_ms = (perf_counter() - model_load_started) * 1000.0
        rss_after_models = int(process.memory_info().rss)
        peak_rss = rss_after_models
        if (
            loader.facial_runtime is None
            or loader.pad_runtime is None
            or loader.normalization is None
            or loader.fusion is None
        ):
            raise FinalInferenceError(
                "Los runtimes aprobados no están completamente disponibles."
            )
        schema = config.input_schema
        passthrough = (
            schema.row_id,
            schema.participant_id,
            schema.session_id,
            schema.timestamp,
            schema.facial_label,
            schema.pad_label,
            schema.behavioral_label,
            schema.fusion_label,
            schema.scenario,
            schema.attack_type,
            schema.source_device,
            schema.illumination,
            schema.condition,
            schema.pretest_detected,
            schema.pretest_latency_ms,
            schema.pretest_false_alert,
        )
        results: list[dict[str, object]] = []
        for _, row in test_frame.iterrows():
            output: dict[str, object] = {
                column: row[column]
                for column in passthrough
                if column in test_frame.columns
            }
            participant = str(row.get(schema.participant_id, ""))
            image_value = row.get(schema.image_path)
            image_content: bytes | None = None
            if _available(image_value):
                image_content = _sample_path(config, image_value).read_bytes()
            started = perf_counter()
            component_risks: dict[str, float | None] = {
                "facial": None,
                "pad": None,
                "behavioral": None,
            }
            if (
                image_content is not None
                and _available(row.get(schema.facial_label))
            ):
                try:
                    facial = loader.facial_runtime.infer(
                        participant, image_content
                    )
                    output.update(
                        {
                            "facial_similarity": facial.similarity,
                            "facial_threshold": facial.threshold,
                            "facial_decision": facial.decision,
                            "facial_latency_ms": facial.latency_ms,
                            "facial_decode_ms": facial.image_decode_ms,
                            "facial_model_inference_ms": facial.model_inference_ms,
                            "facial_model_version": facial.model_version,
                        }
                    )
                    component_risks["facial"] = loader.normalization.normalize(
                        "facial", facial.similarity
                    )
                except ApplicationError as exc:
                    output["facial_rejection_code"] = exc.code
            if (
                image_content is not None
                and _available(row.get(schema.pad_label))
            ):
                try:
                    pad = loader.pad_runtime.infer(image_content)
                    output.update(
                        {
                            "pad_attack_probability": pad.attack_probability,
                            "pad_threshold": pad.threshold,
                            "pad_decision": pad.decision,
                            "pad_latency_ms": pad.latency_ms,
                            "pad_decode_ms": pad.image_decode_ms,
                            "pad_model_inference_ms": pad.model_inference_ms,
                            "pad_model_version": pad.model_version,
                        }
                    )
                    component_risks["pad"] = loader.normalization.normalize(
                        "pad", pad.attack_probability
                    )
                except ApplicationError as exc:
                    output["pad_rejection_code"] = exc.code
            if _available(row.get(schema.behavioral_label)):
                try:
                    behavioral_runtime = loader.get_behavioral_runtime(
                        participant
                    )
                    features: dict[str, float] = {}
                    for feature in behavioral_runtime.feature_names:
                        value = row.get(feature)
                        if not _available(value):
                            raise FinalInferenceError(
                                "Falta una feature conductual requerida."
                            )
                        features[feature] = float(value)
                    behavioral = behavioral_runtime.infer(features)
                    output.update(
                        {
                            "behavioral_reconstruction_error": (
                                behavioral.reconstruction_error
                            ),
                            "behavioral_threshold": behavioral.threshold,
                            "behavioral_decision": behavioral.decision,
                            "behavioral_latency_ms": behavioral.latency_ms,
                            "behavioral_model_version": (
                                behavioral.model_version
                            ),
                        }
                    )
                    component_risks[
                        "behavioral"
                    ] = loader.normalization.normalize(
                        "behavioral", behavioral.reconstruction_error
                    )
                except ApplicationError as exc:
                    output["behavioral_rejection_code"] = exc.code
            for component, risk in component_risks.items():
                output[f"{component}_risk"] = risk
            try:
                fused = loader.fusion.fuse(component_risks)
                decision_threshold = (
                    loader.fusion.config.risk_thresholds.medium_max
                )
                output.update(
                    {
                        "fusion_risk": fused.risk,
                        "fusion_threshold": decision_threshold,
                        "fusion_predicted": int(
                            fused.risk >= decision_threshold
                        ),
                        "fusion_available_components": "+".join(
                            fused.available_components
                        ),
                        "fusion_strategy": fused.strategy,
                        "fusion_latency_ms": fused.latency_ms,
                        "fusion_version": (
                            loader.fusion.config.fusion_version
                        ),
                    }
                )
            except ApplicationError as exc:
                output["fusion_rejection_code"] = exc.code
            output["total_inference_latency_ms"] = (
                perf_counter() - started
            ) * 1000.0
            peak_rss = max(peak_rss, int(process.memory_info().rss))
            results.append(output)
        result = pd.DataFrame(results)
        result.attrs.update(
            {
                "rss_before_models_bytes": rss_before_models,
                "rss_after_models_bytes": rss_after_models,
                "peak_rss_during_inference_bytes": peak_rss,
                "model_load_ms": model_load_ms,
            }
        )
        return result
    except ApplicationError as exc:
        raise FinalInferenceError(
            f"La carga o inferencia aprobada falló con código {exc.code}."
        ) from exc
    finally:
        loader.shutdown()
