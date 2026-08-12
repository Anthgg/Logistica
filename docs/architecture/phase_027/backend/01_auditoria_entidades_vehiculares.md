# Auditoría de Entidades Vehiculares Previas y Justificación Relacional

## 1. Auditoría de Modelos Previos

Antes del diseño e implementación de la Fase 027, se realizó una inspección exhaustiva de todo el repositorio (`src/backend/app/models`, `src/backend/app/schemas`, y migraciones de Alembic previas a `r300110027dc`).

### Resultado de la Auditoría:
* **Entidades previas identificadas**: 0 (cero). No existía ninguna tabla relacional, esquema Pydantic ni modelo ORM referente a vehículos, flotas, placas, SOAT ni capacidades mecánicas.
* **Fases previas reutilizadas**:
  * **Fase 024**: Tablas `logistics_units_of_measure` y `logistics_unit_conversions` para el manejo formal de unidades de masa (kg, t) y volumen ($m^3$, $l$).
  * **Fase 025**: Tabla `logistics_business_partners` (específicamente registros con rol `CARRIER`) para la asignación de transportistas externos autorizados.
  * **Fase 001/002**: Motor de auditoría inmutable `logistics_audit_events` y control multi-tenant por `organization_id`.

---

## 2. Justificación Arquitectónica de las 13 Tablas Relacionales

Para evitar modelos "monolíticos" con campos nulos excesivos y mantener el principio de responsabilidad única (SRP), la Fase 027 divide el dominio vehicular en 13 tablas especializadas:

```
+------------------------------------------------------------------------------------+
|                                  DOMINIO VEHICULAR                                 |
+------------------------------------------------------------------------------------+
| 1. logistics_vehicles                      (Entidad Raíz y Estado)                 |
| 2. logistics_vehicle_makes                 (Catálogo de Marcas)                    |
| 3. logistics_vehicle_models                (Catálogo de Modelos)                   |
| 4. logistics_vehicle_capacity_profiles     (Capacidades en Peso/Volumen - Decimals)|
| 5. logistics_vehicle_dimensions            (Largo, Ancho, Alto, Vol. Interno)      |
| 6. logistics_vehicle_ownership_assignments (Historial y Tipo de Propiedad)         |
| 7. logistics_vehicle_carrier_assignments   (Historial de Asignación a Transportista)|
| 8. logistics_vehicle_documents             (Expediente Documental: SOAT, CITV)     |
| 9. logistics_vehicle_document_requirements (Matriz de Reglas Documentales)        |
| 10. logistics_vehicle_operational_restrictions (Bloqueos Manuales y Sanciones)     |
| 11. logistics_vehicle_plate_assignments    (Trazabilidad de Cambios de Placa)      |
| 12. logistics_vehicle_aliases              (Placas Anteriores y Códigos Alternos)  |
| 13. logistics_vehicle_versions             (Snapshots Inmutables SHA-256)          |
+------------------------------------------------------------------------------------+
```

### Detalle de Justificación por Tabla

1. `logistics_vehicles`: Representa la entidad central (vehículo) manteniendo identificadores únicos (`id`, `vehicle_code`, `normalized_plate`, `normalized_vin`) y los estados en tiempo real (`lifecycle_status`, `operational_status`, `compliance_status`).
2. `logistics_vehicle_makes`: Evita inconsistencias de texto libre (ej: "Toyota", "TOYOTA", "toyota") estandarizando las marcas a nivel de sistema u organización.
3. `logistics_vehicle_models`: Mantiene la jerarquía Modelo -> Marca, asociando características predeterminadas de fábrica.
4. `logistics_vehicle_capacity_profiles`: Separa la matemática de capacidades (peso bruto, tara, carga útil) con referencias a unidades de medida de la Fase 024. Permite recalcular perfiles por modificaciones estructurales sin alterar la cabecera.
5. `logistics_vehicle_dimensions`: Almacena dimensiones físicas exteriores e interiores. Facilita la validación geométrica en almacenes y bahías de carga.
6. `logistics_vehicle_ownership_assignments`: Permite rastrear la evolución de la propiedad de la unidad (compra propia, leasing, alquiler, tercero) a lo largo del tiempo con rangos de fechas (`effective_from`, `effective_to`).
7. `logistics_vehicle_carrier_assignments`: Desacopla al vehículo del transportista. Una unidad de un tercero puede ser asignada a diferentes empresas de transporte en distintas fechas.
8. `logistics_vehicle_documents`: Guarda los metadatos y enlaces a documentos legales obligatorios (SOAT, Inspección Técnica, Tarjeta de Propiedad, Permiso MTC) con fechas de emisión y vencimiento.
9. `logistics_vehicle_document_requirements`: Define las reglas de negocio sobre qué documentos son obligatorios y si causan bloqueo inmediato al vencer según el tipo de vehículo.
10. `logistics_vehicle_operational_restrictions`: Permite registrar bloqueos operativos administrativos o mecánicos con nivel de gravedad y flujo de des-bloqueo auditado.
11. `logistics_vehicle_plate_assignments`: Registra cada cambio de placa que sufre el vehículo (por re-matriculación SUNARP), preservando la vigencia histórica.
12. `logistics_vehicle_aliases`: Registra placas previas y códigos secundarios para garantizar que búsquedas por placas antiguas encuentren la unidad actual.
13. `logistics_vehicle_versions`: Almacena snapshots JSON codificados con SHA-256 para auditorías forenses, asegurando inmutabilidad ante disputas legales o inspecciones MTC.
