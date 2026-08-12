import { useCallback, useEffect, useState } from 'react'
import { rucIntegrationApi } from '../../api/ruc-integration-api'
import { Button } from '../common/Button'
import { LoadingSkeleton } from '../common/LoadingSkeleton'
import type { BusinessPartner } from '../../types/business-partners'
import type {
  ApplyRucDataRequest,
  BusinessPartnerRucVerification,
  RucLookupResponse,
} from '../../types/ruc-integration'
import { ApplyRucDataDialog } from './ApplyRucDataDialog'
import { DataFreshnessIndicator } from './DataFreshnessIndicator'
import { DataSourceBadge } from './DataSourceBadge'
import { RucLookupResultCard } from './RucLookupResultCard'

interface Props {
  partner: BusinessPartner
  onPartnerUpdated?: () => void
}

export function BusinessPartnerRucVerificationPanel({ partner, onPartnerUpdated }: Props) {
  const [verifications, setVerifications] = useState<BusinessPartnerRucVerification[]>([])
  const [latestLookup, setLatestLookup] = useState<RucLookupResponse | null>(null)
  const [verificationId, setVerificationId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Dialog state
  const [showApplyDialog, setShowApplyDialog] = useState(false)
  const [applying, setApplying] = useState(false)
  const [applyError, setApplyError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const items = await rucIntegrationApi.listPartnerVerifications(partner.id)
      setVerifications(items)
      if (partner.tax_id && partner.tax_id.length === 11) {
        const lookup = await rucIntegrationApi.lookupRuc({
          ruc: partner.tax_id,
          partner_id: partner.id,
          include_annexes: true,
        })
        setLatestLookup(lookup)
      }
    } catch {
      // Keep empty if none
    } finally {
      setLoading(false)
    }
  }, [partner.id, partner.tax_id])

  useEffect(() => {
    void load()
  }, [load])

  const handleVerify = async (useAuthorizedProvider = false) => {
    if (!partner.tax_id) return
    setVerifying(true)
    setError(null)
    try {
      const verification = await rucIntegrationApi.verifyPartnerRuc(
        partner.id,
        useAuthorizedProvider,
      )
      const lookup = await rucIntegrationApi.lookupRuc({
        ruc: partner.tax_id,
        partner_id: partner.id,
        include_annexes: true,
        use_authorized_provider: useAuthorizedProvider,
      })
      setLatestLookup(lookup)
      setVerificationId(verification.verification_id)
      const items = await rucIntegrationApi.listPartnerVerifications(partner.id)
      setVerifications(items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al consultar el RUC')
    } finally {
      setVerifying(false)
    }
  }

  const handleApplyData = async (req: ApplyRucDataRequest) => {
    setApplying(true)
    setApplyError(null)
    try {
      await rucIntegrationApi.applyRucDataToPartner(partner.id, req)
      setShowApplyDialog(false)
      setVerificationId(null)
      if (onPartnerUpdated) onPartnerUpdated()
      void load()
    } catch (err) {
      setApplyError(err instanceof Error ? err.message : 'Error al aplicar datos al socio')
    } finally {
      setApplying(false)
    }
  }

  if (loading) return <LoadingSkeleton rows={6} />

  const rucVal = partner.tax_id || ''
  const is11Digits = rucVal.length === 11

  return (
    <div className="space-y-6 text-xs">
      {/* Header Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 block text-[10px]">
            RUC del Socio
          </span>
          <span className="font-mono text-lg font-bold text-slate-800">
            {rucVal || 'Sin RUC registrado'}
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {is11Digits && (
            <>
              <Button
                type="button"
                variant="secondary"
                onClick={() => handleVerify(false)}
                isLoading={verifying}
                loadingLabel="Consultando..."
              >
                Consultar Padrón
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => handleVerify(true)}
                isLoading={verifying}
                loadingLabel="Consultando..."
              >
                Consultar Proveedor Autorizado
              </Button>
            </>
          )}
          {latestLookup && verificationId && (
            <Button
              type="button"
              onClick={() => setShowApplyDialog(true)}
            >
              Aplicar Datos Campo por Campo
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-red-700">
          {error}
        </div>
      )}

      {/* Latest Lookup Card */}
      {latestLookup && (
        <RucLookupResultCard
          result={latestLookup}
          onApplyDataToPartner={verificationId ? () => setShowApplyDialog(true) : undefined}
        />
      )}

      {/* Verifications History Timeline */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Historial de Verificaciones de RUC ({verifications.length})
        </h4>

        {verifications.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-slate-400">
            No se han registrado verificaciones previas para este socio.
          </div>
        ) : (
          <div className="space-y-2">
            {verifications.map((v) => (
              <div
                key={v.id}
                className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-3.5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-800">{v.ruc}</span>
                    <DataSourceBadge source={v.source} label={v.source_label} size="sm" />
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                        v.verification_status === 'VALIDATED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {v.verification_status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                    <span>Fecha: {new Date(v.verification_date).toLocaleDateString('es-PE')}</span>
                    <span>· {v.created_by_name}</span>
                    {v.dataset_version && <span>· v{v.dataset_version}</span>}
                  </div>
                </div>

                <DataFreshnessIndicator
                  freshnessStatus={v.freshness_status}
                  sourceDate={v.verification_date}
                  ageInDays={v.age_in_days}
                  showAbsoluteDate={false}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Apply Dialog */}
      {latestLookup && verificationId && (
        <ApplyRucDataDialog
          isOpen={showApplyDialog}
          isSubmitting={applying}
          lookupData={latestLookup}
          verificationId={verificationId}
          currentPartnerName={partner.legal_name}
          error={applyError}
          onApply={handleApplyData}
          onClose={() => setShowApplyDialog(false)}
        />
      )}
    </div>
  )
}
