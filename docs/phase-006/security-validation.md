# Validación de seguridad

## Invariantes verificadas

| Invariante | Estado | Cómo se comprueba |
|---|---|---|
| Denegación por defecto | VERIFICADA | Sin permiso efectivo → 403, en 55 casos de prueba |
| Ámbito aplicado | VERIFICADA | Organización fuera de ámbito → 403 |
| Step-up exigido | VERIFICADA | Sin prueba → 403, también para el rol de plataforma |
| Sin bypass de administrador | VERIFICADA | 0 comprobaciones por nombre de rol en el dominio logístico |
| Escalada de privilegios | VERIFICADA | Nadie concede permisos que no tiene, sin excepción para admin |
| Separación de funciones | VERIFICADA | Las tres reglas de F005 siguen en verde |
| Sin comodines | VERIFICADA | No existe `*`, `all` ni `full_access` |

## Separación de funciones y los permisos nuevos

Los permisos añadidos en F006 respetan las tres reglas de F005:

- **Originar / aprobar compra**: `PURCHASING` recibe crear, calcular y puntuar
  evaluaciones; `PURCHASING_APPROVER` recibe registrar la decisión. Ningún rol reúne
  ambos lados.
- **Recibir / dictaminar calidad**: sin cambios.
- **Ajustar / auditar inventario**: sin cambios. Hay además una prueba que exige que
  `LOGISTICS_AUDITOR` no tenga ningún permiso mutador — un auditor que puede modificar
  deja de ser una comprobación independiente.

## Mínimo privilegio en los mappings nuevos

Los seis permisos del ciclo de vida documental no se concedieron en bloque:

| Grupo | Roles |
|---|---|
| Editar y registrar evidencia | Quien ya sube archivos: recepción, calidad, almacén, despacho, compras |
| Archivar y restaurar | Control documental y gerencia |
| Retención legal y aceptar custodia | Control documental y administración |

Quien sube un archivo no puede congelarlo legalmente. Es la diferencia entre `files.*`
concedido en bloque y seis acciones declaradas por separado.

## Lo que sigue abierto

| Deuda | Estado |
|---|---|
| 52 operaciones autorizadas por nombre de rol | Fuera del dominio logístico; con trinquete |
| `PurchaseOrderModel` duplicado | Deuda preexistente; 139 fallos en la suite completa |
| Intermitencia de sesión | Deuda preexistente, sin silenciar |
| 80 cuentas fixture con hash inválido | No pueden autenticarse; higiene de datos |
| `roles/editor` en la service account | Más permisos de los necesarios |
| Environment `production` sin crear | El gate de revisores está declarado, no aplicado |
