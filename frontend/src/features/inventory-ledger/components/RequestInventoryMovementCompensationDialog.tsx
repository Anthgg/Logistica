import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { inventoryMovementCompensationsApi } from '../api/inventoryMovementCompensationsApi'
import type { InventoryMovement } from '../types/inventory-ledger'

interface Props {
  movement: InventoryMovement
  onClose: () => void
  onSuccess: () => void
}

export function RequestInventoryMovementCompensationDialog({ movement, onClose, onSuccess }: Props) {
  const [reasonCode, setReasonCode] = useState('')
  const [description, setDescription] = useState('')
  const [compensationType, setCompensationType] = useState<'FULL' | 'PARTIAL'>('FULL')
  const [confirmed, setConfirmed] = useState(false)
  const [createdCompensationId, setCreatedCompensationId] = useState<string | null>(null)

  const submit = useMutation(
    () =>
      inventoryMovementCompensationsApi.createInventoryCompensationRequest(movement.movement_id, {
        compensation_type: compensationType,
        reason_code: reasonCode,
        description,
        affected_lines:
          compensationType === 'PARTIAL'
            ? movement.lines.map((l) => ({
                movement_line_id: l.line_id,
                quantity: l.quantity,
                reason: null,
              }))
            : [],
        evidence_file_ids: [],
      }),
    {
      onSuccess: (result) => setCreatedCompensationId(result?.compensation_id ?? null),
    },
  )

  const submitForReview = useMutation(
    (compensationId: string) => inventoryMovementCompensationsApi.submitInventoryCompensationRequest({ compensation_id: compensationId }),
    {
      onSuccess: () => onSuccess(),
    },
  )

  const canSubmit = reasonCode.trim().length > 0 && description.trim().length > 0 && confirmed

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto space-y-4">
        <header className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-medium">Solicitar compensación</h2>
          <Button variant="secondary" onClick={onClose}>Cerrar</Button>
        </header>

        <div className="p-4 space-y-4">
          <Alert variant="warning">
            Una compensación no elimina ni modifica el movimiento original. Se publicará un nuevo MOV compensatorio.
          </Alert>

          <section className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700">MOV original</h3>
            <div className="p-3 bg-gray-50 rounded text-sm space-y-1">
              <div>
                <span className="text-gray-500">Código:</span>{' '}
                <span className="font-mono">{movement.movement_code}</span>
              </div>
              <div>
                <span className="text-gray-500">Tipo:</span> {movement.movement_type}
              </div>
              <div>
                <span className="text-gray-500">Líneas:</span> {movement.total_lines}
              </div>
              <div>
                <span className="text-gray-500">Razón original:</span> {movement.reason}
              </div>
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-medium text-gray-700">Detalles de la solicitud</h3>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Tipo de compensación
              </label>
              <select
                value={compensationType}
                onChange={(e) => setCompensationType(e.target.value as 'FULL' | 'PARTIAL')}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              >
                <option value="FULL">Total</option>
                <option value="PARTIAL">Parcial</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Código de motivo *
              </label>
              <input
                type="text"
                value={reasonCode}
                onChange={(e) => setReasonCode(e.target.value)}
                placeholder="Ej: POSTING_ERROR, INTEGRITY_VIOLATION"
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Descripción *
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
          </section>

          <Alert variant="info">
            Esta acción requiere step-up. El backend calculará la inversión; no se puede cambiar producto, destino libre ni unidad.
          </Alert>

          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="rounded mt-1"
            />
            <span>
              Confirmo que entiendo que el movimiento original permanecerá en el libro y que se publicará un nuevo MOV compensatorio.
            </span>
          </label>

          {submit.error && (
            <Alert variant="error">{submit.error}</Alert>
          )}
        </div>

        <footer className="p-4 border-t flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          {!createdCompensationId ? (
            <Button
              onClick={() => submit.mutate(undefined)}
              disabled={!canSubmit || submit.isPending}
            >
              {submit.isPending ? 'Creando...' : 'Crear solicitud'}
            </Button>
          ) : (
            <Button
              onClick={() => submitForReview.mutate(createdCompensationId)}
              disabled={submitForReview.isPending}
            >
              {submitForReview.isPending ? 'Enviando...' : 'Enviar a revisión'}
            </Button>
          )}
        </footer>
      </div>
    </div>
  )
}
