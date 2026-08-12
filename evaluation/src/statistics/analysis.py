from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.multitest import multipletests

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    bootstrap_mean_interval,
    pad_error_rates,
    stratified_bootstrap_interval,
    wilson_interval,
)
from evaluation.src.common.privacy import participant_code


def _metric_statistic(
    name: str,
    threshold: float,
) -> Callable[[np.ndarray, np.ndarray], float]:
    def statistic(labels: np.ndarray, scores: np.ndarray) -> float:
        if name == "roc_auc":
            return (
                float(roc_auc_score(labels, scores))
                if len(np.unique(labels)) == 2
                else math.nan
            )
        predicted = scores >= threshold
        true_positive = int(np.sum((labels == 1) & predicted))
        true_negative = int(np.sum((labels == 0) & ~predicted))
        false_positive = int(np.sum((labels == 0) & predicted))
        false_negative = int(np.sum((labels == 1) & ~predicted))
        total = len(labels)
        if name == "accuracy":
            return float((true_positive + true_negative) / total)
        if name == "precision":
            denominator = true_positive + false_positive
            return float(true_positive / denominator) if denominator else 0.0
        if name == "recall":
            denominator = true_positive + false_negative
            return (
                float(true_positive / denominator) if denominator else 0.0
            )
        if name == "f1":
            denominator = (
                2 * true_positive + false_positive + false_negative
            )
            return (
                float(2 * true_positive / denominator)
                if denominator
                else 0.0
            )
        if name == "far":
            denominator = false_positive + true_negative
            return (
                float(false_positive / denominator)
                if denominator
                else math.nan
            )
        if name == "frr":
            denominator = false_negative + true_positive
            return (
                float(false_negative / denominator)
                if denominator
                else math.nan
            )
        raise ValueError(f"Métrica bootstrap no soportada: {name}.")

    return statistic


def _pad_rate_statistic(
    name: str,
) -> Callable[[np.ndarray, np.ndarray], float]:
    def statistic(labels: np.ndarray, decisions: np.ndarray) -> float:
        predicted = decisions >= 0.5
        false_positive = int(np.sum((labels == 0) & predicted))
        true_negative = int(np.sum((labels == 0) & ~predicted))
        false_negative = int(np.sum((labels == 1) & ~predicted))
        true_positive = int(np.sum((labels == 1) & predicted))
        apcer_denominator = false_negative + true_positive
        bpcer_denominator = false_positive + true_negative
        apcer = (
            float(false_negative / apcer_denominator)
            if apcer_denominator
            else math.nan
        )
        bpcer = (
            float(false_positive / bpcer_denominator)
            if bpcer_denominator
            else math.nan
        )
        if name == "apcer":
            return apcer
        if name == "bpcer":
            return bpcer
        if name == "acer":
            return float((apcer + bpcer) / 2.0)
        raise ValueError(f"Tasa PAD bootstrap no soportada: {name}.")

    return statistic


def _paired_effect_size(pretest: np.ndarray, posttest: np.ndarray) -> float | None:
    differences = posttest - pretest
    if len(differences) < 2:
        return None
    standard_deviation = float(np.std(differences, ddof=1))
    if standard_deviation == 0:
        return 0.0
    return float(np.mean(differences) / standard_deviation)


def _mcnemar_records(
    comparison: pd.DataFrame,
) -> tuple[dict[str, object], dict[str, object]]:
    truth = comparison["true_condition"].astype(int).to_numpy()
    pre = comparison["pretest_detected"].astype(int).to_numpy()
    post = comparison["posttest_detected"].astype(int).to_numpy()
    pre_correct = pre == truth
    post_correct = post == truth
    table = np.asarray(
        [
            [
                np.sum(pre_correct & post_correct),
                np.sum(pre_correct & ~post_correct),
            ],
            [
                np.sum(~pre_correct & post_correct),
                np.sum(~pre_correct & ~post_correct),
            ],
        ],
        dtype=int,
    )
    result = mcnemar(table, exact=True)
    discordant_pre = int(table[0, 1])
    discordant_post = int(table[1, 0])
    odds_ratio = (
        float(discordant_post / discordant_pre)
        if discordant_pre
        else (math.inf if discordant_post else 1.0)
    )
    test_record = {
        "test": "mcnemar_exact",
        "comparison": "pretest_vs_posttest_correctness",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "assumptions": "paired_binary_outcomes",
        "n": len(comparison),
    }
    effect_record = {
        "effect": "mcnemar_odds_ratio",
        "comparison": "pretest_vs_posttest_correctness",
        "value": odds_ratio,
        "interpretation": "odds of posttest-only correctness versus pretest-only correctness",
    }
    return test_record, effect_record


