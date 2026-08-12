import type {
  ComparisonViewMode,
  EvaluationDecisionType,
  QuotationEvaluationStatus,
  DecisionStatus,
  ComparativeDocumentStatus,
  ExportStatus,
  ExportFormat,
  QuotationRoundStatus,
  ScoreStatus,
  TechnicalCompliance,
  OverrideStatus,
  TiePolicy,
  EvaluationCriterionGroup,
} from './types/evaluation'

export function formatDecimal(value: string | null, maxDecimals = 4): string {
  if (value === null || value === '') return '—'
  // No se usa Number para autoridad: solo para presentación visual superficial.
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return value
  return parsed.toLocaleString('es-PE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals,
  })
}

export function formatMoney(
  amount: string | null,
  currency: string | null,
  maxDecimals = 2,
): string {
  if (amount === null || amount === '') return '—'
  const text = formatDecimal(amount, maxDecimals)
  return currency ? `${text} ${currency}` : text
}

export function truncate(value: string, max = 60): string {
  if (value.length <= max) return value
  return `${value.slice(0, max - 1)}…`
}

const STATUS_LABELS: Record<QuotationEvaluationStatus, string> = {
  DRAFT: 'Borrador',
  READY: 'Lista',
  IN_PROGRESS: 'En progreso',
  CALCULATED: 'Calculada',
  UNDER_REVIEW: 'En revisión',
  DECISION_RECORDED: 'Decisión registrada',
  SUPERSEDED: 'Reemplazada',
  CANCELLED: 'Cancelada',
  ARCHIVED: 'Archivada',
}

export function evaluationStatusLabel(status: QuotationEvaluationStatus): string {
  return STATUS_LABELS[status] ?? status
}

const ROUND_STATUS_LABELS: Record<QuotationRoundStatus, string> = {
  DRAFT: 'Borrador',
  OPEN: 'Abierta',
  OPEN_INTERNAL_REVIEW: 'Revisión interna',
  CLOSED: 'Cerrada',
  CANCELLED: 'Cancelada',
  ARCHIVED: 'Archivada',
}

export function roundStatusLabel(status: QuotationRoundStatus): string {
  return ROUND_STATUS_LABELS[status] ?? status
}

const DECISION_TYPE_LABELS: Record<EvaluationDecisionType, string> = {
  SINGLE_SUPPLIER: 'Proveedor único',
  SPLIT_BY_LINE: 'Dividir por línea',
  SPLIT_BY_QUANTITY: 'Dividir por cantidad',
  NO_AWARD: 'No adjudicar',
  REQUOTE: 'Nueva cotización',
  CLARIFICATION: 'Solicitar aclaración',
  MANUAL_EXCEPTION: 'Excepción manual',
}

export function decisionTypeLabel(type: EvaluationDecisionType): string {
  return DECISION_TYPE_LABELS[type] ?? type
}

const DECISION_STATUS_LABELS: Record<DecisionStatus, string> = {
  DRAFT: 'Borrador',
  VALIDATED: 'Validada',
  SUBMITTED: 'Enviada',
  RECORDED: 'Registrada',
  SUPERSEDED: 'Reemplazada',
  CANCELLED: 'Cancelada',
}

export function decisionStatusLabel(status: DecisionStatus): string {
  return DECISION_STATUS_LABELS[status] ?? status
}

const DOC_STATUS_LABELS: Record<ComparativeDocumentStatus, string> = {
  DRAFT: 'Borrador',
  PREVIEW: 'Previsualización',
  ISSUED: 'Emitido',
  VOID: 'Anulado',
  SUPERSEDED: 'Reemplazado',
}

export function comparativeDocumentStatusLabel(
  status: ComparativeDocumentStatus,
): string {
  return DOC_STATUS_LABELS[status] ?? status
}

const EXPORT_STATUS_LABELS: Record<ExportStatus, string> = {
  QUEUED: 'En cola',
  GENERATING: 'Generando',
  AVAILABLE: 'Disponible',
  FAILED: 'Fallida',
  EXPIRED: 'Expirada',
}

