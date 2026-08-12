from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Asigna particiones deterministas y comprueba fugas.",
        stop_after="splits",
    )