def _latency_test(
    comparison: pd.DataFrame,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    paired = comparison.dropna(
        subset=["pretest_latency_ms", "posttest_latency_ms"]
    )
    if len(paired) < 3:
        return None, None
    pre = paired["pretest_latency_ms"].astype(float).to_numpy()
    post = paired["posttest_latency_ms"].astype(float).to_numpy()
    differences = post - pre
    constant_differences = bool(
        np.allclose(differences, differences[0])
    )
    normality_p = (
        None
        if constant_differences
        else (
            float(stats.shapiro(differences).pvalue)
            if 3 <= len(differences) <= 5000
            else None
        )
    )
    if constant_differences and np.allclose(differences, 0.0):
        test_name = "wilcoxon_signed_rank"
        effect_name = "wilcoxon_r"
        test_record = {
            "test": test_name,
            "comparison": "pretest_vs_posttest_latency",
            "statistic": 0.0,
            "p_value": 1.0,
            "normality_p_value": None,
            "assumptions": "all_paired_differences_are_zero",
            "n": len(paired),
        }
        effect_record = {
            "effect": effect_name,
            "comparison": "pretest_vs_posttest_latency",
            "value": 0.0,
            "interpretation": "paired latency difference",
        }
        return test_record, effect_record
    if (
        not constant_differences
        and normality_p is not None
        and normality_p > 0.05
    ):
        result = stats.ttest_rel(post, pre)
        test_name = "paired_student_t"
        effect_name = "cohen_d_paired"
        effect_value = _paired_effect_size(pre, post)
    else:
        try:
            result = stats.wilcoxon(post, pre)
            test_name = "wilcoxon_signed_rank"
            effect_name = "wilcoxon_r"
            z_approximation = float(stats.norm.isf(result.pvalue / 2.0))
            effect_value = z_approximation / math.sqrt(len(paired))
        except ValueError:
            return None, None
    test_record = {
        "test": test_name,
        "comparison": "pretest_vs_posttest_latency",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "normality_p_value": normality_p,
        "n": len(paired),
    }
    effect_record = {
        "effect": effect_name,
        "comparison": "pretest_vs_posttest_latency",
        "value": effect_value,
        "interpretation": "paired latency difference",
    }
    return test_record, effect_record


def _friedman_records(
    ablation_results: pd.DataFrame,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    pivot = ablation_results.pivot(
        index="row_id",
        columns="configuration",
        values="correct",
    ).dropna()
    if pivot.shape[0] < 2 or pivot.shape[1] < 3:
        return None, None
    arrays = [
        pivot[column].astype(float).to_numpy() for column in pivot.columns
    ]
    try:
        result = stats.friedmanchisquare(*arrays)
    except ValueError:
        return None, None
    kendall_w = float(
        result.statistic / (pivot.shape[0] * (pivot.shape[1] - 1))
    )
    return (
        {
            "test": "friedman",
            "comparison": "approved_ablation_configurations",
            "statistic": float(result.statistic),
            "p_value": float(result.pvalue),
            "n": pivot.shape[0],
            "groups": pivot.shape[1],
        },
        {
            "effect": "kendall_w",
            "comparison": "approved_ablation_configurations",
            "value": kendall_w,
            "interpretation": "agreement/effect across paired configurations",
        },
    )


def _confidence_intervals(
    predictions: pd.DataFrame,
    comparison: pd.DataFrame,
    latency: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> pd.DataFrame:
    schema = config.input_schema
    records: list[dict[str, object]] = []
    sources: list[
        tuple[str, np.ndarray, np.ndarray, np.ndarray]
    ] = []
    modality_specs = (
        (
            "facial",
            schema.facial_label,
            "facial_similarity",
            "facial_threshold",
            "higher",
        ),
        (
            "pad",
            schema.pad_label,
            "pad_attack_probability",
            "pad_threshold",
            "higher",
        ),
        (
            "behavioral",
            schema.behavioral_label,
            "behavioral_reconstruction_error",
            "behavioral_threshold",
            "lower",
        ),
    )
    for component, label_column, score_column, threshold_column, direction in (
        modality_specs
    ):
        required = [label_column, score_column, threshold_column]
        if not set(required) <= set(predictions.columns):
            continue
        evaluated = predictions.dropna(subset=required)
        if evaluated.empty:
            continue
        labels = evaluated[label_column].astype(int).to_numpy()
        scores = evaluated[score_column].astype(float).to_numpy()
        thresholds = evaluated[threshold_column].astype(float).to_numpy()
        decisions = (
            scores >= thresholds
            if direction == "higher"
            else scores <= thresholds
        ).astype(float)
        oriented_scores = (
            scores
            if direction == "higher"
            else thresholds - scores
        )
        sources.append(
            (component, labels, decisions, oriented_scores)
        )
    fusion_required = {
        schema.fusion_label,
        "fusion_predicted",
        "fusion_risk",
    }
    if fusion_required <= set(predictions.columns):
        fusion = predictions.dropna(subset=list(fusion_required))
        if not fusion.empty:
            sources.append(
                (
                    "fusion",
                    fusion[schema.fusion_label].astype(int).to_numpy(),
                    fusion["fusion_predicted"].astype(float).to_numpy(),
                    fusion["fusion_risk"].astype(float).to_numpy(),
                )
            )

    seed_offset = 0
    for component, labels, decisions, oriented_scores in sources:
        baseline = binary_classification_metrics(labels, decisions, 0.5)
        for metric in (
            "accuracy",
            "precision",
            "recall",
            "f1",
            "far",
            "frr",
        ):
            if baseline.get(metric) is None:
                continue
            interval = stratified_bootstrap_interval(
                labels,
                decisions,
                _metric_statistic(metric, 0.5),
                confidence_level=config.confidence_level,
                iterations=config.bootstrap_iterations,
                seed=config.random_seed + seed_offset,
            )
            seed_offset += 1
            records.append(
                {
                    "component": component,
                    "metric": metric,
                    **interval.as_dict(),
                }
            )
        if len(np.unique(labels)) == 2:
            auc_interval = stratified_bootstrap_interval(
                labels,
                oriented_scores,
                _metric_statistic("roc_auc", 0.5),
                confidence_level=config.confidence_level,
                iterations=config.bootstrap_iterations,
                seed=config.random_seed + seed_offset,
            )
            seed_offset += 1
            records.append(
                {
                    "component": component,
                    "metric": "roc_auc",
                    **auc_interval.as_dict(),
                }
            )
        matrix = baseline["confusion_matrix"]
        if not isinstance(matrix, list):
            raise ValueError("La matriz binaria no es válida.")
        tn, fp = int(matrix[0][0]), int(matrix[0][1])
        fn, tp = int(matrix[1][0]), int(matrix[1][1])
        for metric, successes, total in (
            ("accuracy", int(np.sum(labels == decisions)), len(labels)),
            ("far", fp, fp + tn),
            ("frr", fn, fn + tp),
        ):
            if total:
                records.append(
                    {
                        "component": component,
                        "metric": metric,
                        **wilson_interval(
                            successes,
                            total,
                            confidence_level=config.confidence_level,
                        ).as_dict(),
                    }
                )
        if component == "pad":
            pad_baseline = pad_error_rates(baseline)
            for metric in ("apcer", "bpcer", "acer"):
                if pad_baseline[metric] is None:
                    continue
                interval = stratified_bootstrap_interval(
                    labels,
                    decisions,
                    _pad_rate_statistic(metric),
                    confidence_level=config.confidence_level,
                    iterations=config.bootstrap_iterations,
                    seed=config.random_seed + seed_offset,
                )
                seed_offset += 1
                records.append(
                    {
                        "component": component,
                        "metric": metric,
                        **interval.as_dict(),
                    }
                )

    if {"stage", "latency_ms"} <= set(latency.columns):
        for stage, group in latency.groupby("stage"):
            interval = bootstrap_mean_interval(
                group["latency_ms"].astype(float).to_numpy(),
                confidence_level=config.confidence_level,
                iterations=config.bootstrap_iterations,
                seed=config.random_seed + seed_offset,
            )
            seed_offset += 1
            records.append(
                {
                    "component": "performance",
                    "metric": f"{stage}_mean_latency_ms",
                    **interval.as_dict(),
                }
            )
    detection_latency = comparison["posttest_latency_ms"].dropna().astype(float)
    if not detection_latency.empty:
        interval = bootstrap_mean_interval(
            detection_latency.to_numpy(),
            confidence_level=config.confidence_level,
            iterations=config.bootstrap_iterations,
            seed=config.random_seed + seed_offset,
        )
        records.append(
            {
                "component": "comparison",
                "metric": "posttest_mean_time_to_detection_ms",
                **interval.as_dict(),
            }
        )
    return pd.DataFrame(records)


def _spss_exports(
    predictions: pd.DataFrame,
    comparison: pd.DataFrame,
    latency: pd.DataFrame,
    output: Path,
    config: FinalEvaluationConfig,
) -> None:
    comparison.to_csv(
        output / "pretest_posttest_spss.csv", index=False
    )
    comparison.to_csv(output / "session_metrics_spss.csv", index=False)
    latency.to_csv(output / "latency_spss.csv", index=False)
    schema = config.input_schema
    participant = (
        predictions.dropna(subset=[schema.participant_id])
        .groupby(schema.participant_id)
        .agg(
            evaluations=("fusion_predicted", "count"),
            mean_risk=("fusion_risk", "mean"),
            detections=("fusion_predicted", "sum"),
        )
        .reset_index()
    )
    participant[schema.participant_id] = participant[
        schema.participant_id
    ].astype(str).map(participant_code)
    participant.to_csv(
        output / "participant_metrics_spss.csv", index=False
    )
    dictionary = pd.DataFrame(
        [
            {
                "variable": column,
                "description": column.replace("_", " "),
                "type": str(dtype),
                "missing": "blank",
            }
            for column, dtype in comparison.dtypes.items()
        ]
    )
    dictionary.to_csv(
        output / "spss_variable_dictionary.csv", index=False
    )


def run_statistical_analysis(
    predictions: pd.DataFrame,
    comparison: pd.DataFrame,
    ablation_results: pd.DataFrame,
    latency: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tests: list[dict[str, object]] = []
    effects: list[dict[str, object]] = []
    mcnemar_test, mcnemar_effect = _mcnemar_records(comparison)
    tests.append(mcnemar_test)
    effects.append(mcnemar_effect)
    latency_test, latency_effect = _latency_test(comparison)
    if latency_test is not None:
        tests.append(latency_test)
    if latency_effect is not None:
        effects.append(latency_effect)
    friedman_test, friedman_effect = _friedman_records(ablation_results)
    if friedman_test is not None:
        tests.append(friedman_test)
    if friedman_effect is not None:
        effects.append(friedman_effect)
    raw_p_values = np.asarray(
        [float(record["p_value"]) for record in tests],
        dtype=float,
    )
    if len(raw_p_values):
        rejected, corrected, _, _ = multipletests(
            raw_p_values, alpha=0.05, method="holm"
        )
        for record, adjusted, reject in zip(
            tests, corrected, rejected, strict=True
        ):
            record["adjusted_p_value"] = float(adjusted)
            record["reject_null_at_alpha_0_05"] = bool(reject)
            record["multiple_comparison_correction"] = "holm"
    test_frame = pd.DataFrame(tests)
    effect_frame = pd.DataFrame(effects)
    interval_frame = _confidence_intervals(
        predictions,
        comparison,
        latency,
        config,
    )
    output = config.paths.output_directory / "statistics"
    output.mkdir(parents=True, exist_ok=True)
    test_frame.to_csv(output / "statistical_tests.csv", index=False)
    interval_frame.to_csv(
        output / "confidence_intervals.csv", index=False
    )
    effect_frame.to_csv(output / "effect_sizes.csv", index=False)
    _spss_exports(predictions, comparison, latency, output, config)
    (output / "statistical_report.md").write_text(
        "\n".join(
            [
                "# Análisis estadístico",
                "",
                "Nivel de confianza: 95 %. Alfa: 0.05.",
                "Se aplicó corrección de Holm a las pruebas disponibles.",
                "Los IC de AUC usan bootstrap estratificado; no se sustituyeron por DeLong sin una implementación validada para este pipeline.",
                "Los resultados se interpretan dentro de un diseño preexperimental; no establecen causalidad absoluta.",
                "",
                "## Pruebas",
                "",
                test_frame.to_markdown(index=False),
                "",
                "## Tamaños de efecto",
                "",
                effect_frame.to_markdown(index=False),
                "",
                "## Intervalos de confianza",
                "",
                interval_frame.to_markdown(index=False),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return test_frame, interval_frame, effect_frame
