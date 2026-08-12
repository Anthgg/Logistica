# 23. Decisiones de Diseño Pendientes

Lista de debates técnicos y decisiones que se consolidarán en la Fase 021:

- **Estrategia de purga de archivos ZIP de exportación**: Determinar si las exportaciones expiradas se eliminan físicamente del disco mediante un cron job nocturno o si se conservan para auditoría histórica a largo plazo.
- **Integración con impresoras térmicas cebra (ZPL)**: Considerar si el motor de renderizado debe soportar la exportación del snapshot a lenguaje ZPL nativo además de PDF para etiquetas de putaway.
