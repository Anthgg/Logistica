# 06 — Integración Facial (ArcFace/InsightFace) y Detección de Ataques (PAD)

## Flujo Biométrico Facial

1. **Captura:** El cliente transmite la imagen capturada durante el desafío mediante `POST /api/logistics/security/step-up/challenges/{id}/factors`.
2. **Detección de Ataques (PAD):** `PadInferenceService` evalúa si la captura corresponde a una presentación bona fide o a un ataque (pantalla, foto impresa, video). Si el PAD detecta un ataque, el desafío se bloquea inmediatamente (`LOCKED`/`FAILED`) y se emite un evento de auditoría `logistics.security.pad_attack_detected`.
3. **Verificación Facial:** Si el PAD resulta `BONA_FIDE`, `FacialInferenceService` extrae el embedding ArcFace/InsightFace y calcula la similitud coseno contra el embedding de enrolamiento del usuario.
4. **Privacidad:** La imagen recibida NO se guarda en tablas del dominio logístico ni se incluye en los registros de auditoría. Se procesa en memoria volatil durante la verificación.
