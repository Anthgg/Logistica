import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { ShipmentHeader } from '../components/shipments/ShipmentHeader'
import { ShipmentSummary } from '../components/shipments/ShipmentSummary'
import { ShipmentInformationCard } from '../components/shipments/ShipmentInformationCard'
import { ShipmentTimeline } from '../components/shipments/ShipmentTimeline'
import { ChangeShipmentStatusDialog } from '../components/shipments/ChangeShipmentStatusDialog'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useAuth } from '../hooks/useAuth'
import { useTranslations } from '../hooks/useTranslations'
import { ApiRequestError } from '../types/api'
import type { Shipment, ShipmentEvent, ShipmentStatus } from '../types/operations'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'
import { SHIPMENT_TRANSITIONS } from '../features/shipments/shipmentTransitions'
import { getShipmentStatusLabel } from '../features/shipments/shipmentStatusLabels'

export function ShipmentDetailPage() {
  const { shipmentId = '' } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { catalogVersion, language } = useTranslations()
  const canChangeStatus = user ? permissionsFor(user.role).changeShipmentStatus : false
  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [shipment, setShipment] = useState<Shipment | null>(null)
  const [timeline, setTimeline] = useState<ShipmentEvent[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modalError, setModalError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    void catalogVersion
    if (!shipmentId) return
    setIsLoading(true)
    setError(null)
    try {
      const [detail, events] = await Promise.all([
        operationsApi.shipments.get(shipmentId),
        operationsApi.shipments.timeline(shipmentId),
      ])
      setShipment(detail)
      setTimeline(events)
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [catalogVersion, shipmentId])

  useEffect(() => { void load() }, [load])

  const currentStatus = shipment?.status
  const allowedNextStatuses = currentStatus ? SHIPMENT_TRANSITIONS[currentStatus] || [] : []

  const handleOpenModal = () => {
    setModalError(null)
    setSuccessMessage(null)
    setIsOpen(true)
  }

  const changeStatus = async ({
    status,
    location,
    description,
  }: {
    status: ShipmentStatus
    location: string
    description: string
  }) => {
    if (!currentStatus || !allowedNextStatuses.includes(status)) {
      setModalError('Transición de estado no permitida.')
      return
    }

    setIsSaving(true)
    setModalError(null)
    try {
      const executed = await guardSensitiveAction(async () => {
        await operationsApi.shipments.status(shipmentId, {
          status,
          location: location.trim() || undefined,
          description: description.trim() || undefined,
        })
      })
      if (!executed) return

      setIsOpen(false)
      const label = getShipmentStatusLabel(status, language)
      setSuccessMessage(`Estado actualizado. El envío ahora figura como "${label}".`)
      await load()
    } catch (caught: unknown) {
      if (caught instanceof ApiRequestError) {
        if (caught.status === 401) {
          navigate('/login', {
            replace: true,
            state: {
              errorMessage:
                'Tu sesión ha expirado o no es válida. Por favor, inicia sesión nuevamente.',
            },
          })
          return
        }
        if (caught.status === 403) {
          setModalError(
            'No tienes permisos para cambiar el estado de este envío.',
          )
          return
        }
        if (caught.status === 409) {
          if (caught.code === 'SHIPMENT_STATUS_UNCHANGED') {
            setModalError('El envío ya tiene el estado seleccionado.')
          } else {
            setModalError(
              'El estado del envío cambió o la transición ya no está permitida. Actualizaremos la información.',
            )
          }
          await load()
          return
        }
      }
      setModalError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Alerta de Éxito */}
      {successMessage && (
        <Alert variant="success" onDismiss={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Alerta de Error General */}
      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <LoadingSkeleton label="Cargando detalle del envío y trazabilidad…" rows={8} />
      ) : shipment ? (
        <>
          {/* Header principal */}
          <ShipmentHeader
            trackingCode={shipment.tracking_code}
            status={shipment.status}
            statusLabel={shipment.status_label}
            canChangeStatus={canChangeStatus}
            hasAvailableTransitions={true}
            onChangeStatus={handleOpenModal}
          />

          {/* Resumen operativo superior */}
          <ShipmentSummary shipment={shipment} language={language} />

          {/* Área Principal de 2 Columnas (Info Izquierda / Timeline Derecha) */}
          <div className="grid grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,0.9fr)]">
            <ShipmentInformationCard shipment={shipment} language={language} />
            <ShipmentTimeline events={timeline} />
          </div>

          {/* Modal Cambiar Estado */}
          {isOpen && (
            <ChangeShipmentStatusDialog
              isOpen={isOpen}
              currentStatus={shipment.status}
              isSaving={isSaving}
              error={modalError}
              onClose={() => {
                if (!isSaving) setIsOpen(false)
              }}
              onSubmit={(data) => void changeStatus(data)}
            />
          )}
        </>
      ) : null}
    </div>
  )
}
