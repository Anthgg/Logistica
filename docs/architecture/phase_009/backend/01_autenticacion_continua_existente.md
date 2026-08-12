# 01 — Auditoría de Autenticación Continua Existente

## Componentes Analizados

| Componente | Estado | Servicio / Clase | Entrada | Salida | Escala Puntaje | Datos Persistidos |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ArcFace / InsightFace** | `IMPLEMENTED` | `FacialInferenceService` | Imagen facial / Bounding Box | 512d Embedding / Similaridad Coseno | 0.0 a 1.0 (Similitud) | Vector Cifrado DB |
| **PAD (Presentation Attack)** | `IMPLEMENTED` | `PadInferenceService` | Imagen facial | Probabilidad Bona Fide | 0.0 a 1.0 (Autenticidad) | Registro de evaluación |
| **Autoencoder Conductual** | `IMPLEMENTED` | `BehavioralInferenceService` | Eventos Teclado/Mouse | Error de Reconstrucción (MSE) | $\ge 0.0$ (Error MSE) | Muestras minimizadas |
| **Riesgo de Sesión & Dispositivo** | `IMPLEMENTED` | `RiskDecisionService` | IP, Huella Dispositivo, Recencia | Nivel de Riesgo Aplicado | LOW, MEDIUM, HIGH, CRITICAL | Sesiones / Dispositivos |

## Riesgos e Información Sensible
* Los datos biométricos crudos y plantillas están aislados en el dominio de identidad.
* Ningún endpoint del dominio logístico devuelve embeddings ni imágenes faciales.
