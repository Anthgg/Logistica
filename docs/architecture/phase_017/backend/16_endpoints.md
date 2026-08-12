# Endpoints de la Familia INVENTORY (Phase 017)

## Rutas Registradas
Los endpoints están bajo el prefijo `/api/logistics/inventory` con la etiqueta `Logistics - Inventory Documents`:

1. `POST /documents/{document_type_code}/preview`
   - Genera el PDF en memoria y lo retorna en la respuesta con cabeceras de previsualización inline.
   - Parámetro opcional: `blind_count_mode` (booleano).
2. `POST /documents/{document_type_code}/pdf`
   - Genera y retorna el PDF configurado para descarga directa de archivo.
3. `POST /document-package/manifest`
   - Evalúa y retorna el JSON del manifiesto del paquete documental de inventario.

## Protección
Todos los endpoints requieren el rol/permiso `logistics.documents.read` inyectado a través del dependency injection de `LogisticsPrincipal`.
