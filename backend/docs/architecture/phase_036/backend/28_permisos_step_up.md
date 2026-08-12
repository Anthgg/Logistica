# Permisos y step-up

Los permisos se declaran en el catálogo RBAC y se siembran mediante Alembic. No hay comprobaciones por nombre de rol dentro de servicios.

Lecturas y previews son de riesgo bajo/medio. Enviar o cancelar avisos, administrar transporte, blackouts, confirmar/reprogramar/cancelar citas y emitir/reimprimir CIT requieren step-up según el catálogo. El override de capacidad es crítico.

Los roles existentes reciben únicamente combinaciones explícitas en `ROLE_PERMISSION_MATRIX`; auditor y viewer conservan acceso de sólo lectura.

