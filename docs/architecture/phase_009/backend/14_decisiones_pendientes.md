# 14 — Decisiones Pendientes

## Decisiones Técnicas y Ajustes de Producción

1. **Calibración Fina de Pesos Multimodales en Producción:** Los pesos de fusión ($w_{\text{face}}=0.35$, $w_{\text{pad}}=0.35$, $w_{\text{behavior}}=0.15$, $w_{\text{session}}=0.15$) están parametrizados en la política y listos para ajuste empírico durante la fase de prueba piloto.
2. **TTL de Retención de Registros de Desafíos Expired/Consumed:** Se recomienda programar una tarea cron periódica para purgar desafíos `CONSUMED` / `EXPIRED` mayores a 30 días en base de datos.
