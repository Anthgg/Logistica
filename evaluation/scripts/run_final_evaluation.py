from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import _bootstrap

from evaluation.src.common.config import (
    EvaluationConfigurationError,
    load_config,
)
from evaluation.src.common.integrity import (
    EvaluationGateError,
    ExecutionMarkers,
    begin_execution,
    complete_execution,
    create_or_verify_lock,
    preflight,
    record_failure,
    require_preflight,
    verify_and_open_frozen_test,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ejecuta una sola evaluación final controlada."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("evaluation/configs/final_evaluation.yaml"),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "gpu"),
        default="auto",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--authorized-rerun", action="store_true")
    parser.add_argument("--rerun-reason")
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    if arguments.dry_run and (
        arguments.authorized_rerun or arguments.rerun_reason
    ):
        raise SystemExit(
            "El dry-run no acepta opciones de repetición definitiva."
        )
    try:
        config = load_config(
            arguments.config,
            output_override=arguments.output_dir,
        )
    except EvaluationConfigurationError as exc:
        print(
            json.dumps(
                {
                    "approved": False,
                    "configuration_error": str(exc),
                    "test_manifest_opened": False,
                    "markers_created": False,
                    "results_created": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(2) from exc
    result = preflight(config)
    print(json.dumps(result.as_json(), ensure_ascii=False, indent=2))
    if arguments.dry_run:
        if not result.approved:
            raise SystemExit(2)
        return
    require_preflight(result)
    markers: ExecutionMarkers | None = None
    started_at = perf_counter()
    try:
        create_or_verify_lock(config, device=arguments.device)
        markers = begin_execution(
            config,
            authorized_rerun=arguments.authorized_rerun,
            rerun_reason=arguments.rerun_reason,
            command=sys.argv,
        )
        test_frame = verify_and_open_frozen_test(config)
        from evaluation.src.ablation.evaluator import evaluate_ablation
        from evaluation.src.behavioral.evaluator import evaluate_behavioral
        from evaluation.src.common.inference import run_approved_inference
        from evaluation.src.common.privacy import assert_report_privacy
        from evaluation.src.comparison.evaluator import (
            compare_pretest_posttest,
        )
        from evaluation.src.facial.evaluator import evaluate_facial
        from evaluation.src.fusion.evaluator import evaluate_fusion
        from evaluation.src.pad.evaluator import evaluate_pad
        from evaluation.src.performance.evaluator import (
            evaluate_performance,
        )
        from evaluation.src.reports.generator import (
            artifact_checksums,
            generate_final_outputs,
            verify_final_artifacts,
            write_run_metadata,
        )
        from evaluation.src.statistics.analysis import (
            run_statistical_analysis,
        )

        predictions = run_approved_inference(
            config, test_frame, device=arguments.device
        )
        facial = evaluate_facial(predictions, config)
        pad = evaluate_pad(predictions, config)
        behavioral = evaluate_behavioral(predictions, config)
        fusion = evaluate_fusion(predictions, config)
        ablation_results, ablation_summary = evaluate_ablation(
            predictions, config
        )
        comparison, comparison_summary = compare_pretest_posttest(
            predictions, config
        )
        latency, performance = evaluate_performance(predictions, config)
        tests, intervals, effects = run_statistical_analysis(
            predictions,
            comparison,
            ablation_results,
            latency,
            config,
        )
        generate_final_outputs(
            config,
            component_metrics={
                "facial": facial,
                "pad": pad,
                "behavioral": behavioral,
                "fusion": fusion,
            },
            ablation_summary=ablation_summary,
            comparison=comparison,
            comparison_summary=comparison_summary,
            latency=latency,
            performance_summary=performance,
            statistical_tests=tests,
            confidence_intervals=intervals,
            effect_sizes=effects,
        )
        duration = perf_counter() - started_at
        write_run_metadata(
            config,
            run_id=markers.run_id,
            duration_seconds=duration,
            status="completed",
            device=arguments.device,
            authorized_rerun=markers.authorized_rerun,
            rerun_reason=markers.rerun_reason,
            errors=[],
        )
        verify_final_artifacts(config.paths.output_directory)
        assert_report_privacy(config.paths.output_directory)
        checksums = artifact_checksums(config.paths.output_directory)
        complete_execution(
            markers,
            duration_seconds=duration,
            artifact_checksums=checksums,
        )
        print(
            json.dumps(
                {
                    "status": "completed",
                    "run_id": markers.run_id,
                    "artifact_count": len(checksums),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except BaseException as exc:
        record_failure(config, markers, exc)
        if isinstance(exc, (EvaluationGateError, ValueError, RuntimeError)):
            raise SystemExit(str(exc)) from exc
        raise


if __name__ == "__main__":
    main()
