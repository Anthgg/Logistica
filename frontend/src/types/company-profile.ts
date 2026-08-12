export type CompanyProfileStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED' | 'SUPERSEDED'

export type AddressType = 'FISCAL' | 'BRANCH' | 'WAREHOUSE' | 'ADMINISTRATIVE'

export type ContactType = 'GENERAL' | 'LOGISTICS' | 'BILLING' | 'LEGAL' | 'SUPPORT'

export type AssetType = 'LOGO_LIGHT' | 'LOGO_DARK' | 'FAVICON' | 'STAMP' | 'WATERMARK'

export type SignerStatus = 'ACTIVE' | 'SUSPENDED' | 'REVOKED' | 'EXPIRED'

export interface CompanyProfileCapabilities {
  can_edit_profile: boolean
  can_activate_profile: boolean
  can_manage_addresses: boolean
  can_manage_contacts: boolean
  can_upload_logo: boolean
  can_activate_logo: boolean
  can_manage_signers: boolean
  can_upload_signature: boolean
  can_activate_signer: boolean
  can_revoke_signer: boolean
  can_manage_numbering: boolean
  can_preview_documents: boolean
  can_view_history: boolean
}

export interface CompanyProfile {
  id: string
  version_number: number
  status: CompanyProfileStatus
  business_name: string
  trade_name: string | null
  ruc: string
  ruc_verification_status: 'UNVERIFIED' | 'VALID_FORMAT' | 'VERIFIED_EXTERNAL' | 'INVALID'
  entity_type: string | null
  economic_activity: string | null
  primary_email: string
  primary_phone: string
  website_url: string | null
  country_code: string
  timezone: string
  document_language: string
  default_currency: string
  active_logo_asset_id: string | null
  active_logo_url: string | null
  created_at: string
  updated_at: string
  created_by_user_name: string | null
  activated_at: string | null
  activated_by_user_name: string | null
  capabilities: CompanyProfileCapabilities
}

export interface CompanyProfileUpdate {
  business_name: string
  trade_name?: string | null
  ruc: string
  entity_type?: string | null
  economic_activity?: string | null
  primary_email: string
  primary_phone: string
  website_url?: string | null
  country_code: string
  timezone: string
  document_language: string
  default_currency: string
}

export interface OrganizationAddress {
  id: string
  address_type: AddressType
  label: string
  address_line: string
  district: string
  province: string
  department: string
  country_code: string
  branch_id: string | null
  branch_name?: string | null
  is_primary: boolean
  is_visible_in_documents: boolean
  is_active: boolean
  created_at: string
}

export interface OrganizationAddressCreate {
  address_type: AddressType
  label: string
  address_line: string
  district: string
  province: string
  department: string
  country_code: string
  branch_id?: string | null
  is_primary?: boolean
  is_visible_in_documents?: boolean
}

export interface OrganizationContact {
  id: string
  contact_type: ContactType
  name: string
  job_title: string
  email: string
  phone: string
  extension: string | null
  branch_id: string | null
  document_families: string[]
  is_primary: boolean
  is_visible_in_documents: boolean
  is_active: boolean
  created_at: string
}

export interface OrganizationContactCreate {
  contact_type: ContactType
  name: string
  job_title: string
  email: string
  phone: string
  extension?: string | null
  branch_id?: string | null
  document_families: string[]
  is_primary?: boolean
  is_visible_in_documents?: boolean
}

export interface OrganizationAsset {
  id: string
  asset_type: AssetType
  file_name: string
  mime_type: string
  file_size_bytes: number
  width_px: number | null
  height_px: number | null
  is_active: boolean
  uploaded_by_user_name: string
  uploaded_at: string
  preview_blob_url?: string | null
}

export interface AuthorizedSigner {
  id: string
  full_name: string
  job_title: string
  department: string
  user_id: string | null
  authorization_ref: string
  authorization_type: string
  valid_from: string
  valid_until: string | null
  all_branches: boolean
  branch_ids: string[]
  document_families: string[]
  document_types: string[]
  monetary_limit: string | null
  currency: string | null
  status: SignerStatus
  signature_asset_id: string | null
  has_signature: boolean
  observations: string | null
  created_at: string
}

