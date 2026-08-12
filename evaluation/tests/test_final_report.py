from evaluation.src.ablation.evaluator import evaluate_ablation
from evaluation.src.behavioral.evaluator import evaluate_behavioral
from evaluation.src.common.privacy import assert_report_privacy
from evaluation.src.comparison.evaluator import compare_pretest_posttest
from evaluation.src.facial.evaluator import evaluate_facial
from evaluation.src.fusion.evaluator import evaluate_fusion
from evaluation.src.pad.evaluator import evaluate_pad
from evaluation.src.performance.evaluator import evaluate_performance
from evaluation.src.reports.generator import (
    artifact_checksums,
    generate_final_outputs,
    verify_final_artifacts,
    write_run_metadata,
)
from evaluation.src.statistics.analysis import run_statistical_analysis


def test_complete_synthetic_report_contract(
    synthetic_config,
    synthetic_predictions,
) -> None:
    facial = evaluate_facial(synthetic_predictions, synthetic_config)
    pad = evaluate_pad(synthetic_predictions, synthetic_config)
    behavioral = evaluate_behavioral(
        synthetic_predictions,
        synthetic_config,
    )
    fusion = evaluate_fusion(synthetic_predictions, synthetic_config)
    ablation_results, ablation_summary = evaluate_ablation(
        synthetic_predictions,
        synthetic_config,
    )
    comparison, comparison_summary = compare_pretest_posttest(
        synthetic_predictions,
        synthetic_config,
    )
    latency, performance = evaluate_performance(
        synthetic_predictions,
        synthetic_config,
    )
    tests, intervals, effects = run_statistical_analysis(
        synthetic_predictions,
        comparison,
        ablation_results,
        latency,
        synthetic_config,
    )
    generate_final_outputs(
        synthetic_config,
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
    write_run_metadata(
        synthetic_config,
        run_id="synthetic-run",
        duration_seconds=1.0,
        status="completed",
        device="cpu",
        authorized_rerun=False,
        rerun_reason=None,
        errors=[],
    )
    output = synthetic_config.paths.output_directory
    verify_final_artifacts(output)
    assert_report_privacy(output)
    checksums = artifact_checksums(output)
    assert "final_evaluation_report.md" in checksums
    report = (output / "final_evaluation_report.md").read_text(
        encoding="utf-8"
    )
    assert "## 32. Versiones y checksums" in report