export function exportStatusLabel(status: ExportStatus): string {
  return EXPORT_STATUS_LABELS[status] ?? status
}

export function exportFormatLabel(format: ExportFormat): string {
  return format
}

const SCORE_STATUS_LABELS: Record<ScoreStatus, string> = {
  DRAFT: 'Borrador',
  SUBMITTED: 'Enviado',
  ACCEPTED: 'Aceptado',
  REJECTED: 'Rechazado',
  SUPERSEDED: 'Reemplazado',
}

export function scoreStatusLabel(status: ScoreStatus): string {
  return SCORE_STATUS_LABELS[status] ?? status
}

const COMPLIANCE_LABELS: Record<TechnicalCompliance, string> = {
  COMPLIANT: 'Cumple',
  PARTIALLY_COMPLIANT: 'Cumple parcialmente',
  NON_COMPLIANT: 'No cumple',
  ALTERNATIVE_REVIEW: 'Alternativa en revisión',
  NOT_EVALUATED: 'Sin evaluar',
}

export function complianceLabel(compliance: TechnicalCompliance): string {
  return COMPLIANCE_LABELS[compliance] ?? compliance
}

const OVERRIDE_STATUS_LABELS: Record<OverrideStatus, string> = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobado',
  REJECTED: 'Rechazado',
  SUPERSEDED: 'Reemplazado',
}

export function overrideStatusLabel(status: OverrideStatus): string {
  return OVERRIDE_STATUS_LABELS[status] ?? status
}

const TIE_POLICY_LABELS: Record<TiePolicy | 'MANUAL', string> = {
  HIGHEST_TECHNICAL: 'Mayor puntaje técnico',
  LOWEST_PRICE: 'Menor precio',
  LOWEST_RISK: 'Menor riesgo',
  SHORTEST_DELIVERY: 'Menor plazo',
  MANUAL: 'Decisión manual',
  REQUOTE: 'Nueva cotización',
}

export function tiePolicyLabel(policy: TiePolicy | 'MANUAL'): string {
  return TIE_POLICY_LABELS[policy] ?? policy
}

const GROUP_LABELS: Record<EvaluationCriterionGroup, string> = {
  ECONOMIC: 'Económico',
  TECHNICAL: 'Técnico',
  COMMERCIAL: 'Comercial',
  RISK: 'Riesgo',
  QUALITY: 'Calidad',
  COMPLIANCE: 'Cumplimiento',
  OTHER: 'Otro',
}

export function criterionGroupLabel(group: EvaluationCriterionGroup): string {
  return GROUP_LABELS[group] ?? group
}

const VIEW_MODE_LABELS: Record<ComparisonViewMode, string> = {
  ORIGINAL: 'Valor original',
  NORMALIZED: 'Valor normalizado',
  SCORE: 'Puntaje',
  WEIGHTED: 'Puntaje ponderado',
}

export function comparisonViewModeLabel(mode: ComparisonViewMode): string {
  return VIEW_MODE_LABELS[mode] ?? mode
}

/**
 * Valida visualmente un peso decimal como string. Sin autoridad: el backend confirma.
 */
export function isDecimalString(value: string): boolean {
  return /^\d{0,12}(\.\d{0,6})?$/.test(value.trim())
}

/**
 * Suma visual (no autoritativa) de pesos en strings. El backend es la autoridad.
 */
export function visualSum(weights: string[]): string {
  let acc = 0
  for (const w of weights) {
    const n = Number(w)
    if (Number.isFinite(n)) acc += n
  }
  return acc.toFixed(6)
}

export function visualDiff(total: string, target = '100'): string {
  const a = Number(total)
  const b = Number(target)
  if (!Number.isFinite(a) || !Number.isFinite(b)) return '—'
  return (b - a).toFixed(6)
}

export function generateIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}