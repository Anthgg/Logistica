# 08 — Especificación de Snapshots Inmutables y Hash SHA-256

---

## 1. Congelamiento Histórico de Datos (Snapshot Pattern)

Una Orden de Compra es un documento legal y contractual. Si el nombre comercial, RUC, dirección fiscal o cuenta bancaria de un proveedor cambian en el maestro de proveedores (CRM/ERP) seis meses después de emitida una orden, la versión histórica de la orden **nunca debe alterarse**.

Para garantizar la **fidelidad histórica e inmutabilidad**, la Fase 034 utiliza el patrón **Snapshot Inmutable**. Cada revisión de una Orden de Compra (`po_purchase_order_revisions`) serializa cuatro estructuras JSONB independientes:

1. **`supplier_snapshot`**: Datos completos del proveedor al momento de la revisión (RUC/Tax ID, Razón Social, Dirección Fiscal, Contacto, Datos Bancarios).
2. **`buyer_snapshot`**: Datos completos de la entidad compradora (Organización, Sede, Dirección de Entrega, Datos de Contacto).
3. **`source_snapshot`**: Trazabilidad del documento origen (ID de Decisión CCO, ID de Solicitud/Requisición, Adjudicatarios).
4. **`monetary_snapshot`**: Resumen financiero exacto congelado (Subtotal, Descuentos, Impuestos, Fletes, Total General).

---

## 2. Proveedor de Snapshots (`PurchaseOrderSnapshotProvider`)

El servicio `PurchaseOrderSnapshotProvider` encapsula la construcción y serialización de snapshots en formato JSON canónico:

```python
import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Dict

class DecimalEncoder(json.JSONEncoder):
    """Garantiza la serialización exacta de objetos Decimal a string para evitar perdida de precisión."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class PurchaseOrderSnapshotProvider:
    @staticmethod
    def build_supplier_snapshot(supplier_entity: Any) -> Dict[str, Any]:
        return {
            "supplier_id": str(supplier_entity.id),
            "tax_id": supplier_entity.tax_id,
            "legal_name": supplier_entity.legal_name,
            "trade_name": supplier_entity.trade_name,
            "fiscal_address": supplier_entity.fiscal_address,
            "payment_bank_account": supplier_entity.payment_bank_account,
        }

    @staticmethod
    def compute_revision_content_hash(
        revision_number: int,
        supplier_snapshot: Dict[str, Any],
        buyer_snapshot: Dict[str, Any],
        source_snapshot: Dict[str, Any],
        monetary_snapshot: Dict[str, Any],
        lines_data: list[Dict[str, Any]]
    ) -> str:
        """Calcula el hash determinista SHA-256 de la revisión ordenando canónicamente las claves JSON."""
        payload = {
            "revision_number": revision_number,
            "supplier_snapshot": supplier_snapshot,
            "buyer_snapshot": buyer_snapshot,
            "source_snapshot": source_snapshot,
            "monetary_snapshot": monetary_snapshot,
            "lines": lines_data,
        }
        
        # Serialización canónica: claves ordenadas, sin espacios redundantes, encoder Decimal
        canonical_json = json.dumps(
            payload, 
            cls=DecimalEncoder, 
            sort_keys=True, 
            separators=(",", ":")
        )
        
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
```

---

## 3. Ejemplo de Digest SHA-256 (`content_hash`)

El campo `content_hash` almacena una cadena hexadecimal de 64 caracteres SHA-256. 

Cualquier intento de alteración maliciosa o corrupción directa en la base de datos PostgreSQL romperá la correspondencia del hash al re-evaluar la firma de la revisión:

```json
{
  "revision_number": 1,
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "supplier_snapshot": {
    "supplier_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "tax_id": "20100047218",
    "legal_name": "DISTRIBUIDORA INDUSTRIAL S.A.C."
  },
  "monetary_snapshot": {
    "subtotal": "1000.00",
    "tax_total": "180.00",
    "grand_total": "1180.00"
  }
}
```
