# 07 — Integración Conductual (Autoencoder)

## Procesamiento de Eventos de Teclado y Mouse

1. **Agregación & Minimización:** `BehavioralInferenceService` procesa características derivadas de la dinámica de tecleo (dwell time, flight time) y trayectorias del mouse (velocidad, curvatura).
2. **Sin Privilegios de Contenido:** Está estrictamente prohibido registrar o capturar contenido de texto, claves o valores ingresados en formularios.
3. **Error de Reconstrucción (MSE):** El modelo Autoencoder evalúa la muestra contra el perfil aprendido del usuario. Si la muestra es insuficiente (`INSUFFICIENT_DATA`), se aplica la regla de señal faltante sin asumir automáticamente legitimidad.
