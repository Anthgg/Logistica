# 07 — Identificadores de Productos y Códigos de Barras

## 1. Gestión Multi-Código de Barras (`ProductIdentifierModel`)

Un producto en una cadena de suministro puede poseer múltiples códigos de barras o identificadores globales y locales dependiendo de su empaque o procedencia (ejemplo: EAN-13 para la unidad de venta individual, GTIN-14 para la caja máster de 24 unidades, y un código interno de almacén).

La **Fase 023** soporta una relación uno-a-muchos entre el producto y sus identificadores mediante la tabla `product_identifiers`.

---

## 2. Esquema Relacional de `product_identifiers`

```sql
CREATE TYPE identifier_type_enum AS ENUM (
    'GTIN_8',        -- EAN-8 / GS1
    'GTIN_12',       -- UPC-A / GS1
    'GTIN_13',       -- EAN-13 / GS1
    'GTIN_14',       -- ITF-14 / DUN-14 / GS1
    'INTERNAL_BARCODE',-- Código interno generado por la plataforma (T1P-...)
    'QR_CODE',       -- Código QR de alta densidad
    'CUSTOM_CODE'    -- Código de cliente o proveedor externo
);

CREATE TABLE product_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    identifier_type identifier_type_enum NOT NULL,
    raw_value VARCHAR(100) NOT NULL,
    normalized_value VARCHAR(100) NOT NULL,
    
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    description VARCHAR(255) NULL, -- Ej: "Código EAN en empaque máster 24 unidades"
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_identifiers_org_value UNIQUE (organization_id, normalized_value)
);

CREATE INDEX idx_identifiers_product ON product_identifiers(product_id);
CREATE INDEX idx_identifiers_lookup ON product_identifiers(organization_id, normalized_value);
```

---

## 3. Algoritmo de Verificación Módulo 10 (`ProductIdentifierValidator`)

Los estándares internacionales GS1 (GTIN-8, GTIN-12, GTIN-13, GTIN-14) exigen la validación del último dígito de chequeo (*Check Digit*) mediante el algoritmo normalizado **Módulo 10**.

```python
class InvalidBarcodeChecksumError(ValueError):
    pass

class ProductIdentifierValidator:

    @staticmethod
    def validate_modulo_10(barcode: str) -> bool:
        """
        Valida el dígito de chequeo Módulo 10 para secuencias numéricas GTIN (8, 12, 13, 14).
        """
        if not barcode.isdigit():
            return False
            
        digits = [int(c) for c in barcode]
        check_digit = digits[-1]
        payload = digits[:-1]
        
        # Ponderación alternativa desde la derecha: 3, 1, 3, 1...
        total = 0
        reverse_payload = list(reversed(payload))
        for idx, digit in enumerate(reverse_payload):
            weight = 3 if idx % 2 == 0 else 1
            total += digit * weight
            
        calculated_check = (10 - (total % 10)) % 10
        return calculated_check == check_digit

    @classmethod
    def validate_and_normalize(cls, identifier_type: str, raw_value: str) -> str:
        clean = raw_value.strip().replace(" ", "").replace("-", "")
        
        if identifier_type in ["GTIN_8", "GTIN_12", "GTIN_13", "GTIN_14"]:
            expected_lengths = {
                "GTIN_8": 8,
                "GTIN_12": 12,
                "GTIN_13": 13,
                "GTIN_14": 14
            }
            target_len = expected_lengths[identifier_type]
            
            if len(clean) != target_len or not clean.isdigit():
                raise ValueError(f"El identificador {identifier_type} debe tener exactamente {target_len} dígitos numéricos.")
                
            if not cls.validate_modulo_10(clean):
                raise InvalidBarcodeChecksumError(
                    f"El código de barras '{clean}' para {identifier_type} falló la validación del dígito de chequeo Módulo 10."
                )
                
        return clean.upper()
```

---

## 4. Generación de Código Interno (`T1P-{ref}-{checksum}`)

Para productos que no poseen un código EAN/UPC de fábrica, la plataforma genera automáticamente un código de barras interno con la siguiente estructura:

$$\text{Format: } \texttt{T1P-} + \text{8\_CHAR\_HEX} + \texttt{-} + \text{CHECK\_DIGIT}$$

Ejemplo: `T1P-A4F89B12-7`

### Algoritmo de Generación:
```python
import random

def generate_internal_barcode() -> str:
    hex_ref = f"{random.getrandbits(32):08X}"
    # Convertir caracteres hex a valor numérico para calcular checksum Módulo 10
    numeric_rep = "".join([str(ord(c) % 10) for c in hex_ref])
    
    total = 0
    for idx, digit in enumerate(reversed([int(d) for d in numeric_rep])):
        weight = 3 if idx % 2 == 0 else 1
        total += digit * weight
    checksum = (10 - (total % 10)) % 10
    
    return f"T1P-{hex_ref}-{checksum}"
```

---

## 5. Renderizado de Código de Barras en PNG (Code128)

La plataforma cuenta con un servicio integrado de renderizado gráfico de códigos de barras en formato **PNG / SVG** utilizando el estándar **Code128**:

```python
import io
import barcode
from barcode.writer import ImageWriter

class BarcodeImageService:

    @staticmethod
    def render_code128_png(code_value: str) -> bytes:
        """
        Renderiza una imagen PNG binaria con simbología Code128 para etiquetas físicas.
        """
        code128 = barcode.get('code128', code_value, writer=ImageWriter())
        buffer = io.BytesIO()
        code128.write(buffer, options={
            'module_width': 0.3,
            'module_height': 15.0,
            'font_size': 10,
            'text_distance': 5.0,
            'quiet_zone': 6.5,
        })
        return buffer.getvalue()
```

### Endpoint REST de Renderizado:
`GET /api/logistics/product-identifiers/{id}/barcode-image`
Retorna una respuesta `Content-Type: image/png` lista para ser mostrada en componentes UI o enviada a impresoras térmicas de etiquetas (Zebra/TSC).
