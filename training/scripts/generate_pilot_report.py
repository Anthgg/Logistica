from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Genera tablas, gráficos, informe y readiness del piloto.",
        stop_after="report",
    )
