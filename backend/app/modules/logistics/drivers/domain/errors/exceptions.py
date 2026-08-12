"""Domain exceptions for Phase 029 — Driver Master Data."""

from fastapi import status
from app.core.exceptions import ApplicationError


class DriverNotFound(ApplicationError):
    def __init__(self, driver_id: str):
        super().__init__(
            message=f"Conductor con ID '{driver_id}' no encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_NOT_FOUND",
        )


class DriverCodeConflict(ApplicationError):
    def __init__(self, code: str):
        super().__init__(
            message=f"El código de conductor '{code}' ya existe en esta organización.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DRIVER_CODE_CONFLICT",
        )


class DriverStatusInvalid(ApplicationError):
    def __init__(self, current_status: str, action: str):
        super().__init__(
            message=f"No se puede realizar la acción '{action}' en un conductor con estado '{current_status}'.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_STATUS_INVALID",
        )


class DriverCannotBeActivated(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"El conductor no puede ser activado: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_CANNOT_BE_ACTIVATED",
        )


class DriverCannotBeRetired(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"El conductor no puede ser retirado: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_CANNOT_BE_RETIRED",
        )


class DriverBlockedError(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"El conductor está bloqueado: {reason}",
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="DRIVER_BLOCKED",
        )


class DriverVersionConflict(ApplicationError):
    def __init__(self):
        super().__init__(
            message="Conflicto de concurrencia al actualizar el conductor. La versión especificada difiere de la actual.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DRIVER_VERSION_CONFLICT",
        )


class DriverDuplicateSuspected(ApplicationError):
    def __init__(self, details: str):
        super().__init__(
            message=f"Se ha detectado un posible conductor duplicado: {details}",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DRIVER_DUPLICATE_SUSPECTED",
        )


class DriverIdentityDocumentNotFound(ApplicationError):
    def __init__(self, doc_id: str):
        super().__init__(
            message=f"Documento de identidad '{doc_id}' no encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_IDENTITY_DOCUMENT_NOT_FOUND",
        )


class DriverIdentityDocumentConflict(ApplicationError):
    def __init__(self, doc_type: str, val: str):
        super().__init__(
            message=f"El documento de identidad {doc_type} '{val}' ya está registrado en la organización.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DRIVER_IDENTITY_DOCUMENT_CONFLICT",
        )


class DriverIdentityDocumentInvalid(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Documento de identidad no válido: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DRIVER_IDENTITY_DOCUMENT_INVALID",
        )


class DriverIdentityDocumentExpired(ApplicationError):
    def __init__(self, expires_at: str):
        super().__init__(
            message=f"El documento de identidad ha expirado en la fecha {expires_at}.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_IDENTITY_DOCUMENT_EXPIRED",
        )


class DriverLicenseNotFound(ApplicationError):
    def __init__(self, license_id: str):
        super().__init__(
            message=f"Licencia de conducir '{license_id}' no encontrada.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_LICENSE_NOT_FOUND",
        )


class DriverLicenseConflict(ApplicationError):
    def __init__(self, num: str):
        super().__init__(
            message=f"La licencia de conducir '{num}' ya está registrada en la organización.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="DRIVER_LICENSE_CONFLICT",
        )


class DriverLicenseInvalid(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Licencia de conducir no válida: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DRIVER_LICENSE_INVALID",
        )


class DriverLicenseExpired(ApplicationError):
    def __init__(self, expires_at: str):
        super().__init__(
            message=f"La licencia de conducir expiró el {expires_at}.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_LICENSE_EXPIRED",
        )


class DriverLicenseSuspended(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"La licencia de conducir está suspendida: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_LICENSE_SUSPENDED",
        )


class DriverLicenseRevoked(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"La licencia de conducir ha sido revocada: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_LICENSE_REVOKED",
        )


class DriverLicenseCategoryMissing(ApplicationError):
    def __init__(self, cat_code: str):
        super().__init__(
            message=f"La categoría de licencia '{cat_code}' no existe en el catálogo o no está activa.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_LICENSE_CATEGORY_MISSING",
        )


class DriverLicenseCategoryExpired(ApplicationError):
    def __init__(self, cat_code: str):
        super().__init__(
            message=f"La asignación de la categoría de licencia '{cat_code}' ha expirado.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_LICENSE_CATEGORY_EXPIRED",
        )


class DriverCarrierAssignmentNotFound(ApplicationError):
    def __init__(self, assignment_id: str):
        super().__init__(
            message=f"Asignación de transportista '{assignment_id}' no encontrada.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_CARRIER_ASSIGNMENT_NOT_FOUND",
        )


class DriverCarrierInvalid(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Socio comercial inválido para asignación de transportista: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_CARRIER_INVALID",
        )


class DriverCarrierRoleRequired(ApplicationError):
    def __init__(self, partner_id: str):
        super().__init__(
            message=f"El socio comercial '{partner_id}' no tiene un rol 'CARRIER' activo.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_CARRIER_ROLE_REQUIRED",
        )


class DriverCarrierBlockedError(ApplicationError):
    def __init__(self, partner_id: str):
        super().__init__(
            message=f"El transportista '{partner_id}' se encuentra bloqueado.",
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="DRIVER_CARRIER_BLOCKED",
        )


class DriverContactInvalid(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Datos de contacto del conductor inválidos: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DRIVER_CONTACT_INVALID",
        )


class DriverPhotoNotFound(ApplicationError):
    def __init__(self, photo_id: str):
        super().__init__(
            message=f"Fotografía '{photo_id}' no encontrada.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_PHOTO_NOT_FOUND",
        )


class DriverPhotoReferenceInvalid(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Referencia de fotografía inválida: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DRIVER_PHOTO_REFERENCE_INVALID",
        )


class DriverDocumentNotFound(ApplicationError):
    def __init__(self, doc_id: str):
        super().__init__(
            message=f"Documento de conductor '{doc_id}' no encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_DOCUMENT_NOT_FOUND",
        )


class DriverDocumentExpired(ApplicationError):
    def __init__(self, doc_type: str):
        super().__init__(
            message=f"El documento '{doc_type}' ha expirado.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_DOCUMENT_EXPIRED",
        )


class DriverRestrictionNotFound(ApplicationError):
    def __init__(self, rest_id: str):
        super().__init__(
            message=f"Restricción de conductor '{rest_id}' no encontrada.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DRIVER_RESTRICTION_NOT_FOUND",
        )


class DriverVehicleIncompatible(ApplicationError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"El conductor no es compatible con el vehículo especificado: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DRIVER_VEHICLE_INCOMPATIBLE",
        )
