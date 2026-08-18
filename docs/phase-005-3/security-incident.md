# Incidentes de seguridad tratados en F005.3

Este documento no contiene ningún valor secreto, ni antiguo ni nuevo.

## 1. `SECRET_KEY` con el valor de ejemplo en producción

**Severidad: crítica.**

### Qué se encontró

El servicio Cloud Run productivo corría con `SECRET_KEY` igual al literal de ejemplo
que el repositorio usa como marcador. No es un valor difícil de adivinar: está escrito
en la configuración por defecto.

### Por qué importa

`SECRET_KEY` no es decorativa. La auditoría del código (`app/core/security.py`)
confirma que es la clave HS256 con la que se **firman y se verifican** los JWT:

- `create_access_token()` → firma el token de acceso
- `create_refresh_token()` → firma el token de refresco
- `decode_jwt_token()` → verifica ambos

Con una clave de firma conocida, cualquiera puede fabricar un token de acceso válido
para cualquier `sub` (usuario) y `sid` (sesión). La verificación lo aceptaría porque la
firma es correcta. Eso es una elusión completa de la autenticación, no una debilidad
teórica.

### Qué NO depende de ella

CSRF usa doble envío de cookie con un token aleatorio propio
(`secrets.token_urlsafe(32)`) comparado con `hmac.compare_digest`. No interviene
`SECRET_KEY`, así que rotarla no afecta a la protección CSRF.

No existe soporte de rotación con `kid` ni un segundo secreto de respaldo: hay una única
clave, y cambiarla invalida todos los tokens emitidos con la anterior.

### Acción

Rotada. Nueva clave generada con `secrets.token_urlsafe(48)`, escrita directamente en
Google Secret Manager sin pasar por terminal, registros ni ficheros del repositorio. El
servicio la consume por referencia (`--set-secrets`), no como valor literal.

**Efecto aceptado**: las sesiones anteriores a la rotación dejan de ser válidas. Se
prefirió eso a conservar una clave conocida; no se implementó compatibilidad con la
clave anterior, que sería mantener viva justamente la parte insegura.

## 2. Exposición de `DATABASE_URL` productiva

**Severidad: alta.**

### Qué se encontró

Dos problemas distintos que se refuerzan:

1. La cadena de conexión productiva, **con contraseña**, estaba como variable de
   entorno literal del servicio Cloud Run. Cualquiera con permiso de lectura sobre el
   servicio —bastante más común que el de leer secretos— la obtenía.
2. Durante F005.2 quedó expuesta en la salida de la sesión de trabajo: una vez por un
   `gcloud run services describe` de auditoría, y otra por un fallo de enmascarado en
   un script propio, que ante una URL entre comillas no encontró host y volcó el valor
   crudo.

### Acción

| Elemento | Estado |
|---|---|
| Fallo de enmascarado | Corregido en F005.2: la función es a prueba de fallos y nunca deriva salida del valor crudo |
| Detector de fugas | Añadido en F005.3 (`scripts/scan_for_secrets.py`), con gate en CI |
| Valor literal en Cloud Run | Sustituido por referencia a Secret Manager |
| Contraseña de la base | **`PENDING_SECURE_USER_ACTION`** |

### Por qué la contraseña sigue pendiente

Rotar la contraseña de la base exige el panel de Supabase, al que este agente no tiene
acceso, y la política de la fase prohíbe pedir credenciales por conversación. Los pasos
figuran en [`runbook.md`](runbook.md); ninguno requiere entregar el valor a nadie.

Mientras no se rote, hay que considerar la credencial anterior **potencialmente
comprometida**: mover el valor a Secret Manager reduce la exposición futura, pero no
invalida el valor ya expuesto.

## 3. Historial de git

El escaneo de los workflows de despliegue y de la documentación de fase no encontró
credenciales productivas versionadas (`SECRET_LEAKS=0`).

`ci.yml` sí contiene credenciales, pero de un contenedor PostgreSQL efímero contra
`localhost` y una `SECRET_KEY` de test: nacen y mueren con el runner y no dan acceso a
nada. Quedan deliberadamente fuera del gate.

No se ha reescrito historia de git. Ante un secreto expuesto, la acción que sirve es
**rotarlo**; reescribir el historial no invalida un valor que ya circuló.
