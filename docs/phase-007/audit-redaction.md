# F007 · Política de Sanitización y Redacción de Secretos

## 1. Regla Crítica: `AUDIT_SECRET_LEAKS=0`
Bajo ninguna circunstancia se almacenan secretos, tokens, credenciales o material criptográfico en las columnas `previous_data`, `new_data` o `metadata_`.

## 2. Campos Redactados Automáticamente
El módulo `sanitizer.py` inspecciona recursivamente diccionarios y estructuras anidadas reemplazando por `[REDACTED]` los siguientes patrones:
- `password`, `password_hash`, `new_password`, `old_password`
- `token`, `access_token`, `refresh_token`, `session_token`, `auth_token`
- `secret`, `secret_key`, `client_secret`
- `cookie`, `session_cookie`, `csrf_token`
- `api_key`, `access_key`, `private_key`
- `biometric_raw`, `facial_template`
- `database_url`, `connection_string`

## 3. Enmascaramiento Dinámico de Direcciones IP
Para proteger la privacidad de los operadores conforme a regulaciones de protección de datos:
- Las direcciones IP se registran en base de datos.
- En las respuestas HTTP de consulta (`GET /audit-events/{id}`) y exportación (`GET /audit-events/export`), la IP se devuelve como `[REDACTED]` a menos que el usuario autenticado cuente expresamente con el permiso `logistics.audit.read_sensitive`.\n