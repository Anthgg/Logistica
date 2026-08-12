"""Domain Exception definitions for Phase 026 (RUC Module)."""

from fastapi import HTTPException, status


class RucDomainError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": message})
        self.error_code = error_code
        self.message = message


class RucInvalidError(RucDomainError):
    def __init__(self, message: str = "El número de RUC no es válido sintácticamente."):
        super().__init__(status.HTTP_400_BAD_REQUEST, "RUC_INVALID", message)


class RucNotFoundError(RucDomainError):
    def __init__(self, ruc: str):
        super().__init__(status.HTTP_404_NOT_FOUND, "RUC_NOT_FOUND", f"RUC '{ruc}' no fue encontrado en el padrón o fuentes activas.")


class RucDatasetUnavailableError(RucDomainError):
    def __init__(self, message: str = "No hay un padrón de RUC activo disponible para la consulta."):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, "RUC_DATASET_UNAVAILABLE", message)


class RucImportAlreadyRunningError(RucDomainError):
    def __init__(self, message: str = "Ya existe un trabajo de importación de RUC en ejecución."):
        super().__init__(status.HTTP_409_CONFLICT, "RUC_IMPORT_ALREADY_RUNNING", message)


class RucImportArchiveInvalidError(RucDomainError):
    def __init__(self, message: str = "El archivo ZIP de importación es inválido o está corrupto."):
        super().__init__(status.HTTP_400_BAD_REQUEST, "RUC_IMPORT_ARCHIVE_INVALID", message)


class RucImportZipBombError(RucDomainError):
    def __init__(self, message: str = "Se detectó un riesgo de descompresión (ZIP bomb/path traversal)."):
        super().__init__(status.HTTP_400_BAD_REQUEST, "RUC_IMPORT_ZIP_BOMB_DETECTED", message)


class RucImportAnomalousRowCountError(RucDomainError):
    def __init__(self, message: str = "La variación en el conteo de filas supera los umbrales de seguridad permitidos."):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "RUC_IMPORT_ANOMALOUS_ROW_COUNT", message)


class RucProviderUnavailableError(RucDomainError):
    def __init__(self, message: str = "El proveedor autorizado de RUC no está disponible."):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, "RUC_PROVIDER_UNAVAILABLE", message)


class RucVerificationConflictError(RucDomainError):
    def __init__(self, message: str = "Se detectaron conflictos en la verificación de datos del socio."):
        super().__init__(status.HTTP_409_CONFLICT, "RUC_VERIFICATION_CONFLICT", message)
