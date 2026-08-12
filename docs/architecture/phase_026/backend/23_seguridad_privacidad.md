# 23 — Seguridad, Protección de Datos Personales y Rate Limiting

## 1. Tratamiento de Personas Naturales con RUC (RUC 10)

Los RUCs iniciados en `10` corresponden a **Personas Naturales con Negocio**, donde los primeros 8 dígitos coinciden con el Documento Nacional de Identidad (DNI) del contribuyente.

### Cumplimiento con la Ley N° 29733 (Ley de Protección de Datos Personales - Perú):
1. **Principio de Finalidad**: Los datos de contribuyentes RUC 10 se consultan y almacenan exclusivamente para fines de verificación fiscal y emisión de comprobantes de pago en transacciones comerciales.
2. **Minimización de Datos**: No se extraen ni procesan datos personales no tributarios.
3. **Acceso Restringido**: El acceso a búsquedas masivas de RUCs de personas naturales está restringido por permisos RBAC.

---

## 2. Rate Limiting Estricto por IP y Tenant

Para mitigar raspado no autorizado del padrón alojado localmente, la API aplica limitación de tasa (*Rate Limiting*) mediante Token Bucket en Redis:

- **Endpoints de Lookup**: Máximo 100 peticiones / minuto por usuario autenticado.
- **Endpoints Públicos / Anónimos**: Bloqueados (requiere JWT autenticado).
