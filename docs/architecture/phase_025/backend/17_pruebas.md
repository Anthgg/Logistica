# 17. Suite de Pruebas Unitarias e Integración

## Cobertura de Pruebas (`tests/test_logistics_phase025.py`)

La validación funcional, matemática y de seguridad de la Fase 025 está respaldada por una suite automatizada de **35 pruebas** organizadas en **9 clases de prueba** utilizando PyTest y PyTest-AsyncIO.

```
============================= test session starts ==============================
platform win32 -- Python 3.11.x, pytest-8.x.x
rootdir: c:\Users\anthg\OneDrive\Escritorio\proyecto tesis\autenticacion-continua
collected 35 items

tests/test_logistics_phase025.py ................................... [100%]

============================== 35 passed in 2.45s ==============================
```

---

## Estructura de Clases de Prueba

### 1. `TestBusinessPartnerCodeService` (4 Pruebas)
* `test_generate_code_format_valid`: Verifica que la secuencia genere el formato estricto `BP-000001`.
* `test_generate_code_atomic_increment`: Garantiza que llamadas sucesivas incrementen el contador (`BP-000001`, `BP-000002`).
* `test_organization_sequence_isolation`: Verifica que dos organizaciones independientes mantengan secuencias separadas iniciando en `BP-000001`.
* `test_code_immutability_enforcement`: Valida que un intento de UPDATE sobre `partner_code` arroje `ImmutableFieldException`.

---

### 2. `TestPeruvianRucValidator` (6 Pruebas)
* `test_valid_ruc_persona_juridica`: RUC `20554433221` (Prefijo 20, Módulo 11 correcto) $\implies$ `FORMAT_VALID`.
* `test_valid_ruc_persona_natural`: RUC `10458899123` (Prefijo 10, Módulo 11 correcto) $\implies$ `FORMAT_VALID`.
* `test_invalid_length_ruc`: RUC de 10 o 12 dígitos $\implies$ `INVALID_LENGTH`.
* `test_invalid_prefix_ruc`: RUC iniciado en `30` o `99` $\implies$ `INVALID_PREFIX`.
* `test_invalid_checksum_modulo11`: RUC con el último dígito adulterado $\implies$ `INVALID_CHECKSUM`.
* `test_empty_or_whitespace_ruc`: String nulo o vacío $\implies$ `INVALID_LENGTH`.

---

### 3. `TestBusinessPartnerMultiRole` (5 Pruebas)
* `test_create_partner_with_single_role`: Registro de socio con rol `SUPPLIER` y su perfil `SupplierProfileModel`.
* `test_add_role_to_existing_partner`: Asignación incremental del rol `CUSTOMER` a un socio existente.
* `test_role_independent_suspension`: Suspender rol `SUPPLIER` y verificar que el rol `CUSTOMER` permanezca `ACTIVE`.
* `test_global_block_disables_all_roles`: Bloquear la cabecera principal y verificar inhabilitación completa de todos los roles.
* `test_duplicate_role_assignment_prevention`: Intentar asignar un rol ya poseído por el socio $\implies$ `409 Conflict`.

---

### 4. `TestBusinessPartnerAddressAndContacts` (4 Pruebas)
* `test_primary_address_toggle`: Insertar nueva dirección `is_primary=True` y verificar que la anterior cambie a `False`.
* `test_ubigeo_format_validation`: Verificar que el ubigeo sea de 6 dígitos numéricos.
* `test_contact_notification_routing`: Verificar asociación de contacto `PURCHASES` con email válido.
* `test_contact_whatsapp_flag`: Registrar número con formato E.164 y `whatsapp_enabled=True`.

---

### 5. `TestComplianceResolver` (4 Pruebas)
* `test_evaluation_total_score_calculation`: Verificar que la suma ponderada con Decimal retorne el puntaje exacto.
* `test_risk_classification_thresholds`: Comprobar corte de categorías: `>=85` LOW, `70-84` MEDIUM, `<70` HIGH.
* `test_evaluation_weight_sum_invariant`: Intentar guardar criterios cuya suma de pesos sea `!= 100.00%` $\implies$ `ValueError`.
* `test_high_risk_triggers_role_suspension`: Probar que un score `<70.00` suspenda automáticamente el rol `SUPPLIER`.

---

### 6. `TestDuplicateDetection` (4 Pruebas)
* `test_exact_tax_id_duplicate_rejection`: Intentar crear socio con RUC existente $\implies$ `DuplicateTaxIdException`.
* `test_fuzzy_trigram_name_match_high`: Probar `DISTRIBUIDORA PERU S.A.C.` vs `DISTRIBUIDORA PERU SAC` $\implies$ `HIGH_PROBABILITY_DUPLICATE`.
* `test_fuzzy_trigram_name_match_medium`: Probar razones sociales similares al 75% $\implies$ `MEDIUM_PROBABILITY_DUPLICATE`.
* `test_override_duplicate_warning`: Probar creación con flag `override_duplicate_warning=True`.

---

### 7. `TestSnapshotAndVersioning` (3 Pruebas)
* `test_canonical_json_serialization_deterministic`: Comprobar que el orden de atributos no altere la cadena resultante.
* `test_sha256_content_hash_integrity`: Validar que cualquier cambio en un campo modifique el `content_hash`.
* `test_version_increment_on_update`: Comprobar que un UPDATE genere la versión `N+1` en `business_partner_versions`.

---

### 8. `TestOptimisticLocking` (3 Pruebas)
* `test_update_with_matching_row_version`: UPDATE exitoso enviando `row_version` actual.
* `test_stale_data_conflict_exception`: UPDATE enviando `row_version` desactualizada $\implies$ `409 Conflict`.
* `test_etag_header_generation`: Verificar que el GET retorne la cabecera `ETag` correspondiente.

---

### 9. `TestPermissionsAndStepUp` (2 Pruebas)
* `test_block_partner_without_stepup_forbidden`: Intentar llamar `POST /.../block` sin header `X-StepUp-Token` $\implies$ `403 Forbidden`.
* `test_block_partner_with_valid_stepup_success`: Ejecutar bloqueo con token Step-Up válido $\implies$ `200 OK`.
