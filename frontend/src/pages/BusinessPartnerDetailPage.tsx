import { useCallback, useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { businessPartnersApi } from '../api/business-partners-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import type {
  BusinessPartner,
  BusinessPartnerAddress,
  BusinessPartnerContact,
  BusinessPartnerDocument,
  BusinessPartnerEvaluation,
} from '../types/business-partners'
import { getErrorMessage } from '../utils/errors'

import { BusinessPartnerRucVerificationPanel } from '../components/ruc/BusinessPartnerRucVerificationPanel'

type PartnerTab =
  | 'summary'
  | 'roles'
  | 'addresses'
  | 'contacts'
  | 'evaluations'
  | 'documents'
  | 'ruc_verification'

export function BusinessPartnerDetailPage() {
  const { partnerId } = useParams<{ partnerId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab: PartnerTab = (searchParams.get('tab') as PartnerTab) || 'summary'

  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [partner, setPartner] = useState<BusinessPartner | null>(null)
  const [addresses, setAddresses] = useState<BusinessPartnerAddress[]>([])
  const [contacts, setContacts] = useState<BusinessPartnerContact[]>([])
  const [evaluations, setEvaluations] = useState<BusinessPartnerEvaluation[]>([])
  const [documents, setDocuments] = useState<BusinessPartnerDocument[]>([])

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadPartner = useCallback(async () => {
    if (!partnerId) return
    setIsLoading(true)
    setError(null)
    try {
      const p = await businessPartnersApi.get(partnerId)
      setPartner(p)
      const related = await Promise.allSettled([
        businessPartnersApi.listAddresses(partnerId),
        businessPartnersApi.listContacts(partnerId),
        businessPartnersApi.listEvaluations(partnerId),
        businessPartnersApi.listDocuments(partnerId),
      ])
      setAddresses(related[0].status === 'fulfilled' ? related[0].value : [])
      setContacts(related[1].status === 'fulfilled' ? related[1].value : [])
      setEvaluations(related[2].status === 'fulfilled' ? related[2].value : [])
      setDocuments(related[3].status === 'fulfilled' ? related[3].value : [])
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void loadPartner()
  }, [loadPartner])

  const setTab = (tab: PartnerTab) => {
    setSearchParams({ tab })
  }

  const handleBlock = async () => {
    if (!partnerId) return
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await businessPartnersApi.block(partnerId, 'Bloqueo preventivo por cumplimiento')
      })
      if (!executed) return
      await loadPartner()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  if (!partnerId) return null

  return (
    <div className="page">
      {partner && (
        <PageHeader
          eyebrow={`Código: ${partner.code} · RUC/ID: ${partner.tax_id}`}
          title={partner.legal_name}
          description={partner.trade_name ? `Nombre comercial: ${partner.trade_name}` : 'Sin nombre comercial.'}
          actions={
            <div className="flex items-center gap-2">
              <StatusBadge value={partner.status.toLowerCase()}>{partner.status}</StatusBadge>
              {partner.status === 'ACTIVE' && partner.capabilities.can_block && (
                <Button size="small" variant="secondary" onClick={() => void handleBlock()} isLoading={isSaving}>
                  Bloquear Socio (Step-Up)
                </Button>
              )}
            </div>
          }
        />
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando expediente del socio de negocio…</p>
        </div>
      ) : partner ? (
        <section className="panel operations-section space-y-4">
          <div className="tabs border-b border-slate-200 pb-2 flex items-center gap-2">
            {[
              { id: 'summary', label: 'Resumen' },
              { id: 'roles', label: 'Roles Asignados' },
              { id: 'addresses', label: 'Direcciones' },
              { id: 'contacts', label: 'Contactos' },
              { id: 'evaluations', label: 'Evaluaciones' },
              { id: 'documents', label: 'Documentos Metadatos' },
              { id: 'ruc_verification', label: 'Verificación RUC' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  activeTab === t.id
                    ? 'bg-blue-700 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
                onClick={() => setTab(t.id as PartnerTab)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="pt-2 text-xs">
            {activeTab === 'summary' && (
              <div className="grid grid-cols-2 gap-4 text-slate-700">
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Identificador Fiscal:</span>
                  <span className="font-mono font-bold text-slate-900">{partner.tax_id} ({partner.tax_id_status})</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Nivel de Riesgo:</span>
                  <span className="font-bold text-slate-900">{partner.risk_level}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Estado Cumplimiento:</span>
                  <span className="font-bold text-slate-900">{partner.compliance_status}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">País Origen:</span>
                  <span className="font-bold text-slate-900">{partner.country_code}</span>
                </div>
              </div>
            )}

            {activeTab === 'roles' && (
              <div className="flex gap-2">
                {partner.roles.map((r) => (
                  <span key={r} className="px-2.5 py-1 bg-blue-100 text-blue-900 rounded-md font-bold text-[11px]">
                    {r}
                  </span>
                ))}
              </div>
            )}

            {activeTab === 'addresses' && (
              <div className="space-y-2">
                {addresses.map((a) => (
                  <div key={a.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="font-bold text-slate-900">{a.address_type}</span>: {a.street}, {a.district}, {a.department}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'contacts' && (
              <div className="space-y-2">
                {contacts.map((c) => (
                  <div key={c.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="font-bold text-slate-900">{c.full_name}</span> ({c.role_title}) - Correo: {c.email}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'evaluations' && (
              <div className="space-y-2">
                {evaluations.map((e) => (
                  <div key={e.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex justify-between">
                    <span>Periodo: {e.period}</span>
                    <span className="font-bold font-mono text-blue-700">Puntaje: {e.score} ({e.status})</span>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'documents' && (
              <div className="space-y-2">
                {documents.map((d) => (
                  <div key={d.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex justify-between">
                    <span>{d.doc_type} N° {d.doc_number}</span>
                    <span className={d.is_expired ? 'text-rose-600 font-bold' : 'text-emerald-700 font-bold'}>
                      {d.is_expired ? 'Vencido' : 'Vigente'} ({d.status})
                    </span>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'ruc_verification' && (
              <BusinessPartnerRucVerificationPanel
                partner={partner}
                onPartnerUpdated={loadPartner}
              />
            )}
          </div>
        </section>
      ) : null}
    </div>
  )
}
