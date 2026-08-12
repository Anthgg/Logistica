import { SectionPanel, KeyValueGrid, EmptyPanel, ErrorPanel, SkeletonRows } from './ui/Primitives'
import type { UnloadingExpectedLoad } from '../types/inbound-docks'

export function UnloadingExpectedLoadPanel({
  load,
  loading,
  error,
}: {
  load: UnloadingExpectedLoad | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel
        title="Datos esperados"
        description="Información esperada. La cantidad recibida se validará en la Fase 039."
      >
        <SkeletonRows rows={4} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel
        title="Datos esperados"
        description="Información esperada. La cantidad recibida se validará en la Fase 039."
      >
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!load) {
    return (
      <SectionPanel
        title="Datos esperados"
        description="Información esperada. La cantidad recibida se validará en la Fase 039."
      >
        <EmptyPanel title="Sin datos esperados" description="El backend no devolvió información esperada." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Datos esperados"
      description="Información esperada. La cantidad recibida se validará en la Fase 039."
    >
      <KeyValueGrid
        items={[
          { label: 'OC', value: load.po_codes?.length ? load.po_codes.join(', ') : '—' },
          { label: 'Líneas esperadas', value: load.expected_lines_count ?? '—' },
          { label: 'Pallets', value: load.pallets ?? '—' },
          { label: 'Bultos', value: load.packages ?? '—' },
          { label: 'Peso', value: load.weight ?? '—' },
          { label: 'Precinto', value: load.seal_number ?? '—', mono: true },
          { label: 'Condiciones', value: load.conditions ?? '—' },
          { label: 'Requisitos especiales', value: load.special_requirements?.length ? load.special_requirements.join(', ') : '—' },
          { label: 'Documentos', value: load.documents?.length ? `${load.documents.length} adjunto(s)` : '—' },
        ]}
      />
      {load.gate_warnings && load.gate_warnings.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-amber-700">
          <p className="text-[11px] font-semibold">Advertencias de garita</p>
          <ul className="list-disc pl-4 text-[11px]">
            {load.gate_warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="mt-3 rounded-lg border border-indigo-200 bg-indigo-50/40 p-2 text-[11px] text-indigo-700">
        Información esperada. La cantidad recibida se validará en la Fase 039.
      </p>
    </SectionPanel>
  )
}
