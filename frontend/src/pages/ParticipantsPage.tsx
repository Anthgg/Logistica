import { useCallback, useEffect, useState } from 'react'
import { researchApi } from '../api/research-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { Input } from '../components/common/Input'
import {
  OperationsTable,
  type TableColumn,
} from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useAuth } from '../hooks/useAuth'
import type { Participant } from '../types/research'
import { formatDateTime } from '../utils/date'
import { getErrorMessage } from '../utils/errors'

export function ParticipantsPage() {
  const { user } = useAuth()
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const [participants, setParticipants] = useState<Participant[]>([])
  const [linkedUserId, setLinkedUserId] = useState(user?.id ?? '')
  const [editing, setEditing] = useState<Participant | null>(null)
  const [isActive, setIsActive] = useState(true)
  const [withdrawing, setWithdrawing] = useState<Participant | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      setParticipants((await researchApi.participants()).items)
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const openCreate = () => {
    setEditing(null)
    setLinkedUserId(user?.id ?? '')
    setIsActive(true)
    setIsOpen(true)
  }

  const openEdit = (participant: Participant) => {
    setEditing(participant)
    setLinkedUserId(participant.linked_user_id ?? '')
    setIsActive(participant.is_active)
    setIsOpen(true)
  }

  const save = async () => {
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        if (editing) {
          await researchApi.updateParticipant(editing.id, {
            linked_user_id: linkedUserId || null,
            is_active: isActive,
          })
        } else {
          await researchApi.createParticipant(linkedUserId)
        }
      })
      if (!executed) return
      setIsOpen(false)
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  const withdraw = async () => {
    if (!withdrawing) return
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await researchApi.withdrawParticipant(withdrawing.id)
      })
      if (!executed) return
      setWithdrawing(null)
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  const columns: TableColumn<Participant>[] = [
    {
      key: 'code',
      label: 'Código',
      render: (row) => <strong>{row.participant_code}</strong>,
    },
    {
      key: 'user',
      label: 'Usuario vinculado',
      render: (row) => row.linked_user_id ?? 'No vinculado',
    },
    {
      key: 'date',
      label: 'Inscripción',
      render: (row) => formatDateTime(row.enrollment_date),
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <StatusBadge value={row.is_active ? 'active' : 'withdrawn'}>
          {row.is_active ? 'Activo' : 'Retirado'}
        </StatusBadge>
      ),
    },
    {
      key: 'action',
      label: '',
      align: 'right',
      render: (row) => (
        <div className="table-actions">
          <Button size="small" variant="ghost" onClick={() => openEdit(row)}>
            Editar
          </Button>
          {row.is_active && (
            <Button
              size="small"
              variant="ghost"
              onClick={() => setWithdrawing(row)}
            >
              Retirar
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="page">
      <PageHeader
        eyebrow="Muestra del estudio"
        title="Participantes"
        description="Registro pseudonimizado y estado de participación."
        actions={<Button onClick={openCreate}>Nuevo participante</Button>}
      />
      {error && <Alert variant="error">{error}</Alert>}
      <section className="panel operations-section">
        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando participantes…</p>
          </div>
        ) : (
          <OperationsTable
            rows={participants}
            columns={columns}
            getRowKey={(row) => row.id}
          />
        )}
      </section>
      <ResourceDialog
        isOpen={isOpen}
        title={editing ? 'Editar participante' : 'Nuevo participante'}
        description={
          editing
            ? 'Actualiza el vínculo y el estado del participante.'
            : 'Por defecto se vincula con el usuario administrador actual.'
        }
        submitLabel={editing ? 'Guardar cambios' : 'Crear participante'}
        isSubmitting={isSaving}
        onClose={() => setIsOpen(false)}
        onSubmit={() => void save()}
      >
        <Input
          label="ID del usuario vinculado"
          value={linkedUserId}
          onChange={(event) => setLinkedUserId(event.target.value)}
          placeholder="UUID del usuario"
        />
        {editing && (
          <label className="consent-check">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(event) => setIsActive(event.target.checked)}
            />
            <span>Participante activo</span>
          </label>
        )}
      </ResourceDialog>
      <ConfirmDialog
        isOpen={withdrawing !== null}
        title="¿Retirar participante?"
        description={`Se registrará el retiro de ${
          withdrawing?.participant_code ?? 'este participante'
        }.`}
        confirmLabel="Confirmar retiro"
        isLoading={isSaving}
        onCancel={() => setWithdrawing(null)}
        onConfirm={() => void withdraw()}
      />
    </div>
  )
}
