# Informe de preparación para producción — Fase 7.5

**Estado: `not_ready`**

Escala permitida: `not_ready`, `pilot_only`, `ready_for_controlled_deployment` y `ready_for_limited_production`. Los dos últimos estados requieren evaluación propia congelada y aprobación humana; no se derivan automáticamente de una métrica alta.

Este estado se deriva únicamente de artefactos verificables; no se fabricaron métricas.

## Evidencia

```json
{
  "generated_at": "2026-07-26T08:15:56.849469+00:00",
  "downloaded_datasets": [],
  "pad_completed_experiments": 0,
  "behavioral_completed_experiments": 0,
  "frozen_test_consumed": false
}
```

## Generalización

Pendiente de resultados cross-dataset y pruebas propias.

## Ataques no vistos

No demostrado; deben incluirse impresiones, teléfono y monitor.

## Dispositivos no vistos

Pendiente de cámaras y equipos reales de la operación.

## Iluminación

Pendiente de estratificación por condiciones reales.

## Sesgo

Requiere análisis por participante, dispositivo y contexto.

## Falsos positivos

No estimados en prueba propia congelada.

## Falsos negativos

No estimados en prueba propia congelada.

## Latencia

Debe medirse con el artefacto candidato en Cloud Run.

## Memoria

Debe medirse con límites reales del servicio.

## Disponibilidad de cámara

Definir reverificación y modo degradado.

## Cambios conductuales

Evaluar día, fatiga, hardware, navegador y actividad.

## Drift

Monitorear distribuciones; nunca reentrenar automáticamente.

## Privacidad

Conservar solo timings/coordenadas normalizadas y trazabilidad.

## Licencias

Los datasets restringidos siguen bloqueados hasta acuerdo.

## Limitaciones

Un benchmark externo no garantiza ausencia de fallos en producción.

## Monitoreo posterior

- Distribución agregada de scores y drift de características.
- Reverificaciones, falsas alertas reportadas y fallos de cámara.
- Activación de modo degradado, latencia y versiones desplegadas.
- Sin eventos crudos, texto, teclas, imágenes ni reentrenamiento automático.

Todo nuevo entrenamiento requiere consentimiento, versión de dataset, splits separados, evaluación, aprobación y despliegue controlado.
