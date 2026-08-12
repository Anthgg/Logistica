# 06. Interfaz Móvil del Conductor (PWA / Mobile View) — Proyecto T1

## 1. Alcance de la Interfaz Móvil

La vista de conductor (`/driver/app`) está optimizada para smartphones con pantallas táctiles pequeñas y conexiones móviles intermitentes:

```text
┌──────────────────────────────────────┐
│ 🚛 ANDESLOG - CONDUCTOR               │
├──────────────────────────────────────┤
│ VIAJE ACTIVO: #TRIP-8842             │
│ Vehículo: Placa ABC-123 (Camión 5T)   │
│ Estado: EN RUTA                      │
├──────────────────────────────────────┤
│ PRÓXIMA PARADA:                      │
│ 🏢 Supermercados Wong - San Isidro   │
│ 📍 Av. Javier Prado Este 2450         │
│ 📦 4 Pallets / 120 Cajas             │
├──────────────────────────────────────┤
│ [ 📍 NAVEGAR CON MAPS / WAZE ]       │
│                                      │
│ [ 🚀 REGISTRAR LLEGADA A PARADA ]    │
│                                      │
│ [ 📝 REGISTRAR ENTREGA (POD) ]       │
│                                      │
│ [ ⚠️ REPORTAR INCIDENCIA EN RUTA ]   │
└──────────────────────────────────────┘
```

---

## 2. Transmisión GPS y Búfer Offline

- **Geolocalización en Segundo Plano:** Utiliza la Geolocation API del navegador móvil para obtener coordenadas cada 30 segundos mientras el viaje esté en estado `IN_TRANSIT`.
- **Búfer de Almacenamiento Local (IndexedDB / LocalStorage):** Si el camión entra en una zona sin cobertura de red móvil, las lecturas GPS y fotos tomadas se almacenan localmente con marca de tiempo UTC. Al restablecerse la conexión de datos, se envían automáticamente al backend en segundo plano.

---

## 3. Captura de Prueba de Entrega Digital (POD)

La pantalla de liquidación de parada permite al conductor capturar 3 tipos de evidencia:
1. **Firma Digital en Pantalla:** Canvas táctil para firma del cliente receptor.
2. **Fotografía de Mercadería Entregada:** Captura directa desde la cámara del smartphone guardada como JPEG comprimido.
3. **Código OTP de Entrega:** Casilla para ingresar el código de 4 dígitos proporcionado por el cliente.
