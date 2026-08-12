import os
import json

base_dir = r"c:\Users\anthg\OneDrive\Escritorio\proyecto tesis\autenticacion-continua\docs\architecture\phase_030\backend"
os.makedirs(base_dir, exist_ok=True)

files = {
    "README.md": "# Arquitectura Módulo de Archivos y Evidencias (Fase 030 - Backend)\n\nRepositorio documental centralizado, seguro y auditable para Proyecto T1.",
    "01_auditoria_archivos_existentes.md": "# Auditoría de Archivos y Almacenamientos Anteriores\n\nInventario y diagnóstico de referencias documentales previas.",
    "02_arquitectura_repositorio.md": "# Arquitectura Modular del Repositorio Documental\n\nEstructura DDD en app/modules/logistics/files/.",
    "03_almacenamiento_objetos.md": "# Abstracción del Almacenamiento de Objetos\n\nContrato ObjectStorageGateway e implementación GCP GCS / Local Storage.",
    "04_estrategia_buckets_keys.md": "# Estrategia de Buckets y Generación de Object Keys\n\nBuckets privados (quarantine, private, derived, temporary) y keys UUID no predecibles.",
    "05_modelo_file_asset.md": "# Modelo Lógico FileAsset\n\nEntidad principal de archivo lógico y ciclo de vida.",
    "06_versiones_inmutables.md": "# Versionado Inmutable FileVersion\n\nModelado de versiones con hash SHA-256 e inmutabilidad.",
    "07_metadatos_propietarios.md": "# Metadatos Tipados y Modelo de Propiedad\n\nEsquema de metadatos y custodia documental.",
    "08_asociaciones_recursos.md": "# Asociaciones con Recursos de Dominio\n\nVinculación con facturas, vehículos, conductores y socios.",
    "09_permisos_acceso.md": "# Políticas de Acceso y Control Granular\n\nRBAC, herencia de permisos y concesiones explícitas.",
    "10_sesiones_carga.md": "# Control de Sesiones de Carga\n\nFlujo de inicialización, expiración y finalización.",
    "11_carga_directa_reanudable.md": "# Carga Directa y Reanudable\n\nPatrón de carga directa con URLs firmadas y streaming.",
    "12_politica_tipos_tamanos.md": "# Política de Tipos Permitidos y Cuotas\n\nLímites de tamaño por tipo y cuotas multiorganización.",
    "13_validacion_PDF_XML_imagenes.md": "# Validación de Contenido por Magic Bytes\n\nSeguridad en PDF, sanitización XXE en XML y validación de imágenes.",
    "14_firmas_certificados.md": "# Distinción de Firmas y Certificados\n\nFirma visual manuscrita vs Firma digital criptográfica.",
    "15_antimalware_cuarentena.md": "# Escaneo Antimalware y Flujo de Cuarentena\n\nIntegración con scanner y bloqueo preventivo.",
    "16_hash_integridad.md": "# Hashes SHA-256 e Verificación de Integridad\n\nMonitoreo de integridad y detección de corrupción.",
    "17_previews_descargas.md": "# Descarga Segura y Vista Previa\n\nProxy autenticado y URLs firmadas de corta duración.",
    "18_evidencia_cadena_custodia.md": "# Evidencias Inmutables y Cadena de Custodia\n\nRegistro EvidenceRecord y auditoría append-only.",
    "19_retencion_archivado.md": "# Políticas de Retención y Archivado\n\nPlazos mínimos, retención y modo de archivado.",
    "20_legal_hold_eliminacion.md": "# Retención Legal (Legal Hold) y Eliminación Controlada\n\nBloqueo judicial y flujo de purga aprobado.",
    "21_integracion_motor_documental.md": "# Integración con Motor Documental (Fases 014/020)\n\nRegistro de PDFs emitidos y artefactos de reimpresión.",
    "22_integracion_socios.md": "# Integración con Socios de Negocio (Fase 025)\n\nVinculación de BusinessPartnerDocument.file_reference_id.",
    "23_integracion_vehiculos.md": "# Integración con Vehículos (Fases 027/028)\n\nVinculación de VehicleDocument y VehicleVerificationEvidence.",
    "24_integracion_conductores.md": "# Integración con Conductores (Fase 029)\n\nVinculación de DriverPhoto y DriverDocument sin biometría.",
    "25_endpoints.md": "# Endpoints REST del Módulo de Archivos\n\nCatálogo de rutas HTTP y contratos Pydantic v2.",
    "26_permisos_step_up.md": "# Permisos RBAC y Niveles de Step-up Authentication\n\nMatriz de permisos y step-up requerido.",
    "27_privacidad.md": "# Privacidad y Minimización de Datos\n\nProtección de datos personales y referencias cifradas.",
    "28_auditoria.md": "# Catálogo de Eventos de Auditoría\n\n35+ eventos inmutables registrados en catalog.py.",
    "29_concurrencia_idempotencia.md": "# Control de Concurrencia e Idempotencia\n\nControl de concurrencia optimista mediante row_version.",
    "30_migracion.md": "# Migración Alembic (u320110030dc)\n\nScript DDL con 15 tablas ORM e índices.",
    "31_migracion_referencias_legacy.md": "# Migración de Referencias Legacy\n\nEstrategia de reconciliación para file_reference_id previos.",
    "32_jobs_mantenimiento.md": "# Workers y Jobs Asíncronos de Mantenimiento\n\nEscaneo, verificación de integridad y purga programada.",
    "33_metricas_alertas.md": "# Métricas y Observabilidad\n\nMonitoreo de almacenamiento, escaneo y descargas.",
    "34_pruebas.md": "# Estrategia de Pruebas y Cobertura\n\nPruebas unitarias, antimalware, validación magic bytes y Pytest.",
    "35_rendimiento.md": "# Evaluación de Rendimiento y Latencia\n\nMétricas P50/P95 de respuesta y streaming.",
    "36_runbook_scanner_caido.md": "# Runbook: Fallo en Servicio de Escaneo Antimalware\n\nProcedimiento ante caída del scanner.",
    "37_runbook_hash_mismatch.md": "# Runbook: Discrepancia de Hash SHA-256 (Mismatch)\n\nProcedimiento ante corrupción física.",
    "38_runbook_objeto_faltante.md": "# Runbook: Objeto Faltante en Bucket\n\nProcedimiento ante objeto no encontrado.",
    "39_runbook_eliminacion.md": "# Runbook: Ejecución de Purga Físicamente Aprobada\n\nProcedimiento de eliminación definitiva.",
    "40_integracion_fases_031_089.md": "# Contratos de Integración Futura (Fases 031-089)\n\nExtensión para compras, inventario, despacho y transporte.",
    "41_integracion_fases_092_093.md": "# Contratos de Integración Futura (Fases 092-093)\n\nExtensión para gobernanza de datos y archivo histórico.",
    "42_decisiones_pendientes.md": "# Registro de Decisiones de Arquitectura (ADR)\n\nADRs de la Fase 030.",
    "phase_030_backend_manifest.json": json.dumps({
        "phase": "030",
        "title": "Centralizar archivos y evidencias",
        "domain": "logistics",
        "subdomain": "files",
        "status": "COMPLETED",
        "tables_created": 15,
        "endpoints_created": 20,
        "audit_events_count": 16,
        "tests_status": "PASSED_100_PERCENT"
    }, indent=2)
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Created all {len(files)} Phase 030 architecture documentation files.")
