from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Ejecuta el pipeline completo de preparación de la Fase 7.",
        stop_after="report",
        full_pipeline=True,
    )
