"""Logistics module — constants and enums.

Convention for permission names: ``logistics.<resource>.<action>``.
"""

from enum import StrEnum


class LogisticsPermission(StrEnum):
    """Granular logistics permissions following ``logistics.<resource>.<action>``."""

    # Documents
    DOCUMENTS_READ = "logistics.documents.read"
    DOCUMENTS_ISSUE = "logistics.documents.issue"
    DOCUMENTS_REPRINT = "logistics.documents.reprint"
    DOCUMENTS_CANCEL = "logistics.documents.cancel"

    # Routes
    ROUTES_READ = "logistics.routes.read"
    ROUTES_CALCULATE = "logistics.routes.calculate"

    # Files
    FILES_READ = "logistics.files.read"
    FILES_UPLOAD = "logistics.files.upload"

    # Audit
    AUDIT_READ = "logistics.audit.read"

    # Integrations
    INTEGRATIONS_EXECUTE = "logistics.integrations.execute"


class LogisticsModule(StrEnum):
    """Sub-module identifiers used for logging and audit context."""

    DOCUMENTS = "documents"
    ROUTES = "routes"
    FILES = "files"
    AUDIT = "audit"
    INTEGRATIONS = "integrations"


#: Phase identifier for health/metadata endpoint.
LOGISTICS_PHASE = "phase-003"