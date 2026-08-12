from _cli import run_stage


if __name__ == "__main__":
    run_stage(
        description="Analiza la calidad técnica de las capturas faciales.",
        stop_after="face_quality",
    )
