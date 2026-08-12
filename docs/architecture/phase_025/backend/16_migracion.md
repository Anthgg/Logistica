# 16. Especificación de Migración Alembic (DDL SQL)

## Script de Migración `p270110025dc_phase_025_business_partners.py`

La migración crea las **16 tablas relacionales** del dominio de Socios de Negocio, sus índices de rendimiento B-Tree/GIN, restricciones de unicidad multi-tenant y claves foráneas con reglas de eliminación en cascada controladas.

---

## DDL SQL Extraído de la Migración

```sql
-- Extensiones requeridas para similitud trigram en PostgreSQL
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. Tabla de Secuencias por Organización
CREATE TABLE business_partner_sequences (
    organization_id UUID NOT NULL PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
    current_value INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla Principal de Socios de Negocio
CREATE TABLE business_partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    partner_code VARCHAR(20) NOT NULL,
    legal_name VARCHAR(255) NOT NULL,
    trade_name VARCHAR(255),
    person_type VARCHAR(20) NOT NULL DEFAULT 'LEGAL_ENTITY',
    country_code VARCHAR(2) NOT NULL DEFAULT 'PE',
    tax_id_type VARCHAR(10) NOT NULL DEFAULT 'RUC',
    tax_id_value VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    compliance_status VARCHAR(20) NOT NULL DEFAULT 'COMPLIANT',
    notes TEXT,
    row_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_bp_org_code UNIQUE (organization_id, partner_code),
    CONSTRAINT uq_bp_org_tax_id UNIQUE (organization_id, tax_id_type, tax_id_value)
);

-- Índices B-Tree y GIN para business_partners
CREATE INDEX ix_bp_tax_lookup ON business_partners (organization_id, tax_id_value);
CREATE INDEX ix_bp_org_status ON business_partners (organization_id, status);
CREATE INDEX ix_bp_legal_name_trgm ON business_partners USING gin (legal_name gin_trgm_ops);

-- 3. Tabla de Roles de Socio
CREATE TABLE business_partner_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    role_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    suspension_reason TEXT,
    suspended_at TIMESTAMP WITH TIME ZONE,
    suspended_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_bp_role_type UNIQUE (business_partner_id, role_type)
);

-- 4. Perfil de Proveedor
CREATE TABLE business_partner_supplier_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL UNIQUE REFERENCES business_partner_roles(id) ON DELETE CASCADE,
    payment_condition VARCHAR(20) NOT NULL DEFAULT 'NET_30',
    currency_code VARCHAR(3) NOT NULL DEFAULT 'PEN',
    default_incoterm VARCHAR(3),
    default_lead_time_days INTEGER NOT NULL DEFAULT 7,
    minimum_order_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    requires_purchase_order BOOLEAN NOT NULL DEFAULT TRUE,
    withholding_agent BOOLEAN NOT NULL DEFAULT FALSE,
    detraction_account VARCHAR(30),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Perfil de Cliente
CREATE TABLE business_partner_customer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL UNIQUE REFERENCES business_partner_roles(id) ON DELETE CASCADE,
    credit_limit NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    credit_days INTEGER NOT NULL DEFAULT 0,
    currency_code VARCHAR(3) NOT NULL DEFAULT 'PEN',
    risk_category VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    price_list_id UUID,
    allow_overcredit BOOLEAN NOT NULL DEFAULT FALSE,
    sales_rep_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Perfil de Transportista
CREATE TABLE business_partner_carrier_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL UNIQUE REFERENCES business_partner_roles(id) ON DELETE CASCADE,
    mtc_registration_code VARCHAR(50) NOT NULL,
    mtc_license_expiration DATE,
    fleet_type VARCHAR(20) NOT NULL DEFAULT 'OWNED',
    max_payload_tonnage NUMERIC(8, 2) NOT NULL DEFAULT 0.00,
    permits_hazardous_materials BOOLEAN NOT NULL DEFAULT FALSE,
    tracking_api_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Identificadores Fiscales Secundarios
CREATE TABLE business_partner_tax_identifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    tax_id_type VARCHAR(10) NOT NULL,
    tax_id_value VARCHAR(30) NOT NULL,
    issuing_country VARCHAR(2) NOT NULL DEFAULT 'PE',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. Direcciones de Socios
CREATE TABLE business_partner_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    address_type VARCHAR(20) NOT NULL DEFAULT 'OPERATIONAL',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    urbanization VARCHAR(100),
    ubigeo_code VARCHAR(6),
    department VARCHAR(100),
    province VARCHAR(100),
    district VARCHAR(100),
    country_code VARCHAR(2) NOT NULL DEFAULT 'PE',
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Contactos de Socios
CREATE TABLE business_partner_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    contact_type VARCHAR(20) NOT NULL DEFAULT 'LOGISTICS',
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    job_title VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(30),
    mobile_number VARCHAR(30),
    whatsapp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 10. Evaluaciones
CREATE TABLE business_partner_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    evaluation_code VARCHAR(30) NOT NULL,
    evaluation_date DATE NOT NULL,
    evaluated_by UUID NOT NULL,
    total_score NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    is_approved BOOLEAN NOT NULL DEFAULT TRUE,
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 11. Detalle de Evaluaciones
CREATE TABLE business_partner_evaluation_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES business_partner_evaluations(id) ON DELETE CASCADE,
    criterion_name VARCHAR(100) NOT NULL,
    weight_percentage NUMERIC(5, 2) NOT NULL,
    score_assigned NUMERIC(5, 2) NOT NULL,
    weighted_score NUMERIC(5, 2) NOT NULL
);

-- 12. Documentos Legales
CREATE TABLE business_partner_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    document_type VARCHAR(30) NOT NULL,
    document_number VARCHAR(100),
    file_storage_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by UUID,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 13. Registro Histórico de Cumplimiento
CREATE TABLE business_partner_compliance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    event_type VARCHAR(30) NOT NULL,
    previous_compliance_status VARCHAR(30) NOT NULL,
    new_compliance_status VARCHAR(30) NOT NULL,
    reason TEXT NOT NULL,
    triggered_by_user_id UUID NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 14. Cuentas Bancarias
CREATE TABLE business_partner_bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    cci_number VARCHAR(50),
    currency_code VARCHAR(3) NOT NULL DEFAULT 'PEN',
    account_type VARCHAR(20) NOT NULL DEFAULT 'SAVINGS',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 15. Snapshots Inmutables de Versionado
CREATE TABLE business_partner_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_partner_id UUID NOT NULL REFERENCES business_partners(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_payload JSONB NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    change_reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    CONSTRAINT uq_bp_version_num UNIQUE (business_partner_id, version_number)
);

-- 16. Matriz de Duplicados
CREATE TABLE business_partner_duplicates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    source_partner_id UUID NOT NULL REFERENCES business_partners(id),
    candidate_partner_id UUID NOT NULL REFERENCES business_partners(id),
    match_level VARCHAR(30) NOT NULL,
    similarity_score NUMERIC(5, 4) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING_REVIEW',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```
