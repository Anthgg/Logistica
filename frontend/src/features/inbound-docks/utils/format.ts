import type {
  DockAssignmentCapabilities,
  InboundDockAssignmentStatus,
  InboundDockPriority,
  InboundDockQueueStatus,
  OperationalTimeQualityStatus,
  UnloadingCheckResult,
  UnloadingOperationStatus,
  UnloadingReadinessStatus,
  WarehouseDockOperationalStatus,
  WarehouseDockStatus,
} from '../types/inbound-docks'

export function dockStatusLabel(value: WarehouseDockStatus): string {
  switch (value) {
    case 'ACTIVE':
      return 'Activo'
    case 'INACTIVE':
      return 'Inactivo'
    case 'BLOCKED':
      return 'Bloqueado'
    case 'MAINTENANCE':
      return 'Mantenimiento'
    case 'ARCHIVED':
      return 'Archivado'
    default:
      return value
  }
}

export function dockOperationalStatusLabel(
  value: WarehouseDockOperationalStatus,
): string {
  switch (value) {
    case 'AVAILABLE':
      return 'Disponible'
    case 'RESERVED':
      return 'Reservado'
    case 'OCCUPIED':
      return 'Ocupado'
    case 'UNLOADING':
      return 'Descargando'
    case 'PENDING_RELEASE':
      return 'Pendiente de liberar'
    case 'BLOCKED':
      return 'Bloqueado'
    case 'MAINTENANCE':
      return 'Mantenimiento'
    case 'INACTIVE':
      return 'Inactivo'
    case 'UNKNOWN':
      return 'Desconocido'
    default:
      return value
  }
}

export function dockOperationalStatusTone(
  value: WarehouseDockOperationalStatus,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral' {
  switch (value) {
    case 'AVAILABLE':
      return 'success'
    case 'RESERVED':
      return 'info'
    case 'OCCUPIED':
      return 'warning'
    case 'UNLOADING':
      return 'info'
    case 'PENDING_RELEASE':
      return 'warning'
    case 'BLOCKED':
      return 'danger'
    case 'MAINTENANCE':
      return 'muted'
    case 'INACTIVE':
      return 'muted'
    case 'UNKNOWN':
    default:
      return 'neutral'
  }
}

export function dockTypeLabel(value: string): string {
  switch (value) {
    case 'STANDARD':
      return 'Estándar'
    case 'REFRIGERATED':
      return 'Refrigerado'
    case 'HAZMAT':
      return 'Materiales peligrosos'
    case 'OVERSIZED':
      return 'Sobredimensionado'
    case 'DRIVE_THROUGH':
      return 'Pasante'
    case 'COVERED':
      return 'Cubierto'
    case 'OUTDOOR':
      return 'Exterior'
    default:
      return value
  }
}

export function dockDirectionLabel(value: string): string {
  switch (value) {
    case 'INBOUND':
      return 'Entrada'
    case 'OUTBOUND':
      return 'Salida'
    case 'BIDIRECTIONAL':
      return 'Bidireccional'
    default:
      return value
  }
}

export function queueStatusLabel(value: InboundDockQueueStatus): string {
  switch (value) {
    case 'WAITING':
      return 'Esperando'
    case 'ASSIGNED':
      return 'Asignado'
    case 'IN_MOVEMENT':
      return 'En movimiento'
    case 'AT_DOCK':
      return 'En muelle'
    case 'READY':
      return 'Listo para descargar'
    case 'UNLOADING':
      return 'Descargando'
    case 'PAUSED':
      return 'Pausada'
    case 'COMPLETED':
      return 'Completada'
    case 'PENDING_RELEASE':
      return 'Pendiente de liberar'
    case 'RELEASED':
      return 'Liberada'
    case 'HELD':
      return 'Retenida'
    case 'CANCELLED':
      return 'Cancelada'
    default:
      return value
  }
}

export function queueStatusTone(
  value: InboundDockQueueStatus,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral' {
  switch (value) {
    case 'WAITING':
      return 'warning'
    case 'ASSIGNED':
    case 'READY':
      return 'info'
    case 'IN_MOVEMENT':
    case 'AT_DOCK':
    case 'UNLOADING':
      return 'info'
    case 'PAUSED':
      return 'warning'
    case 'COMPLETED':
    case 'RELEASED':
      return 'success'
    case 'PENDING_RELEASE':
      return 'warning'
    case 'HELD':
      return 'danger'
    case 'CANCELLED':
      return 'muted'
    default:
      return 'neutral'
  }
}

