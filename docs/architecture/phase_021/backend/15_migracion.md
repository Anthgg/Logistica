# 15. Migración de Base de Datos Alembic `l230110021dc_phase_021_company_profile.py`

## 🗄️ Identificación de la Migración

* **Archivo Script**: `backend/alembic/versions/l230110021dc_phase_021_company_profile.py`
* **Revision ID**: `l230110021dc`
* **Revisión Previa (Revises)**: `l230110020dc` (Fase 020 - Ciclo de Vida Documental)
* **Fecha de Creación**: 2026-07-28

---

## 🏛️ Estructura DDL de las 8 Nuevas Tablas

La migración crea las siguientes 8 tablas con sus correspondientes Foreign Keys, Unique Constraints e Índices optimizados:

```sql
-- 1. Ficha Institucional
CREATE TABLE organization_profiles (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL UNIQUE REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    legal_name VARCHAR(256) NOT NULL,
    trade_name VARCHAR(256),
    ruc VARCHAR(11) NOT NULL UNIQUE,
    legal_entity_type VARCHAR(64),
    economic_activity VARCHAR(256),
    website VARCHAR(256),
    primary_email VARCHAR(128),
    primary_phone VARCHAR(32),
    country_code VARCHAR(2) NOT NULL DEFAULT 'PE',
    locale VARCHAR(10) NOT NULL DEFAULT 'es-PE',
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Lima',
    default_currency VARCHAR(3) NOT NULL DEFAULT 'PEN',
    document_language VARCHAR(10) NOT NULL DEFAULT 'es',
    profile_status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    active_version_id UUID, -- Foreign Key circular agregada via ALTER TABLE
    verification_status VARCHAR(32) NOT NULL DEFAULT 'FORMAT_VALID',
    verification_source VARCHAR(64),
    verified_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Versiones SemVer del Perfil
CREATE TABLE organization_profile_versions (
    id UUID PRIMARY KEY,
    organization_profile_id UUID NOT NULL REFERENCES organization_profiles(id) ON DELETE CASCADE,
    version VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    legal_name VARCHAR(256) NOT NULL,
    trade_name VARCHAR(256),
    ruc VARCHAR(11) NOT NULL,
    institutional_payload JSONB NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_org_profile_ver UNIQUE (organization_profile_id, version)
);

-- Alter Table para FK circular de active_version_id
ALTER TABLE organization_profiles 
    ADD CONSTRAINT fk_org_profile_active_version 
    FOREIGN KEY (active_version_id) REFERENCES organization_profile_versions(id) ON DELETE SET NULL;

-- 3. Direcciones Institucionales
CREATE TABLE organization_addresses (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES logistics_branches(id) ON DELETE SET NULL,
    address_type VARCHAR(32) NOT NULL,
    label VARCHAR(128) NOT NULL,
    address_line VARCHAR(512) NOT NULL,
    district VARCHAR(128),
    province VARCHAR(128),
    department VARCHAR(128),
    postal_code VARCHAR(32),
    country_code VARCHAR(2) NOT NULL DEFAULT 'PE',
    latitude FLOAT,
    longitude FLOAT,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_document_address BOOLEAN NOT NULL DEFAULT TRUE,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'FORMAT_VALID',
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Contactos Institucionales
CREATE TABLE organization_contacts (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES logistics_branches(id) ON DELETE SET NULL,
    contact_type VARCHAR(32) NOT NULL,
    label VARCHAR(128) NOT NULL,
    full_name VARCHAR(256),
    position VARCHAR(128),
    email VARCHAR(128),
    phone VARCHAR(32),
    extension VARCHAR(16),
    website VARCHAR(256),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    show_in_documents BOOLEAN NOT NULL DEFAULT TRUE,
    document_families JSONB,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Activos Gráficos (Logos, Firmas, Sellos)
CREATE TABLE organization_assets (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    asset_type VARCHAR(32) NOT NULL,
    filename VARCHAR(256) NOT NULL,
    mime_type VARCHAR(64) NOT NULL,
    size_bytes INT NOT NULL,
    width INT,
    height INT,
    file_hash VARCHAR(64) NOT NULL,
    storage_provider VARCHAR(32) NOT NULL DEFAULT 'local',
    storage_key VARCHAR(512) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    version INT NOT NULL DEFAULT 1,
    uploaded_by UUID,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    asset_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 6. Firmantes Autorizados
CREATE TABLE authorized_signers (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    full_name VARCHAR(256) NOT NULL,
    position_title VARCHAR(128) NOT NULL,
    department VARCHAR(128),
    document_number_masked VARCHAR(32),
    authorization_reference VARCHAR(128),
    authorization_type VARCHAR(64) NOT NULL DEFAULT 'LEGAL_REPRESENTATIVE',
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    signature_asset_id UUID REFERENCES organization_assets(id) ON DELETE SET NULL,
    stamp_asset_id UUID REFERENCES organization_assets(id) ON DELETE SET NULL,
    can_sign_all_branches BOOLEAN NOT NULL DEFAULT TRUE,
    branch_scope JSONB,
    document_family_scope JSONB,
    document_type_scope JSONB,
    max_amount NUMERIC(14,2),
    currency_code VARCHAR(3),
    notes TEXT,
    created_by UUID,
    updated_by UUID,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    revoked_by UUID,
    revoked_at TIMESTAMPTZ,
    revocation_reason VARCHAR(256),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Configuraciones Documentales
CREATE TABLE organization_document_settings (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL UNIQUE REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    profile_version_id UUID REFERENCES organization_profile_versions(id) ON DELETE SET NULL,
    document_logo_asset_id UUID REFERENCES organization_assets(id) ON DELETE SET NULL,
    default_address_id UUID REFERENCES organization_addresses(id) ON DELETE SET NULL,
    default_contact_id UUID REFERENCES organization_contacts(id) ON DELETE SET NULL,
    show_ruc BOOLEAN NOT NULL DEFAULT TRUE,
    show_trade_name BOOLEAN NOT NULL DEFAULT TRUE,
    show_legal_name BOOLEAN NOT NULL DEFAULT TRUE,
    show_address BOOLEAN NOT NULL DEFAULT TRUE,
    show_contact BOOLEAN NOT NULL DEFAULT TRUE,
    show_template_version BOOLEAN NOT NULL DEFAULT TRUE,
    show_renderer_version BOOLEAN NOT NULL DEFAULT TRUE,
    show_partial_hash BOOLEAN NOT NULL DEFAULT TRUE,
    show_qr BOOLEAN NOT NULL DEFAULT TRUE,
    show_page_number BOOLEAN NOT NULL DEFAULT TRUE,
    confidentiality_text VARCHAR(512),
    footer_text VARCHAR(512),
    default_locale VARCHAR(10) NOT NULL DEFAULT 'es-PE',
    default_timezone VARCHAR(50) NOT NULL DEFAULT 'America/Lima',
    default_currency VARCHAR(3) NOT NULL DEFAULT 'PEN',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Políticas de Presentación de Numeración
CREATE TABLE organization_numbering_display_policies (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES logistics_organizations(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES logistics_branches(id) ON DELETE SET NULL,
    document_type_id UUID NOT NULL REFERENCES document_types(id) ON DELETE CASCADE,
    code_standard_version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    document_site_code_id UUID REFERENCES document_site_codes(id) ON DELETE SET NULL,
    display_pattern VARCHAR(128) NOT NULL DEFAULT '{TYPE}-{SITE}-{YEAR}-{SEQUENCE}',
    sequence_padding INT NOT NULL DEFAULT 6,
    show_internal_code BOOLEAN NOT NULL DEFAULT TRUE,
    show_external_series BOOLEAN NOT NULL DEFAULT TRUE,
    show_external_number BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    created_by UUID,
    approved_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## ⚡ Índices Creados para Optimización de Consultas

1. `ix_org_profiles_org_id` ON `organization_profiles(organization_id)`
2. `ix_org_profiles_ruc` ON `organization_profiles(ruc)`
3. `ix_org_profile_ver_profile_id` ON `organization_profile_versions(organization_profile_id)`
4. `ix_org_addresses_org_id` ON `organization_addresses(organization_id)`
5. `ix_org_contacts_org_id` ON `organization_contacts(organization_id)`
6. `ix_org_assets_org_id` ON `organization_assets(organization_id)`
7. `ix_auth_signers_org_id` ON `authorized_signers(organization_id)`
8. `ix_doc_settings_org_id` ON `organization_document_settings(organization_id)`
9. `ix_numbering_policies_org_id` ON `organization_numbering_display_policies(organization_id)`