export interface AuthorizedSignerCreate {
  full_name: string
  job_title: string
  department: string
  user_id?: string | null
  authorization_ref: string
  authorization_type: string
  valid_from: string
  valid_until?: string | null
  all_branches: boolean
  branch_ids: string[]
  document_families: string[]
  document_types: string[]
  monetary_limit?: number | null
  currency?: string | null
  observations?: string | null
}

export interface NumberingPolicy {
  id: string
  document_type: string
  branch_id: string
  branch_code: string
  pattern_tokens: string[]
  padding_length: number
  external_series_code: string
  external_next_number: number
  status: 'DRAFT' | 'ACTIVE' | 'INACTIVE'
  created_at: string
}

export interface NumberingPolicyCreate {
  document_type: string
  branch_id: string
  pattern_tokens: string[]
  padding_length: number
  external_series_code: string
}

export interface ProfileVersionItem {
  id: string
  version_number: number
  status: CompanyProfileStatus
  created_at: string
  created_by_user_name: string
  activated_at: string | null
  activated_by_user_name: string | null
  hash_sha256: string
  changes_summary: string
}

export interface InstitutionalPreviewRequest {
  doc_type_code: string
  branch_id?: string | null
  signer_id?: string | null
  custom_data?: Record<string, unknown> | null
}

export type InstitutionalDocCategory =
  | 'INBOUND'
  | 'OUTBOUND'
  | 'QUALITY'
  | 'TRANSPORT'
  | 'BILLING_LEGAL'

export interface InstitutionalDocumentTypeInfo {
  code: string
  name: string
  shortName: string
  category: InstitutionalDocCategory
  categoryLabel: string
  description: string
  sampleCustomData?: Record<string, unknown>
}

