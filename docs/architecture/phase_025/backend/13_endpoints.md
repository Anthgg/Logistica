# 13. Especificación de Endpoints REST / OpenAPI

## Catálogo de Endpoints de Socios de Negocio

Todos los endpoints se exponen bajo la ruta base: `/api/logistics/business-partners` y requieren autenticación mediante JWT Bearer Token y los permisos RBAC correspondientes.

---

## 1. Operaciones Principales sobre Socios de Negocio

### `POST /api/logistics/business-partners`
* **Descripción:** Crea un nuevo socio de negocio con su identificador fiscal y roles iniciales.
* **Permiso RBAC:** `logistics.business_partners.create`
* **Request Body:**
  ```json
  {
    "legal_name": "DISTRIBUIDORA INDUSTRIAL DEL PERU S.A.C.",
    "trade_name": "DISIND PERU",
    "person_type": "LEGAL_ENTITY",
    "country_code": "PE",
    "tax_id_type": "RUC",
    "tax_id_value": "20554433221",
    "notes": "Proveedor homologado de repuestos",
    "initial_roles": ["SUPPLIER"],
    "supplier_profile": {
      "payment_condition": "NET_30",
      "currency_code": "PEN",
      "default_lead_time_days": 5
    }
  }
  ```
* **Respuestas:**
  * `201 Created`: Socio registrado exitosamente.
  * `409 Conflict`: RUC o código duplicado (`DuplicateTaxIdException` / `HIGH_PROBABILITY_DUPLICATE`).
  * `422 Unprocessable Entity`: RUC sintácticamente inválido según Módulo 11.

---

### `GET /api/logistics/business-partners`
* **Descripción:** Lista paginada y filtrable de socios de negocio de la organización.
* **Permiso RBAC:** `logistics.business_partners.read`
* **Query Parameters:**
  * `search` (string): Búsqueda por `partner_code`, `legal_name` o `tax_id_value`.
  * `role_type` (string): Filtrar por rol (`SUPPLIER`, `CUSTOMER`, `CARRIER`).
  * `status` (string): Filtrar por estado global (`ACTIVE`, `SUSPENDED`, `BLOCKED`).
  * `page` (int, default 1), `limit` (int, default 20).
* **Respuesta `200 OK`:**
  ```json
  {
    "items": [
      {
        "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "partner_code": "BP-000042",
        "legal_name": "DISTRIBUIDORA INDUSTRIAL DEL PERU S.A.C.",
        "tax_id_type": "RUC",
        "tax_id_value": "20554433221",
        "status": "ACTIVE",
        "roles": ["SUPPLIER"],
        "created_at": "2026-07-28T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
  ```

---

### `GET /api/logistics/business-partners/{id}`
* **Descripción:** Obtiene la ficha completa de un socio incluyendo sus perfiles, direcciones y contactos.
* **Permiso RBAC:** `logistics.business_partners.read`
* **Respuesta Header:** `ETag: "1"` (refleja `row_version`).

---

### `PUT /api/logistics/business-partners/{id}`
* **Descripción:** Actualiza los datos generales de cabecera de un socio. Exige control optimista.
* **Permiso RBAC:** `logistics.business_partners.update`
* **Header Requerido:** `If-Match: "1"` (o campo `row_version` en body).

---

### `POST /api/logistics/business-partners/{id}/block`
* **Descripción:** Inhabilita globalmente a un socio por razones de seguridad o incumplimiento.
* **Permiso RBAC:** `logistics.business_partners.block`
* **Requisito de Seguridad:** **Step-Up Authentication Mandatoria** (SUDO Token en cabecera `X-StepUp-Token`).
* **Request Body:**
  ```json
  {
    "block_reason": "Identificador fiscal reportado por SUNAT como No Habido."
  }
  ```

---

## 2. Operaciones de Roles, Direcciones y Contactos

| Endpoint | Método | Permiso RBAC | Descripción |
|----------|--------|--------------|-------------|
| `/api/logistics/business-partners/{id}/roles` | `POST` | `logistics.business_partner_roles.manage` | Asigna un nuevo rol (`SUPPLIER`, `CUSTOMER`, `CARRIER`) al socio. |
| `/api/logistics/business-partners/{id}/roles/{role_type}/suspend` | `POST` | `logistics.business_partner_roles.manage` | Suspende únicamente un rol específico. |
| `/api/logistics/business-partners/{id}/addresses` | `POST` | `logistics.business_partner_addresses.manage` | Agrega una nueva dirección física o fiscal. |
| `/api/logistics/business-partners/{id}/contacts` | `POST` | `logistics.business_partner_contacts.manage` | Registra un nuevo contacto operativo. |

---

## 3. Endpoints de Evaluaciones y Duplicados

### `POST /api/logistics/business-partners/check-duplicates`
* **Descripción:** Consulta síncrona para verificar si existe un candidato a duplicado antes de guardar.
* **Request Body:** `{"legal_name": "...", "tax_id_value": "..."}`
* **Respuesta `200 OK`:** Retorna el nivel de coincidencia (`HIGH_PROBABILITY_DUPLICATE`, `MEDIUM_PROBABILITY_DUPLICATE` o `NO_DUPLICATE`) y la lista de sugerencias.

### `POST /api/logistics/business-partners/{id}/evaluations`
* **Descripción:** Registra una nueva evaluación ponderada de desempeño ejecutada por el área de homologación.
