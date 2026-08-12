# 08 — Unidad de Medida Base Provisional (`base_unit_code`)

## 1. Estrategia de Unidad de Medida Provisional

En la arquitectura del sistema, la gestión avanzada de unidades de medida (UOM), familias de conversiones dimensionales (ej. `1 CAJA = 12 UND`, `1 PALLET = 40 CAJAS`) y reglas de redondeo se implementará formalmente en la **Fase 024 (Maestro de Unidades y Conversiones UOM)**.

Sin embargo, para permitir la creación operacional de productos en la **Fase 023** sin bloquear el desarrollo backend ni admitir cadenas de texto arbitrarias no estandarizadas, se establece el campo `base_unit_code` respaldado por una **lista provisional controlada** y marcado explícitamente con el indicador **`PENDING_PHASE_024`**.

---

## 2. Catálogo Controlado de Unidades Base Provisionales

Cualquier valor asignado al campo `base_unit_code` en `ProductModel` debe pertenecer de forma obligatoria a la siguiente lista enum validada por el backend:

| Código (`base_unit_code`) | Nombre / Descripción | Magnitud Física |
| :--- | :--- | :--- |
| `UND` | Unidad / Pieza (Default) | Conteo Discreto |
| `KG` | Kilogramo | Masa |
| `G` | Gramo | Masa |
| `L` | Litro | Volumen |
| `ML` | Mililitro | Volumen |
| `M` | Metro | Longitud |
| `CM` | Centímetro | Longitud |
| `M2` | Metro Cuadrado | Área |
| `M3` | Metro Cúbico | Volumen Espacial |
| `CAJA` | Caja Estándar | Conteo / Empaque |
| `PAQUETE` | Paquete / Blíster | Conteo / Empaque |

---

## 3. Validación Backend (`ProductBaseUnitValidator`)

```python
class InvalidBaseUnitCodeError(ValueError):
    pass

class ProductBaseUnitValidator:
    """
    [PENDING_PHASE_024]
    Validador provisional de unidad de medida base.
    En la Fase 024, esta clase será reemplazada por una consulta al servicio UOMMasterService.
    """
    PROVISIONAL_ALLOWED_UNITS = {
        "UND", "KG", "G", "L", "ML",
        "M", "CM", "M2", "M3", "CAJA", "PAQUETE"
    }

    @classmethod
    def validate_base_unit(cls, unit_code: str) -> str:
        if not unit_code or not isinstance(unit_code, str):
            raise InvalidBaseUnitCodeError("El código de unidad base es requerido.")
            
        clean_code = unit_code.strip().upper()
        if clean_code not in cls.PROVISIONAL_ALLOWED_UNITS:
            raise InvalidBaseUnitCodeError(
                f"Unidad base '{clean_code}' no permitida. Lista provisional válida: {sorted(list(cls.PROVISIONAL_ALLOWED_UNITS))}. [PENDING_PHASE_024]"
            )
        return clean_code
```

---

## 4. Desaprobación Explícita de Conversiones en Fase 023

> [!WARNING]
> **REGLA DE ARQUITECTURA DE LA FASE 023:**
> En la Fase 023 **NO SE PERMITE** realizar conversiones entre unidades de medida, definir factores multiplicadores ni registrar unidades secundarias de empaque dentro del modelo de producto.
>
> Todas las cantidades físicas de stock, perfil volumétrico y movimientos de prueba en la Fase 023 se evalúan exclusivamente en términos de la **Unidad Base (`base_unit_code`)**.

---

## 5. Hoja de Ruta de Transición a la Fase 024

```mermaid
graph TD
    subgraph "Fase 023 (Estado Actual)"
        P23[ProductModel.base_unit_code: VARCHAR] --> V23[ProductBaseUnitValidator (Lista Estática 11 Códigos)]
    end

    subgraph "Fase 024 (Integración Futura)"
        UOM_DB[(uom_definitions / uom_conversions)] --> UOM_SVC[UOMMasterService]
        UOM_SVC -->|FK uom_id / Validation| P24[ProductModel.base_unit_id]
        P24 --> C24[UOMConversionEngine (Caja -> UND, Pallet -> Caja)]
    end

    V23 -.->|Migración Transparente| UOM_SVC
```

1. **Compatibilidad Asegurada:** Los 11 códigos de la lista provisional fueron seleccionados en estricta conformidad con la norma ISO 80000 y los códigos de catálogo SUNAT (Anexo 6), garantizando que en la migración DDL de la Fase 024 no se requiera saneamiento de datos.
