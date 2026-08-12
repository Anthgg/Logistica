# 01. Arquitectura Modular

## Enfoque

Monolito modular bajo `app/modules/logistics/`. No microservicios. Cada submódulo tiene capas separadas: API, aplicación, dominio e infraestructura.

## Capas

| Capa | Responsabilidad | Puede depender de |
|------|----------------|-------------------|
| **API** | Endpoints FastAPI, validación HTTP | Aplicación |
| **Application** | Casos de uso, orquestación | Dominio, contratos |
| **Domain** | Entidades, value objects, Protocols | Nada externo |
| **Infrastructure** | Implementaciones de contratos | SQLAlchemy, SDK externos |
| **Shared** | Utilidades comunes del dominio | Solo piezas verdaderamente comunes |

## Reglas

- El dominio **no** depende de FastAPI ni SQLAlchemy.
- La API **no** contiene reglas de negocio.
- La infraestructura **no** define reglas centrales.
- Los submódulos no importan detalles internos de otros submódulos.
- Las dependencias compartidas (auth, DB, CSRF) se reutilizan via adaptadores.