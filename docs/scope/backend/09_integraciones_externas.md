# 09. Integraciones Externas — Proyecto T1

## 1. Mapa de Integraciones

| Servicio / Entidad | Finalidad Funcional | Datos Enviados | Datos Recibidos | Estrategia Técnica / Fallback |
|---|---|---|---|---|
| **SUNAT (Consulta RUC)** | Validar Razón Social, Dirección Fiscal y Estado del RUC (Habido/Activo). | Número de RUC (11 dígitos). | Razón Social, Condición, Ubigeo, Dirección. | API Oficial SUNAT / Padrón Reducido en Base de Datos local con actualización semanal. |
| **SUNARP (Vehículos)** | Consulta de características del vehículo por placa. | Número de Placa. | Marca, Modelo, Serie, Nro Motor, Propietario. | Entrada manual asistida con verificación documental. No scraping automático con CAPTCHA. |
| **MTC (Conductores)** | Verificación de validez y categoría de Licencia de Conducir. | Número de DNI / Licencia. | Categoría, Estado (Vigente/Suspendida), Vencimiento. | Verificación en Padrón MTC local / Validación manual asistida. |
| **SBS / Aseguradoras** | Verificación de vigencia de SOAT y Revisión Técnica (CITV). | Número de Placa / DNI. | Estado SOAT, Aseguradora, Fecha Vencimiento. | Registro manual de póliza con adjunto PDF de evidencia en Cloud Storage. |
| **Proveedor Geocodificación** | Convertir direcciones de entrega a coordenadas Latitud/Longitud. | Dirección de entrega textual. | Latitud, Longitud, Nivel de precisión. | Nominatim / OpenStreetMap API con caché en PostgreSQL. |
| **Motor de Rutas (Valhalla / OSRM)** | Calcular distancias, tiempos de viaje y matriz de distancias. | Lista de coordenadas paradas. | Geometría de ruta, distancia (km), tiempo estimado (min). | Instancia local/contenedor Docker de OSRM / Valhalla. |
| **Cloud Storage (GCS / S3)** | Almacenar PDFs de guías, actas e imágenes POD/incidencias. | Stream binario de archivo + metadatos. | URL firmada (Presigned URL) de acceso temporal. | Cliente oficial `google-cloud-storage` o `boto3`. |
| **Proveedor SMS / OTP** | Envío de códigos OTP de re-autenticación y notificaciones de entrega. | Teléfono destino + Código OTP / Mensaje. | ID de envío, Estado de entrega. | Twilio / MessageBird / AWS SNS API. |
| **MapLibre (Frontend)** | Renderizador de mapas dinámicos en cliente web/móvil. | Tiles vectoriales / Coordenadas. | Renderizado gráfico en pantalla. | Tiles de OpenStreetMap / CartoDB libres. |

---

## 2. Restricciones Técnicas y Legales

1. **PROHIBICIÓN ABSOLUTA DE SCRAPING CON CAPTCHA:** El backend no incluirá librerías de evadir CAPTCHAs para portales gubernamentales. Toda consulta a SUNAT/MTC se hará por API oficial o padrones descargables.
2. **Caché Obligatorio de RUCs:** Toda consulta exitosa de RUC se almacenará en la tabla `business_partners` por un mínimo de 30 días para evitar saturar llamadas externas.
3. **Manejo de Caídas:** Si el servicio externo de geocodificación no responde en 2.5 segundos, el backend aceptará la creación de la dirección con coordenadas (0,0) etiquetada como `PENDING_GEOCODING`.
