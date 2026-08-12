import type { ReceptionDifferenceItem } from '../../types/reception-differences'

interface MissingDocumentDifferencePanelProps {
  item: ReceptionDifferenceItem
}

const DOC_STATUS_LABELS: Record<string, string> = {
  NOT_PRESENTED: 'No presentado',
  NOT_UPLOADED: 'No cargado',
  ILLEGIBLE: 'Ilegible',
  DOES_NOT_MATCH: 'No coincide',
  EXPIRED: 'Vencido',
  INVALID_FORMAT: 'Formato inválido',
  REQUIRES_REVIEW: 'Requiere revisión',
}

export function MissingDocumentDifferencePanel({ item }: MissingDocumentDifferencePanelProps) {
  const doc = item.document_detail

  return (
    <div className="space-y-3 text-xs">
      <div className="grid grid-cols-2 gap-3">
        {doc?.document_type && <InfoCell label="Tipo requerido" value={doc.document_type} />}
        {doc?.requirement_source && <InfoCell label="Fuente del requisito" value={doc.requirement_source} />}
        {doc?.expected_document && <InfoCell label="Documento esperado" value={doc.expected_document} />}
        {doc?.presentation_status && (
          <InfoCell
            label="Estado de presentación"
            value={DOC_STATUS_LABELS[doc.presentation_status] ?? doc.presentation_status}
          />
        )}
        {doc?.issuer && <InfoCell label="Emisor" value={doc.issuer} />}
        {doc?.reference && <InfoCell label="Referencia" value={doc.reference} />}
      </div>

      <InfoCell label="Descripción" value={item.description ?? '—'} />
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="text-slate-800">{value}</p>
    </div>
  )
}
