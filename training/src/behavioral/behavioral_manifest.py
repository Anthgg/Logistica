import pandas as pd

REQUIRED_METADATA = {
    "dataset_version",
    "protocol_version",
    "generated_at",
    "source_session_id",
    "participant_id",
    "session_id",
    "window_id",
    "checksum",
    "quality_status",
    "rejection_reasons",
    "split",
}


def build_behavioral_manifest(features: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_METADATA - set(features.columns)
    if missing and not features.empty:
        raise ValueError(
            "Faltan columnas obligatorias: " + ", ".join(sorted(missing))
        )
    forbidden = {"key", "code", "text", "password", "events", "payload"}
    present = forbidden & {str(column).casefold() for column in features.columns}
    if present:
        raise ValueError(
            "El manifiesto contiene columnas textuales prohibidas: "
            + ", ".join(sorted(present))
        )
    if features.empty:
        return pd.DataFrame(columns=sorted(REQUIRED_METADATA | set(features.columns)))
    return features.copy()
