# 32 — Contrato de Integración Downstream con la Fase 027 (Ubigeos y Direcciones)

## 1. Vinculación Territorial mediante Código Ubigeo (6 Dígitos)

El código de 6 dígitos `ubigeo_code` (ej. `150101` para Lima, Lima, Lima) presente en los registros del padrón RUC y locales anexos sirve como clave foránea virtual hacia la infraestructura de Ubigeos que se implementará en la **Fase 027**.

```mermaid
erDiagram
    RUC_REGISTRY_ENTRIES {
        string ruc
        string ubigeo_code FK
    }
    RUC_REGISTRY_ANNEX_ADDRESSES {
        string ruc
        string ubigeo_code FK
    }
    MAESTRO_UBIGEOS_FASE_027 {
        string ubigeo_code PK
        string departamento
        string provincia
        string distrito
    }

    RUC_REGISTRY_ENTRIES ||--o{ MAESTRO_UBIGEOS_FASE_027 : "Valida Territorialidad"
    RUC_REGISTRY_ANNEX_ADDRESSES ||--o{ MAESTRO_UBIGEOS_FASE_027 : "Asigna Georreferencia"
```

---

## 2. Garantía de Compatibilidad

Los componentes de la Fase 026 exportan el método `validate_ubigeo_format(code: str) -> bool` garantizando que solo códigos de 6 dígitos numéricos normalizados sean almacenados, asegurando migración limpia hacia los modelos de la Fase 027.
