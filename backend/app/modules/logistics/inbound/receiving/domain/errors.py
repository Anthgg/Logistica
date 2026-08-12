from app.core.exceptions import ApplicationError


class ReceivingError(ApplicationError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(code, message, status_code)


def receiving_error(name: str, message: str, status_code: int = 400) -> ReceivingError:
    return ReceivingError(name, message, status_code)


ERROR_CODES = (
    "InboundReceiptNotFound", "InboundReceiptAlreadyExists", "InboundReceiptStatusInvalid",
    "InboundReceiptNotEditable", "InboundReceiptSourceInvalid", "InboundReceiptUnloadingNotCompleted",
    "InboundReceiptSupplierMismatch", "InboundReceiptWarehouseMismatch", "InboundReceiptLineNotFound",
    "InboundReceiptProductMismatch", "InboundReceiptUnexpectedProduct", "InboundReceiptUnknownCode",
    "InboundReceiptAmbiguousCode", "InboundReceiptQuantityInvalid", "InboundReceiptQuantityExceeded",
    "InboundReceiptUnitInvalid", "InboundReceiptConversionMissing", "InboundReceiptLotRequired",
    "InboundReceiptLotQuantityMismatch", "InboundReceiptSerialRequired", "InboundReceiptSerialDuplicate",
    "InboundReceiptSerialQuantityMismatch", "InboundReceiptExpirationRequired", "InboundReceiptExpirationInvalid",
    "InboundReceiptExpiredProduct", "InboundReceiptUnresolvedScans", "InboundReceiptValidationFailed",
    "InboundReceiptDifferenceReviewRequired", "InboundReceiptAlreadyCompleted", "InboundReceiptIntegrityFailed",
    "InboundScanSessionInactive", "InboundScanEventDuplicate", "InboundScanCompensationInvalid",
)


# Typed errors are kept for application-layer consumers; HTTP codes remain
# stable uppercase identifiers through ``ReceivingError``.
class InboundReceiptNotFound(ReceivingError): pass
class InboundReceiptAlreadyExists(ReceivingError): pass
class InboundReceiptStatusInvalid(ReceivingError): pass
class InboundReceiptNotEditable(ReceivingError): pass
class InboundReceiptSourceInvalid(ReceivingError): pass
class InboundReceiptUnloadingNotCompleted(ReceivingError): pass
class InboundReceiptSupplierMismatch(ReceivingError): pass
class InboundReceiptWarehouseMismatch(ReceivingError): pass
class InboundReceiptLineNotFound(ReceivingError): pass
class InboundReceiptProductMismatch(ReceivingError): pass
class InboundReceiptUnexpectedProduct(ReceivingError): pass
class InboundReceiptUnknownCode(ReceivingError): pass
class InboundReceiptAmbiguousCode(ReceivingError): pass
class InboundReceiptQuantityInvalid(ReceivingError): pass
class InboundReceiptQuantityExceeded(ReceivingError): pass
class InboundReceiptUnitInvalid(ReceivingError): pass
class InboundReceiptConversionMissing(ReceivingError): pass
class InboundReceiptLotRequired(ReceivingError): pass
class InboundReceiptLotQuantityMismatch(ReceivingError): pass
class InboundReceiptSerialRequired(ReceivingError): pass
class InboundReceiptSerialDuplicate(ReceivingError): pass
class InboundReceiptSerialQuantityMismatch(ReceivingError): pass
class InboundReceiptExpirationRequired(ReceivingError): pass
class InboundReceiptExpirationInvalid(ReceivingError): pass
class InboundReceiptExpiredProduct(ReceivingError): pass
class InboundReceiptUnresolvedScans(ReceivingError): pass
class InboundReceiptValidationFailed(ReceivingError): pass
class InboundReceiptDifferenceReviewRequired(ReceivingError): pass
class InboundReceiptAlreadyCompleted(ReceivingError): pass
class InboundReceiptIntegrityFailed(ReceivingError): pass
class InboundScanSessionInactive(ReceivingError): pass
class InboundScanEventDuplicate(ReceivingError): pass
class InboundScanCompensationInvalid(ReceivingError): pass
