# 05. Reglas de Conversión Física del Sistema (`UnitConversionRuleModel`)

## 1. Especificación del Modelo `UnitConversionRuleModel`

El modelo `UnitConversionRuleModel` almacena los factores de equivalencia matemática entre dos unidades de medida. Soporta vigencias temporales y la distinción entre reglas universales del sistema y reglas específicas por organización.

### DDL / Esquema de Base de Datos (`unit_conversion_rules`)

```sql
CREATE TABLE unit_conversion_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    from_unit_id UUID NOT NULL REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    to_unit_id UUID NOT NULL REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    conversion_factor NUMERIC(38, 18) NOT NULL,
    inverse_factor NUMERIC(38, 18) NOT NULL,
    effective_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMP WITH TIME ZONE NULL,
    is_system_rule BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    row_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_conversion_rule_pair UNIQUE (organization_id, from_unit_id, to_unit_id, effective_from),
    CONSTRAINT chk_positive_factors CHECK (conversion_factor > 0 AND inverse_factor > 0)
);

CREATE INDEX idx_rules_from_to ON unit_conversion_rules(from_unit_id, to_unit_id);
CREATE INDEX idx_rules_org_active ON unit_conversion_rules(organization_id, is_active);
```

---

## 2. Reglas Físicas Estándar del Sistema (Seeding Base)

El sistema incluye las siguientes equivalencias físicas universales precargadas:

| Unidad Origen (`from`) | Unidad Destino (`to`) | Factor de Conversión (`conversion_factor`) | Factor Inverso (`inverse_factor`) |
| :--- | :--- | :--- | :--- |
| `KG` | `G` | `1000.000000000000000000` | `0.001000000000000000` |
| `TON` | `KG` | `1000.000000000000000000` | `0.001000000000000000` |
| `M` | `CM` | `100.000000000000000000` | `0.010000000000000000` |
| `M` | `MM` | `1000.000000000000000000` | `0.001000000000000000` |
| `M2` | `CM2` | `10000.000000000000000000` | `0.000100000000000000` |
| `M3` | `L` | `1000.000000000000000000` | `0.001000000000000000` |
| `L` | `ML` | `1000.000000000000000000` | `0.001000000000000000` |
| `DOCENA` | `UND` | `12.000000000000000000` | `0.083333333333333333` |
| `CIENTO` | `UND` | `100.000000000000000000` | `0.010000000000000000` |
| `MILLAR` | `UND` | `1000.000000000000000000` | `0.001000000000000000` |

---

## 3. Garantías de Consistencia y Reciprocidad

1. **Auto-Cálculo del Factor Inverso**:
   - Al registrar una regla con factor $F$, el sistema calcula automáticamente el factor inverso $F_{inv} = \frac{1}{F}$ garantizando precisión hasta 18 decimales.
2. **Restricción de Misma Dimensión**:
   - Ambas unidades (`from_unit_id` y `to_unit_id`) deben compartir el mismo `dimension_id` si `is_system_rule = true`.
3. **Validación de Solapamiento Temporal**:
   - No pueden existir dos reglas activas para el mismo par de unidades (`from_unit_id`, `to_unit_id`) en la misma organización con rangos de tiempo solapados.
