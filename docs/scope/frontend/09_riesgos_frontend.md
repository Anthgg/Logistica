# 09. Matriz de Riesgos y Decisiones Pendientes Frontend — Proyecto T1

## 1. Riesgos de Interfaz y Rendimiento Web

| ID | Riesgo Identificado | Impacto | Probabilidad | Estrategia de Mitigación |
|---|---|---|---|---|
| R-UI01 | **Saturación del Navegador por Renderizado de Mapas:** Múltiples marcadores GPS actualizándose a alta frecuencia pueden causar lag en la UI. | MEDIO | MEDIA | Aplicar throttling a las actualizaciones de estado (1 render cada 2-3 segundos) y clustering de marcadores en MapLibre. |
| R-UI02 | **Pérdida de Formulario por Expiración de Sesión:** Si la sesión caduca mientras el usuario llena una recepción larga, se podrían perder datos. | ALTO | MEDIA | Guardado automático del borrador en `sessionStorage` antes de enviar la petición a la API. |
| R-UI03 | **Fotos de POD Excesivamente Pesadas:** Fotos en alta resolución desde smartphones móviles pueden congelar la subida con conexión 3G. | ALTO | ALTA | Compresión automática del lado del cliente en el Canvas a una resolución máxima de 1280x720 JPEG (calidad 0.75) antes del envío. |

---

## 2. Decisiones Pendientes Frontend

- **[PENDIENTE DE DECISIÓN] Librería de Gráficos:** Seleccionar entre Chart.js o Recharts para los tableros ejecutivos.
- **[PENDIENTE DE DECISIÓN] Componente de Canvas de Firma:** Evaluar `react-signature-canvas` para la captura de firma táctil en el smartphone del conductor.
