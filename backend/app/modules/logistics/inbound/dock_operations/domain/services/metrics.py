"""Deterministic calculations based only on authoritative event timestamps."""

from datetime import datetime

from app.modules.logistics.inbound.dock_operations.domain.enums import (
    OperationalTimeQualityStatus,
)


def _seconds(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    value = int((end - start).total_seconds())
    return value if value >= 0 else None


class DockOperationalMetricsService:
    @staticmethod
    def calculate(
        *,
        gate_arrived_at: datetime | None,
        gate_cleared_at: datetime | None,
        queued_at: datetime | None,
        assigned_at: datetime | None,
        movement_started_at: datetime | None,
        dock_arrived_at: datetime | None,
        unloading_started_at: datetime | None,
        unloading_completed_at: datetime | None,
        dock_released_at: datetime | None,
        pause_seconds: int,
    ) -> dict[str, int | str | None]:
        gross = _seconds(unloading_started_at, unloading_completed_at)
        net = None if gross is None else max(gross - max(pause_seconds, 0), 0)
        values: dict[str, int | str | None] = {
            "gate_processing_seconds": _seconds(gate_arrived_at, gate_cleared_at),
            "gate_to_queue_seconds": _seconds(gate_cleared_at, queued_at),
            "dock_assignment_wait_seconds": _seconds(queued_at, assigned_at),
            "movement_to_dock_seconds": _seconds(movement_started_at, dock_arrived_at),
            "gate_to_dock_seconds": _seconds(gate_cleared_at, dock_arrived_at),
            "dock_wait_before_unloading_seconds": _seconds(dock_arrived_at, unloading_started_at),
            "unloading_gross_seconds": gross,
            "unloading_pause_seconds": max(pause_seconds, 0),
            "unloading_net_seconds": net,
            "dock_release_delay_seconds": _seconds(unloading_completed_at, dock_released_at),
            "dock_occupancy_seconds": _seconds(dock_arrived_at, dock_released_at),
            "total_inbound_operational_seconds": _seconds(gate_arrived_at, dock_released_at),
        }
        present = sum(value is not None for key, value in values.items() if key != "unloading_pause_seconds")
        values["data_quality_status"] = (
            OperationalTimeQualityStatus.COMPLETE.value
            if present == 11
            else OperationalTimeQualityStatus.PARTIAL.value
        )
        return values
