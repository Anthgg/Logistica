import { useState } from 'react'
import { purchaseRequisitionsApi } from '../../api/purchase-requisitions-api'
import { Button } from '../common/Button'
import type { PurchaseRequisitionComment } from '../../types/purchase-requisitions'

interface CommentsProps {
  requisitionId: string
  comments: PurchaseRequisitionComment[]
  onCommentAdded?: () => void
  canComment?: boolean
}

export function PurchaseRequisitionCommentsPanel({
  requisitionId,
  comments,
  onCommentAdded,
  canComment = true,
}: CommentsProps) {
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim() || submitting) return
    setSubmitting(true)
    try {
      await purchaseRequisitionsApi.addComment(requisitionId, content.trim())
      setContent('')
      if (onCommentAdded) onCommentAdded()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al añadir comentario')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4 text-xs">
      <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
        Hilo de Comentarios y Observaciones ({comments.length})
      </h4>

      {canComment && (
        <form onSubmit={handleAdd} className="space-y-2">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={2}
            required
            placeholder="Escribe un comentario u observación sobre la solicitud..."
            className="w-full resize-none rounded-xl border border-slate-300 px-3 py-2 text-xs"
          />
          <div className="flex justify-end">
            <Button size="small" type="submit" isLoading={submitting} loadingLabel="Publicando...">
              Publicar Comentario
            </Button>
          </div>
        </form>
      )}

      <div className="space-y-2 pt-2">
        {comments.map((c) => (
          <div key={c.id} className="rounded-xl border border-slate-200 bg-white p-3.5 space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-bold text-slate-800">{c.user_name}</span>
              <span className="text-slate-400 font-mono">{new Date(c.created_at).toLocaleString('es-PE')}</span>
            </div>
            <p className="text-slate-700">{c.content}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

interface DocumentProps {
  requisitionCode: string
  activeRevisionNumber: number
}

export function PurchaseRequisitionDocumentPanel({
  requisitionCode,
  activeRevisionNumber,
}: DocumentProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4 text-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
            Documento de Solicitud de Compra (REQ)
          </span>
          <h3 className="text-sm font-bold text-slate-800">
            {requisitionCode} — Revisión v{activeRevisionNumber}
          </h3>
        </div>

        <div className="flex gap-2">
          <Button size="small" variant="secondary" onClick={() => alert('Generando previsualización autorizada...')}>
            Vista Previa (NO OFICIAL)
          </Button>
          <Button size="small" onClick={() => alert('Iniciando descarga oficial de REQ...')}>
            Descargar Documento
          </Button>
        </div>
      </div>

      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-2 text-slate-600">
        <p>
          El documento REQ es emitido por el backend con marca de agua inmutable. No asigna nuevos correlativos al previsualizar.
        </p>
      </div>
    </div>
  )
}
