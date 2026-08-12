# 12. Especificación OpenAPI y Endpoints REST (Fase 021)

Todos los endpoints descritos se encuentran registrados bajo el prefijo `/api/logistics/company-profile` en `app/modules/logistics/company_profile/router.py`. Requieren autenticación mediante Bearer Token JWT y permisos RBAC específicos.

---

## 📋 Resumen de Endpoints Expuestos

| Método | Ruta | Permiso RBAC Requerido | Descripción |
|---|---|---|---|
| `GET` | `/company-profile` | `logistics.company_profile.read` | Obtiene la Ficha Institucional activa de la organización. |
| `POST` | `/company-profile` | `logistics.company_profile.create` | Inicializa el perfil de la empresa (si no existe). |
| `PATCH` | `/company-profile` | `logistics.company_profile.update` | Actualiza datos institucionales (RUC, Razón Social, etc.). |
| `GET` | `/company-profile/versions` | `logistics.company_profile.read_history` | Lista el historial de versiones SemVer del perfil. |
| `POST` | `/company-profile/versions` | `logistics.company_profile.create` | Genera una nueva versión borrador (`DRAFT`) SemVer. |
| `POST` | `/company-profile/versions/{id}/activate` | `logistics.company_profile.activate` | Activa oficialmente una versión SemVer. |
| `GET` | `/company-profile/addresses` | `logistics.company_addresses.read` | Lista las direcciones institucionales registradas. |
| `POST` | `/company-profile/addresses` | `logistics.company_addresses.manage` | Crea una nueva dirección institucional. |
| `PATCH` | `/company-profile/addresses/{id}` | `logistics.company_addresses.manage` | Actualiza una dirección institucional existente. |
| `POST` | `/company-profile/addresses/{id}/set-primary` | `logistics.company_addresses.manage` | Establece la dirección como principal de la empresa. |
| `GET` | `/company-profile/contacts` | `logistics.company_contacts.read` | Lista los contactos institucionales. |
| `POST` | `/company-profile/contacts` | `logistics.company_contacts.manage` | Registra un nuevo contacto institucional. |
| `PATCH` | `/company-profile/contacts/{id}` | `logistics.company_contacts.manage` | Actualiza un contacto institucional existente. |
| `POST` | `/company-profile/contacts/{id}/set-primary` | `logistics.company_contacts.manage` | Establece el contacto como principal por su área. |
| `GET` | `/company-profile/assets` | `logistics.company_assets.read` | Lista los activos gráficos (Logotipos, Firmas, Sellos). |
| `POST` | `/company-profile/assets/logo` | `logistics.company_assets.upload` | Sube y sanitiza el logotipo oficial en PNG/JPEG/WebP. |
| `GET` | `/company-profile/assets/{id}/content` | `logistics.company_assets.read` | Descarga/visualiza el archivo binario de la imagen. |
| `POST` | `/company-profile/assets/{id}/activate` | `logistics.company_assets.activate` | Activa un activo gráfico cargado. |
| `POST` | `/company-profile/assets/{id}/revoke` | `logistics.company_assets.revoke` | Revoca un activo gráfico. |
| `GET` | `/company-profile/signers` | `logistics.authorized_signers.read` | Lista los firmantes autorizados registrados. |
| `POST` | `/company-profile/signers` | `logistics.authorized_signers.create` | Registra un nuevo firmante autorizado con alcances. |
| `PATCH` | `/company-profile/signers/{id}` | `logistics.authorized_signers.update` | Actualiza alcances o datos del firmante. |
| `POST` | `/company-profile/signers/{id}/signature` | `logistics.authorized_signers.update` | Sube y asocia la firma visual al firmante. |
| `POST` | `/company-profile/signers/{id}/activate` | `logistics.authorized_signers.activate` | Activa las facultades de un firmante autorizado. |
| `POST` | `/company-profile/signers/{id}/suspend` | `logistics.authorized_signers.revoke` | Suspende temporalmente a un firmante autorizado. |
| `POST` | `/company-profile/signers/{id}/revoke` | `logistics.authorized_signers.revoke` | Revoca definitivamente las facultades (requiere motivo). |
| `GET` | `/company-profile/numbering-policies` | `logistics.numbering_policies.read` | Lista las políticas de presentación de numeración. |
| `POST` | `/company-profile/numbering-policies` | `logistics.numbering_policies.create` | Crea una política de presentación de numeración. |
| `POST` | `/company-profile/numbering-policies/preview` | `logistics.numbering_policies.read` | Previsualiza el formato visible sin reservar correlativo. |
| `POST` | `/company-profile/document-preview` | `logistics.company_profile.read` | Renderiza una vista previa PDF fusionando ficha y firmante. |

---

## 🔍 Ejemplos de Request y Response

### 1. Actualizar Ficha Institucional (`PATCH /company-profile`)
#### Request Body:
```json
{
  "legal_name": "EMPRESA LOGÍSTICA PERÚ S.A.C.",
  "trade_name": "LOGÍSTICA PERÚ",
  "ruc": "20123456786",
  "economic_activity": "Transporte y Almacenamiento Carga Pesada",
  "website": "https://logisticaperu.test",
  "primary_email": "contacto@logisticaperu.test",
  "primary_phone": "+51 1 4567890"
}
```

#### Response (200 OK):
```json
{
  "id": "c0819838-f880-480c-b401-9aa04f406b8b",
  "organization_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "legal_name": "EMPRESA LOGÍSTICA PERÚ S.A.C.",
  "trade_name": "LOGÍSTICA PERÚ",
  "ruc": "20123456786",
  "legal_entity_type": null,
  "economic_activity": "Transporte y Almacenamiento Carga Pesada",
  "website": "https://logisticaperu.test",
  "primary_email": "contacto@logisticaperu.test",
  "primary_phone": "+51 1 4567890",
  "country_code": "PE",
  "locale": "es-PE",
  "timezone": "America/Lima",
  "default_currency": "PEN",
  "document_language": "es",
  "profile_status": "DRAFT",
  "active_version_id": null,
  "verification_status": "FORMAT_VALID",
  "created_at": "2026-07-28T10:00:00Z",
  "updated_at": "2026-07-28T11:30:00Z"
}
```

---

### 2. Previsualizar Documento Institucional (`POST /company-profile/document-preview`)
#### Request Body:
```json
{
  "doc_type_code": "PED",
  "branch_id": "b0819838-f880-480c-b401-9aa04f406b8c",
  "custom_data": {
    "motivo_traslado": "Venta Local",
    "observaciones": "Entrega Prioritaria"
  }
}
```

#### Response (200 OK):
* **Headers**: `Content-Type: application/pdf`, `Content-Disposition: inline; filename=PREVIEW_PED.pdf`
* **Body**: Stream binario del archivo PDF generado.
