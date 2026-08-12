import { readFile } from 'node:fs/promises'

const targetVersion = '0.9.8'
const defaultCloudRunOrigin = 'https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app'

const requiredPaths = [
  '/api/auth/change-password',
  '/api/auth/csrf',
  '/api/auth/login',
  '/api/auth/logout',
  '/api/auth/logout-all',
  '/api/auth/me',
  '/api/auth/refresh',
  '/api/auth/register',
  '/api/auth/sessions',
  '/api/auth/sessions/{session_id}',
  '/api/clients',
  '/api/clients/{client_id}',
  '/api/continuous-auth/evaluate',
  '/api/continuous-auth/evaluations',
  '/api/continuous-auth/evaluations/{evaluation_id}',
  '/api/continuous-auth/reverify',
  '/api/continuous-auth/status',
  '/api/dashboard/summary',
  '/api/health',
  '/api/i18n/catalog',
  '/api/incidents',
  '/api/incidents/{incident_id}',
  '/api/incidents/{incident_id}/resolve',
  '/api/inventory',
  '/api/inventory/{item_id}',
  '/api/inventory/movements',
  '/api/models/status',
  '/api/reports/deliveries-by-date',
  '/api/reports/incidents-summary',
  '/api/reports/low-stock',
  '/api/reports/routes-summary',
  '/api/reports/shipments-by-priority',
  '/api/reports/shipments-by-status',
  '/api/research/consent',
  '/api/research/consent/current',
  '/api/research/consent/withdraw',
  '/api/research/participants',
  '/api/research/participants/me',
  '/api/research/participants/self-enroll',
  '/api/research/participants/{participant_id}',
  '/api/research/participants/{participant_id}/withdraw',
  '/api/research/sessions',
  '/api/research/sessions/start',
  '/api/research/sessions/{session_id}',
  '/api/research/sessions/{session_id}/annotation',
  '/api/research/sessions/{session_id}/behavior-batches',
  '/api/research/sessions/{session_id}/cancel',
  '/api/research/sessions/{session_id}/face-captures',
  '/api/research/sessions/{session_id}/finish',
  '/api/routes',
  '/api/routes/{route_id}',
  '/api/routes/{route_id}/assign-shipments',
  '/api/routes/{route_id}/shipments/{shipment_id}',
  '/api/shipments',
  '/api/shipments/{shipment_id}',
  '/api/shipments/{shipment_id}/status',
  '/api/shipments/{shipment_id}/timeline',
  '/api/warehouses',
  '/api/warehouses/{warehouse_id}',
]

const requiredSchemas = [
  'AuthResponse',
  'ContinuousAuthEvaluateRequest',
  'ContinuousAuthEvaluateResponse',
  'ContinuousAuthStatusResponse',
  'ModelStatusResponse',
  'ApprovalRequestResponseSchema',
  'ApprovalSubmitSchema',
  'DecisionRecordSchema',
  'PolicyConditionCreateSchema',
  'PolicyCreateSchema',
  'PolicyResponseSchema',
  'PurchaseOrderCancelRequest',
  'PurchaseOrderDetailResponse',
  'PurchaseOrderGenerationPlanRequest',
  'PurchaseOrderGenerationPlanResponse',
  'PurchaseOrderRejectRequest',
  'PurchaseOrderReturnRequest',
  'PurchaseOrderSummaryResponse',
  'ShipmentRead',
  'StepDefinitionCreateSchema',
  'TranslationCatalogResponse',
]

