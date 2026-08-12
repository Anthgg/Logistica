from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Construye los manifiestos faciales, PAD y conductuales.",
        stop_after="manifests",
    )
