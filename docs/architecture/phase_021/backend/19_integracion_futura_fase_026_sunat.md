# 19. Desacoplamiento de Integración SUNAT y Consulta RUC (Fase 026)

## 🌐 Justificación del Desacoplamiento

Durante la concepción de la Fase 021, se evaluó la posibilidad de conectar la actualización del perfil directamente a servicios de consulta web externos (APIs de SUNAT o Padrón Reducido RUC).

Sin embargo, para mantener la arquitectura de microservicios limpia y evitar fallos en cascada o dependencia de servicios gubernamentales de disponibilidad variable durante la configuración inicial de la empresa, la arquitectura adopta un **Desacoplamiento Estricto**:

```mermaid
graph TD
    subgraph Fase 021 - Ficha Institucional (Local & Autónoma)
        A[Ingreso de RUC / Datos Legales] --> B[Validación Módulo 11 Local - Instantánea]
        B --> C[Estado verification_status = 'FORMAT_VALID']
        C --> D[Permite Operación y Emisión Interna Logística]
    end

    subgraph Fase 026 - Integración Comprobantes & SUNAT (Futuro)
        E[Worker Asíncrono / Consulta SUNAT] --> F{¿Consulta Padrón RUC OK?}
        F -- Sí --> G[Actualiza verification_status = 'SUNAT_VERIFIED']
        F -- No --> H[Alerta Administrativa: Inconsistencia con SUNAT]
    end
```

---

## 📌 Principios del Modelo de Integración Diferida (Fase 026)

1. **Autonomía Operativa**: El sistema opera sin internet o con APIs externas caídas. La validación del RUC se realiza con el algoritmo Módulo 11 en la propia aplicación.
2. **Evolución del Estado `verification_status`**:
   * En Fase 021: Nace como `FORMAT_VALID`.
   * En Fase 026: Una tarea en segundo plano (Background Worker) consultará la validez del RUC, la Condición de Habido y el Estado de Activo en SUNAT, promoviendo el estado a `SUNAT_VERIFIED` y registrando `verification_source = 'SUNAT_PADRON_API'`.
3. **Emisión de Comprobantes Electrónicos (SEE-SUNAT)**: En la Fase 026, la información institucional congelada en el snapshot (RUC, Razón Social, Dirección Fiscal, Ubigeo) será utilizada para construir la trama XML UBL 2.1 exigida por los Operadores de Servicios Electrónicos (OSE / SUNAT).
