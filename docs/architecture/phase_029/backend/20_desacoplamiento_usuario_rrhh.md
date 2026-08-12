# 20 — Desacoplamiento entre Conductor, Usuario, Empleado y Socio Comercial

## Principios de Desacoplamiento de Arquitectura

Una de las decisiones fundamentales de la **Fase 029** es el **desacoplamiento estricto** de la entidad `DriverModel` frente a otras entidades del sistema como `User` (autenticación), `Employee` (recursos humanos) y `BusinessPartner` (terceros).

---

## Comparativa de Roles y Fronteras de Dominio

```mermaid
graph TD
    subgraph Dominio de Seguridad & Autenticación
        User[User / Cuenta de Usuario]
    end
    
    subgraph Dominio de Recursos Humanos
        Employee[Employee / Ficha de RRHH]
    end
    
    subgraph Dominio de Socios Comerciales
        BP[BusinessPartner / Transportista Tercero]
    end
    
    subgraph Dominio Logístico de Transporte (Fase 029)
        Driver[DriverModel / Maestro de Conductores]
    end
    
    Driver -.->|Enlace Opcional 1:1| User
    Driver -.->|Referencia FK Opcional| Employee
    Driver -.->|Asignación Histórica 1:N| BP
```

---

## Justificación Técnica de la Separación

| Entidad | Propósito de Dominio | ¿Por qué NO fusionarla con `Driver`? |
|---|---|---|
| **`User`** (`sys_users`) | Autenticación (JWT/OAuth), credenciales, contraseña y permisos de sistema. | Muchos conductores de empresas transportistas subcontratadas cargan mercadería en planta sin requerir acceso al software o credenciales de usuario. |
| **`Employee`** (`hr_employees`) | Nómina, contrato laboral, asistencia, legajo personal, vacantes y beneficios. | Los conductores de terceros (empresas de transporte contratadas) no pertenecen a la nómina de la empresa titular. Fusionarlos violaría la separación contable y legal. |
| **`BusinessPartner`** (`logistics_business_partners`) | Tercero jurídico o natural (Transportista, Cliente, Proveedor) con RUC/RUT y razón social. | El conductor es la persona física que opera el vehículo. El transportista es la persona jurídica o empresa que contrata al conductor. |

---

## Reglas de Integración Límite (Bounded Context Rules)

1. **Autonomía Operativa**: La existencia y gestión de un conductor en `logistics_drivers` es totalmente independiente de si tiene o no un usuario en el sistema.
2. **Sin Inserción en Cascada Destructiva**: La eliminación o desactivación de un `User` o `Employee` NO elimina ni desactiva automáticamente al `DriverModel`. Las relaciones usan `ON DELETE SET NULL` o tablas de enlace explícitas.
3. **Privacidad de RRHH**: El maestro de conductores no almacena datos salariales, cuentas bancarias de nómina ni contratos de trabajo; solo atributos de transporte y seguridad vial.
