# 14. Catálogo de Eventos de Auditoría (Fase 021)

## 📜 Registros de Auditoría Inmutable

Cada mutación relevante de estado en la Ficha Institucional, Activos Gráficos, Direcciones, Contactos y Firmantes Autorizados emite un evento inmutable hacia la tabla central `logistics_audit_events` a través de `app/modules/logistics/audit/service.py`.

---

## 🗂️ Eventos Registrados en `EVENT_CATALOG`

A continuación se detalla la matriz de eventos introducida y utilizada por la Fase 021:

| Código del Evento | Categoría | Severidad | Descripción del Evento |
|---|---|---|---|
| `logistics.company_profile.updated` | `ORGANIZATION` | `MEDIUM` | Ficha institucional actualizada (RUC, Razón Social, etc.). |
| `logistics.company_profile.version_created` | `ORGANIZATION` | `MEDIUM` | Versión borrador SemVer generada con payload JSONB y SHA-256. |
| `logistics.company_profile.version_activated` | `ORGANIZATION` | `HIGH` | Versión institucional activada y congelada oficialmente. |
| `logistics.company_address.created` | `ORGANIZATION` | `LOW` | Nueva dirección institucional agregada. |
| `logistics.company_address.updated` | `ORGANIZATION` | `LOW` | Dirección institucional actualizada. |
| `logistics.company_address.primary_changed` | `ORGANIZATION` | `MEDIUM` | Cambio de dirección principal de la organización. |
| `logistics.company_contact.created` | `ORGANIZATION` | `LOW` | Nuevo contacto registrado. |
| `logistics.company_contact.updated` | `ORGANIZATION` | `LOW` | Contacto institucional actualizado. |
| `logistics.company_asset.uploaded` | `ORGANIZATION` | `MEDIUM` | Activo gráfico (logo/firma) cargado y sanitizado. |
| `logistics.company_asset.activated` | `ORGANIZATION` | `MEDIUM` | Activo gráfico activado para uso en documentos. |
| `logistics.company_asset.revoked` | `ORGANIZATION` | `HIGH` | Activo gráfico revocado. |
| `logistics.authorized_signer.created` | `ORGANIZATION` | `HIGH` | Registro de nuevo firmante autorizado. |
| `logistics.authorized_signer.updated` | `ORGANIZATION` | `MEDIUM` | Modificación de alcances o facultades de firmante. |
| `logistics.authorized_signer.activated` | `ORGANIZATION` | `HIGH` | Habilitación/Aprobación de firmante autorizado. |
| `logistics.authorized_signer.suspended` | `ORGANIZATION` | `HIGH` | Suspensión temporal de firmante autorizado. |
| `logistics.authorized_signer.revoked` | `ORGANIZATION` | `CRITICAL` | Revocación definitiva de poderes del firmante (con motivo). |
| `logistics.numbering_policy.created` | `DOCUMENT` | `MEDIUM` | Registro de nueva política de presentación de numeración. |
| `logistics.numbering_policy.updated` | `DOCUMENT` | `MEDIUM` | Modificación de patrón estético de numeración. |

---

## 🔍 Estructura del Evento de Auditoría Persistido

Ejemplo de registro insertado en `logistics_audit_events` al activar una nueva versión SemVer del perfil:

```json
{
  "id": "e98f7e6a-1234-4567-89ab-cdef01234567",
  "event_code": "logistics.company_profile.version_activated",
  "category": "organization",
  "severity": "high",
  "actor_user_id": "u1111111-2222-3333-4444-555555555555",
  "organization_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "resource_type": "organization_profile_versions",
  "resource_id": "v9999999-8888-7777-6666-555555555555",
  "new_data": {
    "version": "1.0.1",
    "reason": "Aprobación de nueva Razón Social ante Registros Públicos",
    "content_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
  },
  "created_at": "2026-07-28T11:45:00Z"
}
```
