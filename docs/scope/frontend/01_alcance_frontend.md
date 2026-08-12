# 01. Alcance General del Frontend — Proyecto T1

## 1. Inclusiones Generales del Frontend

El frontend será una aplicación de página única (SPA) construida en React, servida a través de Nginx no privilegiado, diseñada para una experiencia operativa intuitiva y fluida:

- **Estructura de Layout Empresarial:** Navbar superior con información del usuario autenticado, indicador de estado de sesión/confianza biométrica y Sidebar replegable con menú jerárquico por dominio.
- **Formularios de Maestros con Validación en Cliente:** Interfaces responsivas para gestión de Productos, Sedes, Almacenes, Ubicaciones, Socios de Negocio, Vehículos y Conductores.
- **Vistas Operativas de Almacén:** Tableros de control para recepción en muelle (Garita), lista de tareas de picking con ruta sugerida, mesa de packing etiquetado LPN y emisión de despachos.
- **Consola de Monitoreo de Rutas (MapLibre GL):** Mapa interactivo vectorial para visualización de viajes activos, seguimiento de vehículos por GPS en tiempo real, trazado de rutas y geocercas.
- **Manejo de Re-autenticación (Step-Up UI):** Modal emergente de alta prioridad interceptado automáticamente cuando la API requiere confirmación de seguridad para acciones sensibles.
- **Visor e Impresión de Documentos:** Componente modal/drawer para previsualización de Guías de Remisión PDF y actas logísticas generadas.
- **Interfaz Móvil del Conductor (PWA / Responsive Mobile):** Vista simplificada optimizada para teléfonos móviles que permite al conductor iniciar viaje, transmitir coordenadas GPS y registrar la Prueba de Entrega (POD: foto, firma u OTP).

---

## 2. Exclusiones Explícitas del Lanzamiento Inicial

1. **Diseñador de Reportes Drag-and-Drop / WYSIWYG:**
   - *Motivo:* Complejidad innecesaria en el MVP. Se ofrecerán reportes con filtros predefinidos y exportación a Excel/CSV.
2. **Visualizador 3D de Pasillos y Racks de Almacén:**
   - *Motivo:* Alto consumo de recursos en navegador. El MVP utilizará mapas 2D y listas de ubicaciones jerárquicas.
3. **Modo Fuera de Línea (Offline) Completo para la SPA Web Administrative:**
   - *Motivo:* La consola web administrativa requiere conexión constante a la API en Cloud Run. Únicamente la vista del conductor contará con almacenamiento en búfer local para coordenadas GPS.
4. **Personalización Dinámica de Colores por Usuario (Theming Dinámico):**
   - *Motivo:* El sistema utilizará el sistema de diseño estandarizado con soporte para Modo Oscuro (Dark Theme) profesional.
