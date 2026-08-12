import _bootstrap

from evaluation.scripts._stage_support import run_metric_stage
from evaluation.src.fusion.evaluator import evaluate_fusion


if __name__ == "__main__":
    run_metric_stage(evaluate_fusion, "Calcula métricas de fusión autorizadas.")
