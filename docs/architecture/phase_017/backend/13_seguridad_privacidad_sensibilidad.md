# Seguridad y Privacidad en Inventarios (Phase 017)

## Gating de Datos Sensibles
El costo unitario y el impacto económico total de los ajustes (AJI) o diferencias (ADI) se clasifican como información confidencial de negocio.
- **Gating en Backend**: El servicio `InventoryRenderingService` remueve estos campos a menos que la bandera `sensitive_read` sea verdadera.
- **Aviso Visual**: En caso de no tener el permiso, se renderiza una advertencia en el PDF: `Impacto económico — requiere permiso`.

## Protección de Datos Personales
- DNI y licencias de conducir de transportistas en las transferencias (TRA/CRT) se enmascaran en el backend usando la función de privacidad estándar.
