import { clsx } from 'clsx'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { StatusPill } from './ui/Primitives'
import {
  formatServerTime,
  formatSecondsApprox,
  priorityLabel,
  priorityTone,
  queueStatusLabel,
  queueStatusTone,
} from '../utils/format'
import type {
  InboundDockAssignmentStatus,
  InboundDockPriority,
  InboundDockQueueEntry,
  InboundDockQueueStatus,
  UnloadingOperationStatus,
} from '../types/inbound-docks'

export interface BoardCardEntry {
  entry?: InboundDockQueueEntry
  assignmentId?: string
  assignmentStatus?: InboundDockAssignmentStatus
  unloadingStatus?: UnloadingOperationStatus
  dockCode?: string | null
  serverTimeIso?: string | null
  awaitingRelease?: boolean
  waitingSeconds?: number | null
  priority?: InboundDockPriority
  status?: InboundDockQueueStatus
  alerts?: string[]
  responsible?: string | null
  message?: string
}

const STATUS_GROUPS: Array<{
  key: string
  label: string
  description: string
  predicate: (entry: BoardCardEntry) => boolean
}> = [
  {
    key: 'WAITING',
    label: 'Esperando asignación',
    description: 'Vehículos en cola sin muelle asignado.',
    predicate: (e) =>
      !e.assignmentId &&
      (e.entry?.status === 'WAITING' || e.status === 'WAITING' || (!e.status && !e.assignmentId)),
  },
  {
    key: 'ASSIGNED',
    label: 'Muelle asignado',
    description: 'Vehículos con muelle, aún en garita o sin movimiento.',
    predicate: (e) =>
      Boolean(e.assignmentId) &&
      (e.assignmentStatus === 'ASSIGNED' || e.entry?.status === 'ASSIGNED'),
  },
  {
    key: 'IN_MOVEMENT',
    label: 'En movimiento',
    description: 'Vehículos en camino al muelle.',
    predicate: (e) => e.assignmentStatus === 'IN_MOVEMENT' || e.entry?.status === 'IN_MOVEMENT',
  },
  {
    key: 'AT_DOCK',
    label: 'En muelle',
    description: 'Vehículos ocupando muelle, sin descarga activa.',
    predicate: (e) =>
      e.assignmentStatus === 'AT_DOCK' || e.entry?.status === 'AT_DOCK' || e.entry?.status === 'READY',
  },
  {
    key: 'READY',
    label: 'Lista para descargar',
    description: 'Muelle ocupado, descarga aún no iniciada.',
    predicate: (e) =>
      e.assignmentStatus === 'AT_DOCK' && e.unloadingStatus === 'READY',
  },
  {
    key: 'UNLOADING',
    label: 'Descargando',
    description: 'Operaciones de descarga en curso.',
    predicate: (e) =>
      e.assignmentStatus === 'UNLOADING_ACTIVE' ||
      e.entry?.status === 'UNLOADING' ||
      e.unloadingStatus === 'ACTIVE',
  },
  {
    key: 'PAUSED',
    label: 'Pausada',
    description: 'Operaciones con pausa activa.',
    predicate: (e) =>
      e.assignmentStatus === 'UNLOADING_PAUSED' || e.unloadingStatus === 'PAUSED' || e.entry?.status === 'PAUSED',
  },
  {
    key: 'COMPLETED',
    label: 'Descarga completada',
    description: 'Descarga finalizada pendiente de liberación.',
    predicate: (e) =>
      e.assignmentStatus === 'UNLOADING_COMPLETED' ||
      e.unloadingStatus === 'COMPLETED' ||
      e.entry?.status === 'COMPLETED',
  },
  {
    key: 'PENDING_RELEASE',
    label: 'Pendiente de liberar',
    description: 'Muelles con descarga finalizada.',
    predicate: (e) =>
      e.assignmentStatus === 'PENDING_RELEASE' ||
      e.awaitingRelease === true ||
      e.entry?.status === 'PENDING_RELEASE',
  },
  {
    key: 'RELEASED',
    label: 'Liberada',
    description: 'Operaciones finalizadas con muelle liberado.',
    predicate: (e) =>
      e.assignmentStatus === 'RELEASED' || e.entry?.status === 'RELEASED',
  },
]

export function groupEntriesByStatus(entries: BoardCardEntry[]): Record<string, BoardCardEntry[]> {
  const groups: Record<string, BoardCardEntry[]> = {}
  for (const group of STATUS_GROUPS) {
    groups[group.key] = []
  }
  for (const entry of entries) {
    const group = STATUS_GROUPS.find((g) => g.predicate(entry))
    if (group) groups[group.key].push(entry)
    else groups['WAITING'].push(entry)
  }
  return groups
}