export function assignmentStatusLabel(
  value: InboundDockAssignmentStatus,
): string {
  switch (value) {
    case 'ASSIGNED':
      return 'Asignado'
    case 'IN_MOVEMENT':
      return 'En movimiento'
    case 'AT_DOCK':
      return 'En muelle'
    case 'UNLOADING_ACTIVE':
      return 'Descargando'
    case 'UNLOADING_PAUSED':
      return 'Descarga pausada'
    case 'UNLOADING_COMPLETED':
      return 'Descarga finalizada'
    case 'PENDING_RELEASE':
      return 'Pendiente de liberar'
    case 'RELEASED':
      return 'Liberado'
    case 'CANCELLED':
      return 'Cancelado'
    case 'REASSIGNED':
      return 'Reasignado'
    default:
      return value
  }
}

export function assignmentStatusTone(
  value: InboundDockAssignmentStatus,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral' {
  switch (value) {
    case 'ASSIGNED':
      return 'info'
    case 'IN_MOVEMENT':
    case 'AT_DOCK':
    case 'UNLOADING_ACTIVE':
      return 'info'
    case 'UNLOADING_PAUSED':
      return 'warning'
    case 'UNLOADING_COMPLETED':
    case 'PENDING_RELEASE':
      return 'warning'
    case 'RELEASED':
      return 'success'
    case 'CANCELLED':
      return 'muted'
    case 'REASSIGNED':
      return 'warning'
    default:
      return 'neutral'
  }
}

export function priorityLabel(value: InboundDockPriority): string {
  switch (value) {
    case 'LOW':
      return 'Baja'
    case 'NORMAL':
      return 'Normal'
    case 'HIGH':
      return 'Alta'
    case 'URGENT':
      return 'Urgente'
    default:
      return value
  }
}

export function priorityTone(
  value: InboundDockPriority,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral' {
  switch (value) {
    case 'LOW':
      return 'muted'
    case 'NORMAL':
      return 'neutral'
    case 'HIGH':
      return 'warning'
    case 'URGENT':
      return 'danger'
    default:
      return 'neutral'
  }
}

export function unloadingStatusLabel(
  value: UnloadingOperationStatus,
): string {
  switch (value) {
    case 'CREATED':
      return 'Creada'
    case 'READINESS_PENDING':
      return 'Readiness pendiente'
    case 'READY':
      return 'Lista'
    case 'ACTIVE':
      return 'Activa'
    case 'PAUSED':
      return 'Pausada'
    case 'COMPLETED':
      return 'Completada'
    case 'ABORTED':
      return 'Abortada'
    case 'CANCELLED':
      return 'Cancelada'
    default:
      return value
  }
}

export function readinessStatusLabel(
  value: UnloadingReadinessStatus,
): string {
  switch (value) {
    case 'PENDING':
      return 'Pendiente'
    case 'COMPLETE':
      return 'Completo'
    case 'COMPLETE_WITH_OBSERVATIONS':
      return 'Completo con observaciones'
    case 'BLOCKED':
      return 'Bloqueado'
    case 'OVERRIDE_PENDING':
      return 'Override pendiente'
    case 'OVERRIDE_APPROVED':
      return 'Override aprobado'
    default:
      return value
  }
}

export function checkResultLabel(value: UnloadingCheckResult | null): string {
  switch (value) {
    case 'PASS':
      return 'Cumple'
    case 'PASS_WITH_OBSERVATION':
      return 'Cumple con observación'
    case 'FAIL':
      return 'No cumple'
    case 'NOT_APPLICABLE':
      return 'No aplica'
    case 'PENDING_REVIEW':
      return 'Requiere revisión'
    case null:
    default:
      return 'Pendiente'
  }
}

export function dataQualityLabel(
  value: OperationalTimeQualityStatus,
): string {
  switch (value) {
    case 'COMPLETE':
      return 'Completa'
    case 'PARTIAL':
      return 'Parcial'
    case 'MISSING_EVENT':
      return 'Falta evento'
    case 'INVALID_ORDER':
      return 'Orden inválido'
    case 'CORRECTED':
      return 'Corregida'
    case 'IMPORTED':
      return 'Importada'
    case 'INTEGRITY_FAILED':
      return 'Integridad fallida'
    default:
      return value
  }
}

export function dataQualityTone(
  value: OperationalTimeQualityStatus,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral' {
  switch (value) {
    case 'COMPLETE':
    case 'CORRECTED':
      return 'success'
    case 'PARTIAL':
    case 'IMPORTED':
      return 'info'
    case 'MISSING_EVENT':
    case 'INVALID_ORDER':
      return 'warning'
    case 'INTEGRITY_FAILED':
      return 'danger'
    default:
      return 'neutral'
  }
}

