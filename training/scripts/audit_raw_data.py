from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Audita las sesiones y los archivos fuente sin modificar raw.",
        stop_after="audit",
    )
