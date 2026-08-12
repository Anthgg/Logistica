import _bootstrap

from evaluation.scripts._stage_support import run_metric_stage
from evaluation.src.pad.evaluator import evaluate_pad


if __name__ == "__main__":
    run_metric_stage(evaluate_pad, "Calcula métricas PAD sobre predicciones autorizadas.")