export function severityLabel(
  value: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
): string {
  switch (value) {
    case 'LOW':
      return 'Baja'
    case 'MEDIUM':
      return 'Media'
    case 'HIGH':
      return 'Alta'
    case 'CRITICAL':
      return 'Crítica'
    default:
      return value
  }
}

export function sealOpeningResultLabel(value: string): string {
  switch (value) {
    case 'OPENED_NORMALLY':
      return 'Abierto normalmente'
    case 'OPENED_WITH_OBSERVATION':
      return 'Abierto con observación'
    case 'ABSENT':
      return 'Ausente'
    case 'DOES_NOT_MATCH':
      return 'No coincide'
    case 'PREVIOUSLY_BROKEN':
      return 'Previamente roto'
    case 'POSSIBLE_TAMPERING':
      return 'Posible manipulación'
    case 'NOT_APPLICABLE':
      return 'No aplica'
    default:
      return value
  }
}

export function compatibilityLabel(
  value:
    | 'COMPATIBLE'
    | 'COMPATIBLE_WITH_WARNINGS'
    | 'INCOMPATIBLE'
    | 'REQUIRES_REVIEW'
    | 'INCOMPLETE_INFO',
): string {
  switch (value) {
    case 'COMPATIBLE':
      return 'Compatible'
    case 'COMPATIBLE_WITH_WARNINGS':
      return 'Compatible con advertencias'
    case 'INCOMPATIBLE':
      return 'Incompatible'
    case 'REQUIRES_REVIEW':
      return 'Requiere revisión'
    case 'INCOMPLETE_INFO':
      return 'Información incompleta'
    default:
      return value
  }
}

export function compatibilityTone(
  value:
    | 'COMPATIBLE'
    | 'COMPATIBLE_WITH_WARNINGS'
    | 'INCOMPATIBLE'
    | 'REQUIRES_REVIEW'
    | 'INCOMPLETE_INFO',
): 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral' {
  switch (value) {
    case 'COMPATIBLE':
      return 'success'
    case 'COMPATIBLE_WITH_WARNINGS':
      return 'warning'
    case 'INCOMPATIBLE':
      return 'danger'
    case 'REQUIRES_REVIEW':
      return 'info'
    case 'INCOMPLETE_INFO':
      return 'muted'
    default:
      return 'neutral'
  }
}

export function formatServerTime(iso: string | null | undefined, timeZone?: string | null): string {
  if (!iso) return '—'
  try {
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return iso
    return new Intl.DateTimeFormat('es-PE', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: timeZone ?? undefined,
    }).format(date)
  } catch {
    return iso
  }
}

export function formatServerDateTime(
  iso: string | null | undefined,
  timeZone?: string | null,
): string {
  if (!iso) return '—'
  try {
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return iso
    return new Intl.DateTimeFormat('es-PE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: timeZone ?? undefined,
    }).format(date)
  } catch {
    return iso
  }
}

export function formatSecondsApprox(seconds: number | null | undefined): string {
  if (seconds == null) return '—'
  if (seconds < 0) return '—'
  const totalSeconds = Math.floor(seconds)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  const parts: string[] = []
  if (h > 0) parts.push(`${h}h`)
  if (h > 0 || m > 0) parts.push(`${m.toString().padStart(2, '0')}m`)
  parts.push(`${s.toString().padStart(2, '0')}s`)
  return parts.join(' ')
}

export function formatDurationSeconds(seconds: number | null | undefined): string {
  return formatSecondsApprox(seconds)
}

export function formatTimeWindow(
  start: string | null | undefined,
  end: string | null | undefined,
  timeZone?: string | null,
): string {
  if (!start || !end) return '—'
  const startLabel = formatServerTime(start, timeZone)
  const endLabel = formatServerTime(end, timeZone)
  return `${startLabel} – ${endLabel}`
}

export interface DockCapabilitiesBag {
  capabilities: DockAssignmentCapabilities | null | undefined
  has: (code: keyof DockAssignmentCapabilities) => boolean
  missing: (codes: Array<keyof DockAssignmentCapabilities>) => string[]
}

export function useCapabilitiesBag(
  capabilities: DockAssignmentCapabilities | null | undefined,
): DockCapabilitiesBag {
  return {
    capabilities,
    has: (code) => Boolean(capabilities?.[code]),
    missing: (codes) => codes.filter((c) => !capabilities?.[c]) as Array<keyof DockAssignmentCapabilities>,
  }
}
