# 01. Auditoría de Entidades de Socios de Negocio

## Diagnóstico del Estado Previo de la Base de Datos

Previo al diseño e implementación de la Fase 025, se ejecutó un análisis exhaustivo en el esquema de PostgreSQL para verificar la existencia de estructuras relacionales asociadas a actores comerciales (proveedores, clientes, agencias de transporte o contratistas).

### Hallazgos de la Auditoría Schema & Models

1. **Cero Entidades de Socios Preexistentes:** La base de datos carecía por completo de tablas dedicadas como `suppliers`, `customers`, `carriers`, `vendors` o `clients`.
2. **Entidades Aisladas Existentes:** El sistema contaba únicamente con el módulo multi-tenant de Organizaciones (`organizations`) y el módulo de Identidad de Usuarios (`users`, `user_credentials`), los cuales administran la estructura interna de la empresa y sus empleados, pero no representan entidades comerciales externas o de contraparte.
3. **Ausencia de Taxonomía Tributaria:** No existían enumeraciones ni tablas de referencia para identificadores fiscales (RUC, DNI, CE, RUTA, NIF internacional) ni tablas de ubigeos o contactos de terceros.

---

## Análisis Comparativo: Tablas Segregadas vs. Modelo Maestro Unificado

Se evaluaron dos patrones de modelado para la representación de entes comerciales en el ERP:

### Opción A: Modelo Segregado Tradicional (`suppliers`, `customers`, `carriers`)

En este esquema tradicional, cada rol se implementa mediante una entidad y tabla física independiente:

```
+------------------+     +------------------+     +------------------+
|    suppliers     |     |    customers     |     |     carriers     |
+------------------+     +------------------+     +------------------+
| supplier_id (PK) |     | customer_id (PK) |     | carrier_id (PK)  |
| ruc              |     | ruc              |     | ruc              |
| razon_social     |     | razon_social     |     | razon_social     |
| direccion        |     | direccion        |     | direccion        |
| condicion_pago   |     | linea_credito    |     | codigo_mtc       |
+------------------+     +------------------+     +------------------+
```

#### Deficiencias Críticas Detectadas:
* **Duplicación Inevitable de Datos:** Una empresa que actúa simultáneamente como Proveedor de materia prima y Cliente de productos terminados (o Proveedor e Importador/Transportista) debe registrarse tres veces distintas.
* **Inconsistencia Fiscal:** Modificaciones en la razón social o dirección fiscal en la tabla `suppliers` no se reflejan automáticamente en `customers`, generando incongruencias en comprobantes electrónicos y guías de remisión.
* **Fragmentación de la Hoja de Vida Comercial:** Es imposible obtener un reporte consolidado de balance de pagos/cobros o evaluación de riesgo global de la contraparte.

---

### Opción B: Modelo Maestro Unificado Multi-Rol (`BusinessPartnerModel`) — Elegido

Se seleccionó el patrón **Party / Business Partner Master**, ampliamente consolidado en estándares ERP como SAP S/4HANA (BP Domain) y Microsoft Dynamics 365:

```
                               +-----------------------------+
                               |     business_partners       |
                               +-----------------------------+
                               | partner_id (PK)             |
                               | partner_code (BP-XXXXXX)    |
                               | legal_name, trade_name      |
                               | tax_id_value (RUC/DNI)      |
                               +--------------+--------------+
                                              |
                   +--------------------------+--------------------------+
                   | 1:N                                                 | 1:N
     +-------------v-------------+                         +-------------v-------------+
     |   business_partner_roles  |                         | business_partner_addresses|
     |   (SUPPLIER/CUSTOMER/...) |                         | (FISCAL, DELIVERY, ...)   |
     +-------------+-------------+                         +---------------------------+
                   |
      +------------+------------+------------------------+
      | 1:1                     | 1:1                    | 1:1
+-----v---------------+   +-----v---------------+  +-----v---------------+
| supplier_profiles   |   | customer_profiles   |  | carrier_profiles    |
| (lead_time, payment)|   | (credit_limit, days)|  | (mtc_code, fleet)   |
+---------------------+   +---------------------+  +---------------------+
```

#### Ventajas Arquitectónicas del Modelo Seleccionado:
1. **Identidad Canónica Única:** Una persona natural o jurídica posee exactamente **un registro maestro** en `business_partners`, garantizando la unicidad del número de RUC/DNI en toda la organización.
2. **Extensibilidad de Roles Dinámica:** Un socio puede crearse inicialmente como `SUPPLIER` y, posteriormente, asignársele el rol `CUSTOMER` o `CARRIER` sin alterar sus datos primarios (direcciones, cuentas bancarias, documentos legales).
3. **Encapsulamiento de Atributos Especializados:** Cada rol posee su propia tabla de perfil (1:1 condicional) evitando campos nulos masivos (sparse columns) en la tabla principal.
4. **Resiliencia Operativa:** Permite suspender operativamente a un socio en su rol de `SUPPLIER` (por incumplimiento de entregas) manteniendo activo su rol de `CUSTOMER`.

---

## Conclusión de Diseño

La arquitectura adoptada para la Fase 025 elimina la duplicación de identificadores tributarios, simplifica la integración con la facturación electrónica y sienta las bases para el control unificado de riesgos, aprobaciones y auditoría logístico-financiera.
