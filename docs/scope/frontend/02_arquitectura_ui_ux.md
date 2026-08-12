# 02. Arquitectura UI/UX y Sistema de Diseño — Proyecto T1

## 1. Sistema de Diseño (Design System)

El frontend utilizará **Vanilla CSS** con tokens de diseño definidos en variables CSS globales (`index.css`), garantizando máximo control, rendimiento y estética visual de primer nivel (Glassmorphism, sombras suaves, micro-animaciones y paleta tailoreada):

```css
:root {
  /* Colors */
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: rgba(30, 41, 59, 0.7);
  --accent-blue: #0284c7;
  --accent-cyan: #06b6d4;
  --text-primary: #f8fafc;
  --text-muted: #94a3b8;
  --border-subtle: rgba(255, 255, 255, 0.1);
  --status-success: #10b981;
  --status-warning: #f59e0b;
  --status-danger: #ef4444;
  --status-info: #3b82f6;

  /* Typography */
  --font-family: 'Inter', system-ui, -apple-system, sans-serif;
  --radius-md: 8px;
  --radius-lg: 12px;
  --transition-fast: 150ms ease-in-out;
}
```

---

## 2. Layout Principal de la SPA (`AppLayout`)

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ HEADER / TOPBAR (Logo, Búsqueda global, Score Autenticación Continua, User)│
├──────────────┬─────────────────────────────────────────────────────────────┤
│ SIDEBAR      │ MAIN CONTENT AREA                                           │
│ (Navegación) │                                                             │
│              │ ┌─────────────────────────────────────────────────────────┐ │
│ 📦 Maestros  │ │ BREADCRUMB / ACCIONES RÁPIDAS                             │ │
│ 📥 Abast.    │ ├─────────────────────────────────────────────────────────┤ │
│ 🏭 Almacén   │ │                                                         │ │
│ 🚚 Rutas     │ │ VISTA ACTIVA (Tablas paginadas, Mapas MapLibre,         │ │
│ 📈 KPIs      │ │ Formularios glassmorphism, Gráficos)                    │ │
│ 🔒 Auditoría │ │                                                         │ │
│              │ └─────────────────────────────────────────────────────────┘ │
├──────────────┴─────────────────────────────────────────────────────────────┤
│ FOOTER (Estado conexión API, Versión sistema, Indicador de sincronización) │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Componente de Mapa Interactivo (MapLibre GL JS)

Para el monitoreo de vehículos en tiempo real y planificación de rutas, el módulo `TrackingMap` integrará MapLibre GL JS:
- **Capa Vectorial de Mapa:** Tiles de OpenStreetMap libres servidas con estilo oscuro.
- **Marcadores Dinámicos:** Iconos vectoriales rotados según el rumbo (heading) del vehículo.
- **Capas Polilínea:** Trazado de ruta planificada vs ruta real recorrida por el camión.
- **Popups Informativos:** Al hacer clic en un vehículo o parada, muestra estado de carga, conductor, temperatura/velocidad y ETA.
