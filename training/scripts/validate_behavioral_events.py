from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Valida lotes conductuales y rechaza contenido textual.",
        stop_after="event_validation",
    )
