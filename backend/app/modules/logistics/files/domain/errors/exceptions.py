"""Domain exceptions for Phase 030 — Files and Evidence Centralization."""

from fastapi import status
from app.core.exceptions import ApplicationError


class FileNotFoundError(ApplicationError):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_NOT_FOUND",
            message=f"No se encontró el archivo con ID '{file_id}'.",
        )


class FileVersionNotFoundError(ApplicationError):
    def __init__(self, version_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_VERSION_NOT_FOUND",
            message=f"No se encontró la versión de archivo '{version_id}'.",
        )


class FileUploadSessionNotFoundError(ApplicationError):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_UPLOAD_SESSION_NOT_FOUND",
            message=f"No se encontró la sesión de carga '{session_id}'.",
        )


class FileUploadSessionExpiredError(ApplicationError):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            code="FILE_UPLOAD_SESSION_EXPIRED",
            message=f"La sesión de carga '{session_id}' ha expirado.",
        )


class FileUploadSessionAlreadyFinalizedError(ApplicationError):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="FILE_UPLOAD_SESSION_ALREADY_FINALIZED",
            message=f"La sesión de carga '{session_id}' ya ha sido finalizada.",
        )


class FileSizeExceededError(ApplicationError):
    def __init__(self, size_bytes: int, max_bytes: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_SIZE_EXCEEDED",
            message=f"El tamaño del archivo ({size_bytes} bytes) excede el límite permitido ({max_bytes} bytes).",
        )


class FileTypeNotAllowedError(ApplicationError):
    def __init__(self, mime_type: str, extension: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="FILE_TYPE_NOT_ALLOWED",
            message=f"El tipo de archivo '{mime_type}' (extensión '.{extension}') no está permitido.",
        )


class FileTypeMismatchError(ApplicationError):
    def __init__(self, declared_mime: str, detected_mime: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_TYPE_MISMATCH",
            message=f"El tipo declarado ('{declared_mime}') no coincide con el tipo binario detectado ('{detected_mime}').",
        )


class FileContentInvalidError(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="FILE_CONTENT_INVALID",
            message=f"El contenido del archivo no es válido: {reason}",
        )


class FileMalwareDetectedError(ApplicationError):
    def __init__(self, scan_result: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="FILE_MALWARE_DETECTED",
            message=f"El archivo fue rechazado por detección de malware ({scan_result}).",
        )


class FileMalwareScanPendingError(ApplicationError):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            code="FILE_MALWARE_SCAN_PENDING",
            message=f"El archivo '{file_id}' se encuentra en cuarentena a la espera de escaneo antimalware.",
        )


class FileMalwareScannerUnavailableError(ApplicationError):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="FILE_MALWARE_SCANNER_UNAVAILABLE",
            message="El servicio de escaneo antimalware no está disponible. El archivo permanece en cuarentena.",
        )


class FileQuarantinedError(ApplicationError):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            code="FILE_QUARANTINED",
            message=f"El archivo '{file_id}' está retenido en cuarentena.",
        )


class FileRejectedError(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_REJECTED",
            message=f"El archivo fue rechazado: {reason}",
        )


class FileCorruptedError(ApplicationError):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="FILE_CORRUPTED",
            message=f"El archivo '{file_id}' presenta corrupción física o fallo de checksum.",
        )


class FileHashMismatchError(ApplicationError):
    def __init__(self, expected_hash: str, actual_hash: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="FILE_HASH_MISMATCH",
            message=f"El hash SHA-256 calculado ('{actual_hash}') no coincide con el esperado ('{expected_hash}').",
        )


class FileObjectMissingError(ApplicationError):
    def __init__(self, storage_key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_OBJECT_MISSING",
            message=f"El objeto de almacenamiento con clave '{storage_key}' no fue encontrado en el bucket.",
        )


class FileAssociationInvalidError(ApplicationError):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_ASSOCIATION_INVALID",
            message=f"No se puede asociar el archivo al recurso '{resource_type}' con ID '{resource_id}'.",
        )


class FileAccessDeniedError(ApplicationError):
    def __init__(self, reason: str = "Permisos insuficientes para acceder al archivo."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FILE_ACCESS_DENIED",
            message=reason,
        )


class FilePreviewNotAvailableError(ApplicationError):
    def __init__(self, file_id: str, reason: str = "Formato no previsualizable."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_PREVIEW_NOT_AVAILABLE",
            message=f"La vista previa para el archivo '{file_id}' no está disponible: {reason}",
        )


class FileDownloadNotAvailableError(ApplicationError):
    def __init__(self, file_id: str, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_DOWNLOAD_NOT_AVAILABLE",
            message=f"No se puede descargar el archivo '{file_id}': {reason}",
        )


class FileRetentionBlockedError(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="FILE_RETENTION_BLOCKED",
            message=f"Acción bloqueada por política de retención documental: {reason}",
        )


class FileLegalHoldActiveError(ApplicationError):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="FILE_LEGAL_HOLD_ACTIVE",
            message=f"No se puede eliminar ni alterar el archivo '{file_id}' porque posee una retención legal activa (Legal Hold).",
        )


class FileDeletionBlockedError(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="FILE_DELETION_BLOCKED",
            message=f"Eliminación de archivo bloqueada: {reason}",
        )


class EvidenceNotFoundError(ApplicationError):
    def __init__(self, evidence_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVIDENCE_NOT_FOUND",
            message=f"No se encontró el registro de evidencia '{evidence_id}'.",
        )


class EvidenceAlreadyAcceptedError(ApplicationError):
    def __init__(self, evidence_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="EVIDENCE_ALREADY_ACCEPTED",
            message=f"La evidencia '{evidence_id}' ya ha sido aceptada y no puede ser modificada.",
        )


class EvidenceImmutableError(ApplicationError):
    def __init__(self, evidence_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="EVIDENCE_IMMUTABLE",
            message=f"La evidencia '{evidence_id}' es inmutable y no se permite su alteración directa.",
        )
