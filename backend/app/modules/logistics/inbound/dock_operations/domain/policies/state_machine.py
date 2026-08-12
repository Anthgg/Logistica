"""Explicit command-only state transitions for assignments and unloading."""

from app.modules.logistics.inbound.dock_operations.domain.errors import invalid


def require_transition(
    current: str,
    target: str,
    allowed: dict[str, set[str]],
    resource: str,
) -> None:
    if target not in allowed.get(current, set()):
        raise invalid(
            f"{resource.upper()}_STATUS_INVALID",
            f"Transición inválida de {current} a {target}.",
        )


ASSIGNMENT_TRANSITIONS = {
    "ASSIGNED": {"MOVING_TO_DOCK", "AT_DOCK", "CANCELLED", "SUPERSEDED", "REASSIGNMENT_REQUIRED"},
    "MOVING_TO_DOCK": {"AT_DOCK", "CANCELLED", "SUPERSEDED", "REASSIGNMENT_REQUIRED"},
    "AT_DOCK": {"READY_FOR_UNLOADING", "UNLOADING_IN_PROGRESS", "CANCELLED", "SUPERSEDED"},
    "READY_FOR_UNLOADING": {"UNLOADING_IN_PROGRESS", "CANCELLED", "SUPERSEDED"},
    "UNLOADING_IN_PROGRESS": {"UNLOADING_PAUSED", "UNLOADING_COMPLETED", "RELEASE_PENDING"},
    "UNLOADING_PAUSED": {"UNLOADING_IN_PROGRESS", "RELEASE_PENDING"},
    "UNLOADING_COMPLETED": {"RELEASE_PENDING", "DOCK_RELEASED"},
    "RELEASE_PENDING": {"DOCK_RELEASED"},
    "REASSIGNMENT_REQUIRED": {"SUPERSEDED", "CANCELLED"},
}

UNLOADING_TRANSITIONS = {
    "CREATED": {"READINESS_PENDING", "READY", "CANCELLED"},
    "READINESS_PENDING": {"READY", "CANCELLED"},
    "READY": {"IN_PROGRESS", "CANCELLED"},
    "IN_PROGRESS": {"PAUSED", "COMPLETED", "ABORTED"},
    "PAUSED": {"IN_PROGRESS", "ABORTED"},
    "ABORTED": {"SUPERSEDED"},
}
