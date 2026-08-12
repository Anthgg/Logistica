# 22 — Decisiones Pendientes

## 1. Tipo `NI` no insertado en migración `g660970016dc`
**Situación:** La migración insertó CIT, CPV, AREC, DIF y NC en `document_types`, pero omitió NI.  
**Razón:** NI puede existir como tipo genérico en el catálogo base.  
**Acción requerida:** Verificar si `NI` ya existe en `document_types` antes de Fase 017. Si no existe, agregar en una sub-migración o en la migración de Fase 017.

---

## 2. Subfamilia de NI vs AREC
**Situación:** NI y AREC comparten la familia `INBOUND` pero operativamente son diferentes: AREC es de recepción física y NI es de registro de almacén.  
**Opción A:** Mantener ambas en `INBOUND` (actual).  
**Opción B:** Crear subfamilia `INBOUND_WAREHOUSE` para NI.  
**Decisión pendiente:** A confirmar con el usuario en Fase 017.

---

## 3. CPV para Salidas Vehiculares
**Situación:** El CPV actual solo modela eventos de **ingreso** (`gate_event_type = "INGRESO"`).  
**Pendiente:** ¿Debe el CPV registrar también las salidas del vehículo post-descarga? Esto afectaría:
- El template HTML (añadir campo `departure_at`)
- La lógica del gate_event_type (INGRESO / SALIDA / PERMANENCIA)  
**Acción:** Confirmar con el usuario si el control de salidas es requerido en Fase 017 o posterior.

---

## 4. Validación de Invariante de Cantidades
**Situación:** La invariante `received = accepted + rejected` no se valida en Fase 016 (modo preview).  
**Acción:** Agregar validación `@model_validator` en `InboundItemSchema` cuando el AREC sea documento oficial en Fase 041.
