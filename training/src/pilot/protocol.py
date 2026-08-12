from dataclasses import dataclass
from datetime import datetime

from src.common.config import ProtocolConfig
from src.common.timestamps import ensure_utc


@dataclass(frozen=True)
class SessionAnnotation:
    identity_label: str = "genuine"
    sample_role: str = "verification"
    operator_change_at: datetime | None = None
    presentation_label: str | None = None
    attack_type: str | None = None
    source_device: str | None = None
    pad_source_id: str | None = None


def annotation_for(
    protocol: ProtocolConfig, session_id: str
) -> SessionAnnotation:
    values = protocol.session_annotations.get(str(session_id), {})
    change = values.get("operator_change_at")
    attack_type = values.get("attack_type")
    presentation = values.get("presentation_label")
    if attack_type and str(attack_type) not in protocol.allowed_pad_attack_types:
        raise ValueError(f"Tipo PAD no permitido para la sesión {session_id}.")
    if presentation not in {None, "bona_fide", "attack"}:
        raise ValueError(f"Etiqueta PAD no válida para la sesión {session_id}.")
    identity = str(values.get("identity_label", "genuine"))
    sample_role = str(values.get("sample_role", "verification"))
    if identity not in {"genuine", "impostor"}:
        raise ValueError(f"identity_label no válido para {session_id}.")
    if sample_role not in {"enrollment", "verification", "change_operator"}:
        raise ValueError(f"sample_role no válido para {session_id}.")
    return SessionAnnotation(
        identity_label=identity,
        sample_role=sample_role,
        operator_change_at=ensure_utc(str(change)) if change else None,
        presentation_label=str(presentation) if presentation else None,
        attack_type=str(attack_type) if attack_type else None,
        source_device=(
            str(values["source_device"]) if values.get("source_device") else None
        ),
        pad_source_id=(
            str(values["pad_source_id"]) if values.get("pad_source_id") else None
        ),
    )


def annotation_from_record(
    protocol: ProtocolConfig, record: dict[str, object]
) -> SessionAnnotation:
    if str(record.get("annotation_status") or "") != "confirmed":
        return annotation_for(protocol, str(record.get("session_id") or ""))
    values = {
        "identity_label": record.get("identity_label"),
        "sample_role": record.get("sample_role"),
        "operator_change_at": record.get("operator_change_at"),
        "presentation_label": record.get("presentation_label"),
        "attack_type": record.get("attack_type"),
        "source_device": record.get("source_device"),
        "pad_source_id": record.get("pad_source_id"),
    }
    clean_values = {
        key: value
        for key, value in values.items()
        if value is not None and str(value) not in {"", "NaT", "nan", "None"}
    }
    temporary = protocol.model_copy(
        update={
            "session_annotations": {
                str(record.get("session_id") or ""): clean_values
            }
        }
    )
    return annotation_for(temporary, str(record.get("session_id") or ""))


def validate_protocol_annotations(protocol: ProtocolConfig) -> None:
    for session_id in protocol.session_annotations:
        annotation_for(protocol, session_id)
