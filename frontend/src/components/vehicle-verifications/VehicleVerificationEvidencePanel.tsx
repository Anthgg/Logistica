import type { VehicleVerificationEvidence } from '../../types/vehicle-verifications'

interface Props {
  evidences: VehicleVerificationEvidence[]
  verificationId?: string
}

export function VehicleVerificationEvidencePanel({ evidences }: Props) {
  return (
    <div className="space-y-3 text-xs">
      <div className="flex items-center justify-between">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[11px]">
          Evidencias y Documentos de Respaldo ({evidences?.length || 0})
        </h4>
        <span className="text-[10px] text-slate-400 font-mono">
          La administración central de archivos se completa en la Fase 030.
        </span>
      </div>

      {!evidences || evidences.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-slate-400 text-[11px]">
          Sin evidencias adjuntas registradas.
        </div>
      ) : (
        <div className="space-y-2">
          {evidences.map((e) => (
            <div key={e.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-800">{e.file_name}</span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600">
                    Hash: {e.partial_hash}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400">
                  Subido por {e.uploaded_by_user_name} el {new Date(e.created_at).toLocaleString('es-PE')}
                </div>
              </div>

              <span className="font-mono text-[11px] text-slate-500 font-bold">
                {e.evidence_type}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
