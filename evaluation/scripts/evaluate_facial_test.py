import _bootstrap

from evaluation.scripts._stage_support import run_metric_stage
from evaluation.src.facial.evaluator import evaluate_facial


if __name__ == "__main__":
    run_metric_stage(evaluate_facial, "Calcula métricas faciales sobre predicciones autorizadas.")
