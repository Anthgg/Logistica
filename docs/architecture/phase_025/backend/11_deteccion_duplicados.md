# 11. Motor de Detección de Duplicados

## Objetivos del Motor

El motor `BusinessPartnerDuplicateDetection` evita la proliferación de registros duplicados en el ERP causados por variaciones ortográficas en la razón social (ej. `COMERCIAL DISTRIBUIDORA S.A.C.` vs `COMERCIAL DISTRIBUIDORA SAC`) o intentos de re-registro de un mismo RUC/DNI.

---

## Estrategia de Detección a Dos Niveles

```
                                [ NUEVO SOCIO DE NEGOCIO ]
                                            |
                                            v
                      +-------------------------------------------+
                      | NIVEL 1: Coincidencia Exacta de Tax ID     |
                      | (organization_id + tax_id_value)          |
                      +---------------------+---------------------+
                                            |
                         +------------------+------------------+
                         | Coincidencia                        | No Coincidencia
                         v                                     v
           [ BLOQUEO INMEDIATO (409) ]        +-----------------------------------+
           "RUC ya registrado"                | NIVEL 2: Coincidencia Fuzzy       |
                                              | Razón Social (Trigram Jaccard)    |
                                              +-----------------+-----------------+
                                                                |
                                             +------------------+------------------+
                                             | Score >= 85%                        | Score 65-84%
                                             v                                     v
                                [ HIGH_PROBABILITY_DUPLICATE ]       [ MEDIUM_PROBABILITY_DUPLICATE ]
                                Requiere Confirmación Usuario        Alerta Informativa
```

---

## 1. Nivel 1: Coincidencia Exacta por Identificador Fiscal

Es un control estricto a nivel de base de datos impulsado por la restricción de unicidad:
`UniqueConstraint("organization_id", "tax_id_type", "tax_id_value")`

Si se intenta crear un socio con un RUC/DNI ya existente en la organización, el repositorio captura la violación de la restricción arrojando `DuplicateTaxIdException`.

---

## 2. Nivel 2: Coincidencia Fuzzy por Razón Social (`pg_trgm`)

Utiliza la extensión de tramas de trigramas de PostgreSQL (`pg_trgm`) para comparar la similitud textual entre la razón social solicitada (`legal_name`) y los socios existentes.

### Algoritmo de Normalización Textual Previa
Antes de ejecutar la consulta trigram, el string es saneado:
1. Conversión a mayúsculas ASCII.
2. Eliminación de sufijos societarios comunes (`S.A.C.`, `SAC`, `S.A.`, `SA`, `E.I.R.L.`, `EIRL`, `S.R.L.`, `LLC`).
3. Remoción de signos de puntuación y espacios dobles.

### Consulta SQL con Trigram Similarity

```sql
SELECT 
    id, 
    partner_code, 
    legal_name, 
    tax_id_value,
    similarity(
        regexp_replace(upper(legal_name), '( S\.A\.C\.| SAC| S\.A\.| SA| E\.I\.R\.L\.| EIRL)', '', 'g'), 
        :normalized_input_name
    ) AS score
FROM business_partners
WHERE organization_id = :org_id
  AND similarity(legal_name, :input_name) >= 0.65
ORDER BY score DESC
LIMIT 5;
```

---

## Clasificación de Alertas de Duplicidad

| Rango de Similitud | Clasificación | Acción del Sistema |
|--------------------|---------------+--------------------+
| **Score >= 0.85** | `HIGH_PROBABILITY_DUPLICATE` | Bloquea la creación automática. La API devuelve `409 Conflict` con la lista de candidatos y exige el flag `override_duplicate_warning=true` para proceder. |
| **0.65 <= Score < 0.85** | `MEDIUM_PROBABILITY_DUPLICATE` | Permite la creación pero registra una alerta en `business_partner_duplicates` para revisión posterior por auditoría. |
| **Score < 0.65** | `NO_DUPLICATE` | El socio se registra limpiamente sin advertencias. |

---

## Esquema de Alertas (`BusinessPartnerDuplicateModel`)

```python
class DuplicateMatchLevel(str, Enum):
    HIGH_PROBABILITY_DUPLICATE = "HIGH_PROBABILITY_DUPLICATE"
    MEDIUM_PROBABILITY_DUPLICATE = "MEDIUM_PROBABILITY_DUPLICATE"

class BusinessPartnerDuplicateModel(Base):
    __tablename__ = "business_partner_duplicates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    source_partner_id = Column(UUID(as_uuid=True), ForeignKey("business_partners.id"), nullable=False)
    candidate_partner_id = Column(UUID(as_uuid=True), ForeignKey("business_partners.id"), nullable=False)
    
    match_level = Column(SQLEnum(DuplicateMatchLevel), nullable=False)
    similarity_score = Column(Numeric(5, 4), nullable=False) # Ej. 0.8850
    
    status = Column(String(20), nullable=False, default="PENDING_REVIEW") # PENDING_REVIEW, CONFIRMED_MERGED, DISMISSED
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
```
