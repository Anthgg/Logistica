"""Stable application errors for Phase 038."""

from app.core.exceptions import ApplicationError


class DockOperationsError(ApplicationError):
    def __init__(self, code: str, message: str, status_code: int = 422):
        super().__init__(code, message, status_code)


class WarehouseDockNotFound(DockOperationsError):
    def __init__(self):
        super().__init__("WAREHOUSE_DOCK_NOT_FOUND", "Muelle no encontrado.", 404)


class InboundDockQueueEntryNotFound(DockOperationsError):
    def __init__(self):
        super().__init__("INBOUND_DOCK_QUEUE_ENTRY_NOT_FOUND", "Entrada de cola no encontrada.", 404)


class DockAssignmentNotFound(DockOperationsError):
    def __init__(self):
        super().__init__("DOCK_ASSIGNMENT_NOT_FOUND", "Asignación de muelle no encontrada.", 404)


class UnloadingOperationNotFound(DockOperationsError):
    def __init__(self):
        super().__init__("UNLOADING_OPERATION_NOT_FOUND", "Operación de descarga no encontrada.", 404)


def conflict(code: str, message: str) -> DockOperationsError:
    return DockOperationsError(code, message, 409)


def invalid(code: str, message: str) -> DockOperationsError:
    return DockOperationsError(code, message, 422)