export const INSTITUTIONAL_DOCUMENT_TYPES: InstitutionalDocumentTypeInfo[] = [
  // Recepción e Ingreso
  {
    code: 'AREC',
    name: 'Acta de Recepción y Conformidad',
    shortName: 'Acta Recepción (AREC)',
    category: 'INBOUND',
    categoryLabel: 'Recepción e Ingreso',
    description: 'Documento oficial de conformidad de descarga y recepción física de mercancías en almacén.',
    sampleCustomData: {
      supplier_name: 'DISTRIBUIDORA LOGÍSTICA S.A.C.',
      reference: 'GUIA-REMITENTE-001-9872',
      transport_info: 'Muelle 03 | Placa: ABC-789 | Chofer: Juan Pérez',
      notes: 'Mercadería recibida en muelle 03 sujeta a verificación de lote.',
      items: [
        {
          code: 'SKU-001',
          description: 'Cajas de Cartón Corrugado Doble 50x50',
          unit: 'UND',
          expected_quantity: '500.00',
          received_quantity: '500.00',
          status: 'CONFORME',
        },
        {
          code: 'SKU-002',
          description: 'Cinta de Embalaje Industrial 2" x 100m',
          unit: 'RLS',
          expected_quantity: '120.00',
          received_quantity: '120.00',
          status: 'CONFORME',
        },
      ],
    },
  },
  {
    code: 'CIT',
    name: 'Constancia de Inspección Técnica',
    shortName: 'Inspección Técnica (CIT)',
    category: 'INBOUND',
    categoryLabel: 'Recepción e Ingreso',
    description: 'Registro de validación técnica, temperatura y condiciones físico-químicas de ingreso.',
    sampleCustomData: {
      supplier_name: 'AGROINDUSTRIAS DEL SUR S.A.C.',
      reference: 'GUIA-002-8819',
      temperature_celsius: 4.2,
      vehicle_hygiene_score: 98,
      sampling_method: 'AQL 1.5 Nivel II',
      seal_status: 'INTACTO',
      notes: 'Validación de temperatura y parámetros microbiológicos en cámara de recepción.',
      items: [
        {
          code: 'ALM-089',
          description: 'Materia Prima Refrigerada Lote 2026-A',
          unit: 'KG',
          expected_quantity: '1500.00',
          received_quantity: '1500.00',
          status: 'APROBADO',
        },
      ],
    },
  },
  {
    code: 'CPV',
    name: 'Constancia de Peso y Volumen / Control Garita',
    shortName: 'Peso y Garita (CPV)',
    category: 'INBOUND',
    categoryLabel: 'Recepción e Ingreso',
    description: 'Comprobante de ingreso y registro de garita con verificación de chofer, placa, precinto, peso y volumen.',
    sampleCustomData: {
      supplier_name: 'TRANSPORTES Y LOGÍSTICA NACIONAL S.A.',
      vehicle_plate: 'BCF-892',
      trailer_plate: 'TR-102',
      driver_name: 'Carlos Mendoza Ramos',
      driver_license: 'Q12345678',
      gross_weight_kg: 18450.0,
      tare_weight_kg: 8200.0,
      net_weight_kg: 10250.0,
      seal_code: 'SEAL-PERU-99214',
      notes: 'Pesaje conforme en balanza de plataforma norte.',
    },
  },

  // Calidad, Cuarentena y Discrepancias
  {
    code: 'DIF',
    name: 'Declaración de Ingreso Físico y Discrepancias',
    shortName: 'Diferencias (DIF)',
    category: 'QUALITY',
    categoryLabel: 'Calidad y Discrepancias',
    description: 'Constancia formal de mermas, sobrantes, faltantes o daños detectados durante la descarga.',
    sampleCustomData: {
      incident_code: 'INC-2026-0041',
      supplier_name: 'ENVASES INDUSTRIALES DEL PACÍFICO S.A.',
      reference: 'GUIA-001-4412',
      notes: 'Discrepancia detectada durante el conteo ciego en muelle.',
      items: [
        {
          code: 'SKU-001',
          description: 'Bidones Plásticos 20L',
          unit: 'UND',
          expected_quantity: '200.00',
          received_quantity: '195.00',
          status: 'FALTANTE (-5 UND)',
        },
      ],
    },
  },
  {
    code: 'APC',
    name: 'Acta de Retención o Cuarentena Preventiva',
    shortName: 'Acta Cuarentena (APC)',
    category: 'QUALITY',
    categoryLabel: 'Calidad y Discrepancias',
    description: 'Acta oficial de inmovilización preventiva y retención de lotes observados.',
    sampleCustomData: {
      quarantine_reason: 'Ruptura de cadena de frío en tránsito',
      quarantine_zone: 'CAM-FRIA-02',
      quarantined_batches: ['LOT-2026-X88', 'LOT-2026-X89'],
      notes: 'Mercancía bloqueada para despacho hasta dictamen de laboratorio.',
      items: [
        {
          code: 'FAR-004',
          description: 'Reactivos Biológicos 500ml',
          unit: 'FCO',
          expected_quantity: '50.00',
          received_quantity: '50.00',
          status: 'RETENIDO',
        },
      ],
    },
  },
  {
    code: 'NC',
    name: 'Reporte de No Conformidad de Calidad',
    shortName: 'No Conformidad (NC)',
    category: 'QUALITY',
    categoryLabel: 'Calidad y Discrepancias',
    description: 'Registro de incumplimiento de especificaciones de compra o parámetros de entrega.',
    sampleCustomData: {
      nc_level: 'MAJOR',
      supplier_name: 'PROVEEDORES QUÍMICOS INTEGRALES S.A.C.',
      reference: 'OC-2026-0182',
      root_cause: 'Embalaje secundario humedecido y deformado.',
      action_plan: 'Inmovilización de lote y notificación formal a aseguradora.',
      notes: 'Rechazo parcial del lote en inspección de calidad.',
    },
  },

  // Despacho y Transporte
  {
    code: 'CEP',
    name: 'Certificado de Evaluación de Proveedor / Entrega',
    shortName: 'Certificado Proveedor (CEP)',
    category: 'OUTBOUND',
    categoryLabel: 'Evaluación y Despacho',
    description: 'Certificado de evaluación institucional y conformidad de nivel de servicio logístico.',
    sampleCustomData: {
      supplier_name: 'SERVICIOS LOGÍSTICOS & EMBALAJES S.A.',
      supplier_ruc: '20554433221',
      period: '2026-Q1',
      overall_score: 96.5,
      delivery_rating: 'EXCELENTE (98%)',
      quality_rating: 'CONFORME (95%)',
      notes: 'Proveedor homologado en nivel A para la cadena de suministro.',
    },
  },
  {
    code: 'PED',
    name: 'Orden / Pedido de Despacho Logístico',
    shortName: 'Orden Despacho (PED)',
    category: 'OUTBOUND',
    categoryLabel: 'Evaluación y Despacho',
    description: 'Instrucción oficial de preparación, picking, packing y salida de almacén.',
    sampleCustomData: {
      order_ref: 'PED-2026-0129',
      priority: 'ALTA',
      staging_lane: 'CARRIL-SALIDA-04',
      notes: 'Despacho prioritario para sucursal Arequipa.',
      items: [
        {
          code: 'SKU-501',
          description: 'Filtros de Aire Industrial Modelo F-100',
          unit: 'UND',
          expected_quantity: '40.00',
          received_quantity: '40.00',
          status: 'PREPARADO',
        },
      ],
    },
  },
  {
    code: 'MAN',
    name: 'Manifiesto de Carga Consolidado',
    shortName: 'Manifiesto Carga (MAN)',
    category: 'TRANSPORT',
    categoryLabel: 'Transporte y Despacho',
    description: 'Relación consolidada de bultos, guías y destinos asignados a una unidad de transporte.',
    sampleCustomData: {
      carrier_name: 'TransExpress Perú S.A.C.',
      vehicle_plate: 'Z5A-812',
      driver_name: 'Manuel Vargas Llerena',
      route_code: 'RT-NORTE-01',
      total_gross_weight_kg: 3450.5,
      notes: 'Manifiesto consolidado con 5 paradas de distribución.',
      items: [
        {
          code: 'ENV-01',
          description: 'Pallet 01 - Tienda Los Olivos',
          unit: 'PLT',
          expected_quantity: '1.00',
          received_quantity: '1.00',
          status: 'EN RUTA',
        },
      ],
    },
  },
  {
    code: 'POD',
    name: 'Prueba de Entrega Digital (POD)',
    shortName: 'Prueba Entrega (POD)',
    category: 'TRANSPORT',
    categoryLabel: 'Transporte y Despacho',
    description: 'Constancia de entrega final con firma digital y recepción en destino.',
    sampleCustomData: {
      recipient_name: 'María Alejandra Torres',
      recipient_dni: '45892104',
      delivery_address: 'Av. República de Panamá 3545, San Isidro, Lima',
      received_condition: 'CONFORME_TOTAL',
      notes: 'Entrega realizada satisfactoriamente con firma y sello de recepción en garita.',
    },
  },

  // Guías y Comprobantes SUNAT
  {
    code: 'GRR',
    name: 'Guía de Remisión Remitente (GRR)',
    shortName: 'GRR Remitente',
    category: 'BILLING_LEGAL',
    categoryLabel: 'Comprobantes Oficiales',
    description: 'Documento tributario que sustenta el traslado de bienes desde el remitente.',
    sampleCustomData: {
      transfer_reason: 'VENTA',
      gross_weight_kg: 1200.0,
      unit_of_measure: 'KGM',
      origin_ubigeo: '150101',
      destination_ubigeo: '150112',
    },
  },
  {
    code: 'GRT',
    name: 'Guía de Remisión Transportista (GRT)',
    shortName: 'GRT Transportista',
    category: 'BILLING_LEGAL',
    categoryLabel: 'Comprobantes Oficiales',
    description: 'Documento tributario emitido por la empresa de transporte público.',
    sampleCustomData: {
      mtc_registry_number: 'MTC-LIMA-9921',
      transport_modality: 'PUBLICO',
      sender_ruc: '20512345678',
      recipient_ruc: '20601234567',
    },
  },
  {
    code: 'OCD',
    name: 'Orden de Compra Directa (OCD)',
    shortName: 'Orden Compra (OCD)',
    category: 'BILLING_LEGAL',
    categoryLabel: 'Comprobantes Oficiales',
    description: 'Comprobante institucional formal de adquisición y condiciones comerciales.',
    sampleCustomData: {
      vendor_code: 'PROV-4412',
      payment_terms: 'CREDITO_30_DIAS',
      currency: 'PEN',
      total_amount: 15420.0,
    },
  },
]

