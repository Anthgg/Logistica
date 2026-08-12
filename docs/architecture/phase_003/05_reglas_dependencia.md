# 05. Reglas de Dependencia

## Permitidas

- **API → Aplicación**: Los routers importan servicios de aplicación.
- **Aplicación → Dominio**: Los servicios usan entidades y contratos del dominio.
- **Infraestructura → Dominio**: Las implementaciones concretas realizan los contratos.
- **Shared → Shared**: Utilidades comunes entre submódulos.
- **Cualquier capa → core/dependencies**: Reutilización de auth, DB, CSRF.

## Prohibidas

- **Dominio → FastAPI**: El dominio no conoce HTTP.
- **Dominio → SQLAlchemy**: El dominio no conoce ORM.
- **Dominio → SDK externo**: El dominio no conoce proveedores.
- **API → SQLAlchemy**: Los routers no acceden directamente a la DB.
- **API → Reglas de negocio**: Los routers solo validan y delegan.
- **Submódulo → Submódulo (directo)**: Los submódulos no importan detalles internos de otros.

## Riesgos de acoplamiento

- **documents ↔ files**: Documents necesita almacenar PDFs. Solución: documents depende del contrato `FileStorage` (Protocol), no de la implementación.
- **routes_module ↔ integrations**: Routes necesita proveedores externos. Solución: routes depende de `DirectionsProvider` (Protocol), no de un SDK concreto.
- **audit ↔ AuditService existente**: El adaptador de audit envuelve el `AuditService` existente sin crear tabla paralela.