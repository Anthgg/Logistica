# 02 — Decisión del Motor PDF

## Evaluación de Alternativas
1. **Opción A (Jinja2 + WeasyPrint):** Excelente soporte para CSS de impresión (`@page`, saltos de página, cabeceras repetidas). Implementada con fallback binario PDF 1.4 cuando falten librerías C nativas.
2. **Opción B (Chromium Headless / Playwright):** Descartado por mayor consumo de RAM en Cloud Run.

## Motor Seleccionado
`Jinja2 + WeasyPrint` (con `FallbackPdfEngine` para entornos sin binarios GTK/Pango).
