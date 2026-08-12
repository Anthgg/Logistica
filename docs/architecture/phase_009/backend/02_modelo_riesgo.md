# 02 — Modelo de Riesgo y Adaptadores de Señal

## Adaptadores de Normalización

1. **`FaceRiskAdapter`:** Convierte la similitud coseno $S \in [0, 1]$ en un puntaje de riesgo:
   $$R_{\text{face}} = \text{clamp}\left(1.0 - \frac{S - S_{\text{min}}}{S_{\text{max}} - S_{\text{min}}}, 0.0, 1.0\right)$$
   * Umbral base: $S_{\text{min}} = 0.40$, $S_{\text{max}} = 0.75$.

2. **`PadRiskAdapter`:** Convierte la probabilidad de autenticidad bona fide $P \in [0, 1]$ en riesgo:
   $$R_{\text{pad}} = 1.0 - P$$
   * Si ocurre un error de lectura o ataque detectado: $R_{\text{pad}} = 1.0$.

3. **`BehaviorRiskAdapter`:** Normaliza el error de reconstrucción MSE del Autoencoder:
   $$R_{\text{behavior}} = \text{clamp}\left(\frac{\text{MSE} - \text{MSE}_{\text{normal}}}{\text{MSE}_{\text{critical}} - \text{MSE}_{\text{normal}}}, 0.0, 1.0\right)$$

4. **`SessionRiskAdapter`:** Mapea las anomalías de sesión/dispositivo directamente al rango $[0.0, 1.0]$.

## Fusión de Riesgo Ponderada (`RiskFusionService`)

$$\text{Riesgo Combinado} = w_{\text{face}} \cdot R_{\text{face}} + w_{\text{pad}} \cdot R_{\text{pad}} + w_{\text{behavior}} \cdot R_{\text{behavior}} + w_{\text{session}} \cdot R_{\text{session}}$$

Pesos por defecto (`RISK_POLICY_VERSION = "1.0.0"`):
* $w_{\text{face}} = 0.35$
* $w_{\text{pad}} = 0.35$
* $w_{\text{behavior}} = 0.15$
* $w_{\text{session}} = 0.15$