export function InboundBoardCard({
  entry,
  onSelect,
  onAction,
}: {
  entry: BoardCardEntry
  onSelect?: () => void
  onAction?: { label: string; onClick: () => void }[]
}) {
  const status = entry.assignmentStatus ?? entry.entry?.status ?? entry.status
  const statusLabel = status ? queueStatusLabel(status as InboundDockQueueStatus) : entry.message ?? '—'
  const priority = entry.priority ?? entry.entry?.priority
  const waiting = entry.waitingSeconds ?? entry.entry?.waiting_seconds
  return (
    <article
      className={clsx(
        'flex flex-col gap-1.5 rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-xs',
        entry.alerts && entry.alerts.length > 0 && 'border-amber-200 bg-amber-50/30',
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        {priority && <StatusPill tone={priorityTone(priority)}>{priorityLabel(priority)}</StatusPill>}
        {status && (
          <StatusPill tone={queueStatusTone(status as InboundDockQueueStatus)}>{statusLabel}</StatusPill>
        )}
        {entry.dockCode && (
          <span className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
            <LogisticsIcon name="dock" size={12} className="text-slate-500" /> {entry.dockCode}
          </span>
        )}
        {entry.alerts && entry.alerts.length > 0 && (
          <span className="inline-flex items-center gap-1 text-[10px] text-amber-700">
            <LogisticsIcon name="alert" size={11} /> {entry.alerts.length} alerta(s)
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-700">
        <span className="font-mono">CPV {entry.entry?.cpv_code ?? '—'}</span>
        <span className="font-mono">CIT {entry.entry?.cit_code ?? '—'}</span>
        <span>{entry.entry?.supplier_name ?? '—'}</span>
        <span className="font-mono">{entry.entry?.vehicle_plate ?? '—'}</span>
        <span className="text-slate-500">{entry.entry?.vehicle_type ?? '—'}</span>
        <span className="text-slate-500">Llegada {entry.entry?.entered_queue_at ? formatServerTime(entry.entry.entered_queue_at) : '—'}</span>
        <span className="text-slate-500">
          Esperando{' '}
          <span className="font-mono text-slate-700">
            {waiting != null ? formatSecondsApprox(waiting) : '—'}
          </span>
        </span>
        <span className="text-slate-500">{entry.responsible ? `Resp.: ${entry.responsible}` : '—'}</span>
      </div>
      <div className="flex items-center justify-end gap-1">
        {onAction?.map((a) => (
          <button
            key={a.label}
            type="button"
            onClick={a.onClick}
            className="rounded-md border border-slate-200 px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
          >
            {a.label}
          </button>
        ))}
        {onSelect && (
          <button
            type="button"
            onClick={onSelect}
            className="rounded-md bg-[#1F4E6D] px-2 py-1 text-[11px] font-semibold text-white hover:bg-[#173a55]"
          >
            Detalle
          </button>
        )}
      </div>
    </article>
  )
}

export function InboundBoard({
  entries,
  onSelectEntry,
  onSelectAssignment,
  actionsFor,
}: {
  entries: BoardCardEntry[]
  onSelectEntry?: (entry: InboundDockQueueEntry) => void
  onSelectAssignment?: (assignmentId: string) => void
  actionsFor?: (entry: BoardCardEntry) => Array<{ label: string; onClick: () => void }>
}) {
  const groups = groupEntriesByStatus(entries)
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
      {STATUS_GROUPS.map((g) => (
        <section
          key={g.key}
          className="rounded-xl border border-slate-200 bg-slate-50/40 p-3"
          aria-label={g.label}
        >
          <header className="mb-2 flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wide text-slate-700">
              {g.label}
            </h2>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-700">
              {groups[g.key]?.length ?? 0}
            </span>
          </header>
          <p className="mb-2 text-[10px] text-slate-500">{g.description}</p>
          <ul className="space-y-2">
            {(groups[g.key] ?? []).map((e, idx) => (
              <li key={`${e.entry?.id ?? e.assignmentId ?? 'row'}-${idx}`}>
                <InboundBoardCard
                  entry={e}
                  onSelect={
                    e.entry && onSelectEntry
                      ? () => onSelectEntry(e.entry as InboundDockQueueEntry)
                      : e.assignmentId && onSelectAssignment
                        ? () => onSelectAssignment(e.assignmentId as string)
                        : undefined
                  }
                  onAction={actionsFor ? actionsFor(e) : undefined}
                />
              </li>
            ))}
            {!(groups[g.key]?.length ?? 0) && (
              <li className="rounded-md border border-dashed border-slate-200 bg-white px-3 py-2 text-[11px] text-slate-400">
                Sin elementos.
              </li>
            )}
          </ul>
        </section>
      ))}
    </div>
  )
}
