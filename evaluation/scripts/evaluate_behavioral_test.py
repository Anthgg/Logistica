import _bootstrap

from evaluation.scripts._stage_support import run_metric_stage
from evaluation.src.behavioral.evaluator import evaluate_behavioral


if __name__ == "__main__":
    run_metric_stage(
        evaluate_behavioral,
        "Calcula métricas conductuales sobre predicciones autorizadas.",
    )
