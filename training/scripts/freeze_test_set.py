from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Congela de forma controlada el conjunto de prueba.",
        stop_after="freeze",
        freeze_by_default=True,
    )
