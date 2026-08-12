# Portal externo

El portal externo es opcional y no se habilita en esta entrega. No se crean credenciales de proveedor ni sesiones persistentes sin una política aprobada de identidad, expiración, revocación y protección antiabuso.

Se mantiene un hook de job `cleanup-external-sessions` que devuelve cero mientras el portal está desactivado. Esto estabiliza el contrato del scheduler sin introducir una falsa superficie pública.

Una activación futura debe usar tokens de un solo propósito, tenant explícito, expiración corta, rate limiting, auditoría y acceso únicamente al aviso propio.

