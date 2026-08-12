# 02. Catálogo de Dimensiones Físicas (`MeasurementDimensionModel`)

## 1. Especificación del Modelo `MeasurementDimensionModel`

El modelo `MeasurementDimensionModel` define el marco de referencia físico para todas las unidades de medida en el sistema. Impide la mezcla incoherente de magnitudes incompatibles (ej. sumar litros con metros) y actúa como el clasificador primario del motor de conversiones.

### DDL / Esquema de Base de Datos (`measurement_dimensions`)

```sql
CREATE TABLE measurement_dimensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    canonical_unit_code VARCHAR(32) NOT NULL,
    default_precision INTEGER NOT NULL DEFAULT 6,
    is_system_defined BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    row_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_measurement_dimensions_code ON measurement_dimensions(code);
```

---

## 2. Especificación del Catálogo de Dimensiones Sistema

El sistema nace poblado con exactamente **5 dimensiones físicas fundamentales** inmutables:

| Código Dimension | Nombre | Descripción Física | Unidad Canónica | Precisión por Defecto |
| :--- | :--- | :--- | :--- | :--- |
| `COUNT` | Conteo Discrete | Magnitud discreta de conteo de unidades independientes. | `UND` | `0` (Entero estricto o decimal si fraccionable) |
| `MASS` | Masa / Peso | Magnitud continua de masa física. | `KG` | `6` decimales |
| `LENGTH` | Longitud / Distancia | Magnitud lineal espacial. | `M` | `6` decimales |
| `AREA` | Área / Superficie | Magnitud de superficie bidimensional ($L^2$). | `M2` | `6` decimales |
| `VOLUME` | Volumen / Capacidad | Magnitud de espacio tridimensional ($L^3$). | `M3` | `6` decimales |

---

## 3. Reglas de Inmutabilidad y Gobernanza

1. **Protección del Sistema (`is_system_defined = true`)**:
   - Las 5 dimensiones primarias **no pueden ser eliminadas** de la base de datos bajo ninguna circunstancia.
   - El campo `code` y `canonical_unit_code` de estas 5 dimensiones son **inmutables** tras el seeding inicial.
2. **Restricción de Conversión Intra-Dimensión**:
   - Dos unidades $U_1$ y $U_2$ **sólo pueden convertirse directamente entre sí** si pertenecen al mismo `dimension_id`, o si existe una definición explícita de empaque ligada a un producto específico.
3. **Control Optimista (`row_version`)**:
   - Cualquier modificación en metadatos de dimensiones incrementa el entero `row_version`.