const requiredOperations = {
  // Procurement / Purchase Orders
  '/api/logistics/procurement/purchase-orders': ['get'],
  '/api/logistics/procurement/purchase-orders/plan-generation': ['post'],
  '/api/logistics/procurement/purchase-orders/{po_id}': ['get'],
  '/api/logistics/procurement/purchase-orders/{po_id}/submit': ['post'],
  '/api/logistics/procurement/purchase-orders/{po_id}/approve': ['post'],
  '/api/logistics/procurement/purchase-orders/{po_id}/reject': ['post'],
  '/api/logistics/procurement/purchase-orders/{po_id}/return-for-changes': ['post'],
  '/api/logistics/procurement/purchase-orders/{po_id}/cancel': ['post'],
  '/api/logistics/procurement-approvals/policies': ['get', 'post'],
  '/api/logistics/procurement-approvals/policies/{policy_id}': ['get'],
  '/api/logistics/procurement-approvals/policy-versions/{version_id}/activate': ['post'],
  '/api/logistics/procurement-approvals/policy-versions/{version_id}/conditions': ['post'],
  '/api/logistics/procurement-approvals/policy-versions/{version_id}/steps': ['post'],
  '/api/logistics/procurement-approvals/requests': ['post'],
  '/api/logistics/procurement-approvals/requests/{request_id}': ['get'],
  '/api/logistics/procurement-approvals/requests/{request_id}/audit-seal': ['get'],
  '/api/logistics/procurement-approvals/assignments/my-pending': ['get'],
  '/api/logistics/procurement-approvals/assignments/{assignment_id}/decision': ['post'],
  // Business Partners, Products, Units
  '/api/logistics/business-partners': ['get', 'post'],
  '/api/logistics/products': ['get', 'post'],
  '/api/logistics/units': ['get', 'post'],
  '/api/logistics/company-profile': ['get', 'post'],
  '/api/logistics/company-profile/document-preview': ['post'],
  // Vehicles & Drivers
  '/api/logistics/vehicles': ['post'],
  '/api/logistics/vehicles/{vehicle_id}': ['get'],
  '/api/logistics/vehicles/{vehicle_id}/activate': ['post'],
  '/api/logistics/vehicles/{vehicle_id}/block': ['post'],
  '/api/logistics/vehicles/{vehicle_id}/unblock': ['post'],
  '/api/logistics/vehicles/{vehicle_id}/plate-change': ['post'],
  '/api/logistics/vehicles/{vehicle_id}/capacity-profiles': ['post'],
  '/api/logistics/vehicles/{vehicle_id}/carrier-assignments': ['post'],
  '/api/logistics/vehicles/{vehicle_id}/documents': ['get', 'post'],
  '/api/logistics/vehicles/{vehicle_id}/verifications': ['get', 'post'],
  '/api/logistics/vehicles/{vehicle_id}/verification-compliance': ['get'],
  '/api/logistics/vehicle-verifications/{verification_id}/apply': ['post'],
  '/api/logistics/drivers': ['get', 'post'],
  // Warehouse Docks & Unloading Operations
  '/api/logistics/warehouse-docks': ['get', 'post'],
  '/api/logistics/warehouse-docks/{dock_id}': ['get'],
  '/api/logistics/unloading-operations': ['get'],
  '/api/logistics/unloading-operations/{operation_id}': ['get'],
  // Gate Check-ins & Warehouse Gates
  '/api/logistics/gate-check-ins': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}': ['get'],
  '/api/logistics/warehouse-gates': ['get', 'post'],
  '/api/logistics/warehouse-gates/{gate_id}': ['get'],
  // Supplier Evaluations
  '/api/logistics/supplier-evaluations/evaluations': ['post'],
  '/api/logistics/supplier-evaluations/evaluations/{evaluation_id}/calculate': ['post'],
  '/api/logistics/supplier-evaluations/templates': ['get', 'post'],
  // Files Two-Phase Upload
  '/api/logistics/files/upload-sessions': ['post'],
  '/api/logistics/files/upload-sessions/{session_id}/finalize': ['post'],
  '/api/logistics/files': ['get'],
  '/api/logistics/files/{file_id}': ['get'],
  // RUC
  '/api/logistics/ruc/{ruc}': ['get'],
  '/api/logistics/ruc/sources/health': ['get'],
  '/api/logistics/ruc/datasets/current': ['get'],
  '/api/logistics/ruc/datasets/{dataset_id}/activate': ['post'],
  '/api/logistics/ruc/imports': ['post'],
  '/api/logistics/ruc/imports/{job_id}': ['get'],
  '/api/logistics/ruc/assisted-verifications': ['post'],
  '/api/logistics/ruc/assisted-verifications/{verification_id}/approve': ['post'],
  '/api/logistics/ruc/business-partners/{partner_id}/verify-ruc': ['post'],
  '/api/logistics/ruc/business-partners/{partner_id}/apply-ruc-data': ['post'],
  // Documents (binary downloads fixed in this audit)
  '/api/logistics/documents': ['get'],
  '/api/logistics/documents/{document_id}': ['get'],
  '/api/logistics/documents/{document_id}/history': ['get'],
  '/api/logistics/documents/{document_id}/preview': ['get'],
  '/api/logistics/documents/{document_id}/pdf': ['get'],
  '/api/logistics/documents/{document_id}/print-events': ['post'],
  '/api/logistics/documents/{document_id}/reprint': ['post'],
  '/api/logistics/documents/{document_id}/cancel': ['post'],
  '/api/logistics/documents/export': ['post'],
  '/api/logistics/document-series': ['get'],
  // Warehouse modeling (label PDF fixed in this audit)
  '/api/logistics/warehouses/{warehouse_id}/locations': ['get', 'post'],
  '/api/logistics/warehouses/locations/{location_id}/qr': ['get'],
  '/api/logistics/warehouses/locations/{location_id}/label.pdf': ['get'],
  // Gate check-in sub-resources (inspections, evidence, documents)
  '/api/logistics/gate-check-ins/{check_in_id}/vehicle-inspection': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/driver-inspection': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/documents': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/seal-inspection': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/check-results': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/exceptions': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/corrections': ['get', 'post'],
  '/api/logistics/gate-check-ins/{check_in_id}/photos': ['get'],
  '/api/logistics/gate-check-ins/{check_in_id}/photos/associate': ['post'],
  '/api/logistics/gate-check-ins/{check_in_id}/document': ['get'],
  '/api/logistics/gate-check-ins/{check_in_id}/preview': ['get'],
  '/api/logistics/gate-check-ins/{check_in_id}/issue-document': ['post'],
  '/api/logistics/gate-check-ins/{check_in_id}/capabilities': ['get'],
  '/api/logistics/gate-check-ins/{check_in_id}/history': ['get'],
  '/api/logistics/gate-verification-exceptions/{exception_id}/approve': ['post'],
  '/api/logistics/gate-verification-exceptions/{exception_id}/reject': ['post'],
  '/api/logistics/gate-check-in-corrections/{correction_id}/approve': ['post'],
  // Inbound dock assignments
  '/api/logistics/inbound-dock-assignments': ['get'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}': ['get'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/start-movement': ['post'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/confirm-dock-arrival': ['post'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/cancel': ['post'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/release-dock': ['post'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/reassign': ['post'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/metrics': ['get'],
  '/api/logistics/inbound-dock-assignments/{assignment_id}/history': ['get'],
  // Dock assignment plans
  '/api/logistics/dock-assignment-plans': ['post'],
  '/api/logistics/dock-assignment-plans/{assignment_hash}/execute': ['post'],
  // Unloading operations sub-resources
  '/api/logistics/unloading-operations/{operation_id}/start': ['post'],
  '/api/logistics/unloading-operations/{operation_id}/pause': ['post'],
  '/api/logistics/unloading-operations/{operation_id}/resume': ['post'],
  '/api/logistics/unloading-operations/{operation_id}/abort': ['post'],
  '/api/logistics/unloading-operations/{operation_id}/complete': ['post'],
  '/api/logistics/unloading-operations/{operation_id}/readiness-checks': ['get', 'post'],
  '/api/logistics/unloading-operations/{operation_id}/completion-checks': ['get', 'post'],
  '/api/logistics/unloading-operations/{operation_id}/seal-opening': ['get', 'post'],
  '/api/logistics/unloading-operations/{operation_id}/pauses': ['get'],
  '/api/logistics/unloading-operations/{operation_id}/responsibles': ['get', 'post'],
  '/api/logistics/unloading-operations/{operation_id}/equipment': ['get', 'post'],
  '/api/logistics/unloading-operations/{operation_id}/receiving-preparation': ['get'],
  '/api/logistics/unloading-operations/{operation_id}/operational-times': ['get'],
  '/api/logistics/unloading-operations/{operation_id}/integrity': ['get'],
  '/api/logistics/unloading-operations/{operation_id}/time-corrections': ['post'],
  // Inbound dock queue
  '/api/logistics/inbound-dock-queue': ['get'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}': ['get'],
  '/api/logistics/inbound-dock-queue/summary': ['get'],
  '/api/logistics/inbound-dock-queue/ordered': ['get'],
  '/api/logistics/inbound-dock-queue/from-gate-check-in': ['post'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}/change-priority': ['post'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}/mark-ready': ['post'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}/hold': ['post'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}/resume': ['post'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}/remove': ['post'],
  '/api/logistics/inbound-dock-queue/{queue_entry_id}/history': ['get'],
  // Dock operation metrics & exports
  '/api/logistics/dock-operation-metrics': ['get'],
  '/api/logistics/dock-operation-exports': ['post'],
  '/api/logistics/dock-operation-exports/{export_job_id}': ['get'],
  // Supplier evaluation templates
  '/api/logistics/supplier-evaluations/templates/{template_id}/versions': ['post'],
  '/api/logistics/supplier-evaluations/versions/{version_id}/activate': ['post'],
  '/api/logistics/supplier-evaluations/evaluations/{evaluation_id}/manual-scores': ['post'],
  '/api/logistics/supplier-evaluations/evaluations/{evaluation_id}/decisions': ['post'],
  // Purchase requisitions
  '/api/logistics/procurement/requisitions': ['get', 'post'],
  '/api/logistics/procurement/requisitions/{requisition_id}': ['get'],
  '/api/logistics/procurement/requisitions/{requisition_id}/validate': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/submit': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/start-review': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/approve': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/reject': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/return': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/withdraw': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/cancel': ['post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/revisions': ['get'],
  '/api/logistics/procurement/requisitions/{requisition_id}/comments': ['get', 'post'],
  '/api/logistics/procurement/requisitions/{requisition_id}/history': ['get'],
  // Logistics context
  '/api/logistics/me': ['get'],
  '/api/logistics/me/context': ['post'],
  '/api/logistics/me/permissions': ['get'],
  '/api/logistics/authorization/check': ['post'],
}

async function readApiBase() {
  if (process.env.VITE_API_URL?.trim()) {
    return process.env.VITE_API_URL.trim().replace(/\/+$/, '')
  }

  try {
    const contents = await readFile(new URL('../.env', import.meta.url), 'utf8')
    const entry = contents
      .split(/\r?\n/)
      .find((line) => line.trim().startsWith('VITE_API_URL='))
    return entry?.slice(entry.indexOf('=') + 1).trim().replace(/\/+$/, '') ?? ''
  } catch {
    return '/api'
  }
}

function fail(message) {
  throw new Error(`OpenAPI ${targetVersion} incompatible: ${message}`)
}

const configuredApiBase = await readApiBase()
const origin = process.env.OPENAPI_ORIGIN?.replace(/\/+$/, '') || defaultCloudRunOrigin

let openApiUrl = `${origin}/openapi.json`
let response
try {
  response = await fetch(openApiUrl, {
    headers: { Accept: 'application/json' },
  })
} catch {
  // If remote fetch fails, try localhost fallback
  const localUrl = `http://localhost:8000/openapi.json`
  response = await fetch(localUrl, {
    headers: { Accept: 'application/json' },
  })
}

if (!response?.ok) {
  fail(`GET ${openApiUrl} respondió ${response?.status}.`)
}

const specification = await response.json()
if (specification?.info?.version !== targetVersion) {
  fail(`se esperaba versión ${targetVersion} y se recibió ${specification?.info?.version}.`)
}

for (const path of requiredPaths) {
  if (!specification.paths?.[path]) {
    fail(`falta la ruta ${path}.`)
  }
}

for (const schema of requiredSchemas) {
  if (!specification.components?.schemas?.[schema]) {
    fail(`falta el esquema ${schema}.`)
  }
}

for (const [path, methods] of Object.entries(requiredOperations)) {
  for (const method of methods) {
    if (!specification.paths?.[path]?.[method]) {
      fail(`falta la operación ${method.toUpperCase()} ${path}.`)
    }
  }
}

const purchaseOrderDetail =
  specification.components.schemas.PurchaseOrderDetailResponse
for (const property of ['subtotal', 'discount_total', 'tax_total', 'freight_total', 'grand_total']) {
  if (purchaseOrderDetail.properties?.[property]?.type !== 'string') {
    fail(`${property} de PurchaseOrderDetailResponse ya no es decimal string.`)
  }
}

const approvalRequest =
  specification.components.schemas.ApprovalRequestResponseSchema
if (approvalRequest.properties?.amount?.type !== 'string') {
  fail('amount de ApprovalRequestResponseSchema ya no es decimal string.')
}

const statusSchema =
  specification.components.schemas.ContinuousAuthStatusResponse
if (statusSchema.properties?.components_available?.type !== 'object') {
  fail('components_available ya no es un objeto.')
}

const evaluationSchema =
  specification.components.schemas.ContinuousAuthEvaluateResponse
if (!evaluationSchema.properties?.evaluation?.$ref) {
  fail('ContinuousAuthEvaluateResponse ya no envuelve evaluation.')
}

const totalOps = Object.values(requiredOperations).reduce((sum, methods) => sum + methods.length, 0)
console.log(
  `OpenAPI ${specification.info.version} validado exitosamente: ` +
    `${requiredPaths.length} rutas base + ${Object.keys(requiredOperations).length} rutas con operaciones (${totalOps} operaciones) verificadas y ` +
    `${requiredSchemas.length} esquemas validados.`,
)
