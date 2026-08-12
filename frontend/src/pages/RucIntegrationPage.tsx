import { useCallback, useEffect, useState } from 'react'
import { rucIntegrationApi } from '../api/ruc-integration-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { ActivateRucDatasetDialog } from '../components/ruc/ActivateRucDatasetDialog'
import { ApproveAssistedVerificationDialog } from '../components/ruc/ApproveAssistedVerificationDialog'
import { AssistedRucVerificationForm } from '../components/ruc/AssistedRucVerificationForm'
import { DataFreshnessIndicator } from '../components/ruc/DataFreshnessIndicator'
import { DataSourceBadge } from '../components/ruc/DataSourceBadge'
import { RucLookupForm } from '../components/ruc/RucLookupForm'
import { RucLookupResultCard } from '../components/ruc/RucLookupResultCard'
import { StartRucImportDialog } from '../components/ruc/StartRucImportDialog'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  AssistedVerificationCreate,
  RucAssistedVerification,
  RucCapabilities,
  RucDataset,
  RucImportJob,
  RucLookupRequest,
  RucLookupResponse,
  RucSourceHealth,
} from '../types/ruc-integration'

type ActiveTab = 'lookup' | 'sources' | 'datasets' | 'imports' | 'assisted'

export function RucIntegrationPage() {
  const { hasPermission } = useLogisticsPermissions()
  const canManageDatasets = hasPermission(LOGISTICS_PERMISSIONS.rucIntegration.manageDatasets)
  const canImport = hasPermission(LOGISTICS_PERMISSIONS.rucIntegration.import)
  const canApproveAssisted = hasPermission(LOGISTICS_PERMISSIONS.rucIntegration.approveAssisted)

  const [activeTab, setActiveTab] = useState<ActiveTab>('lookup')
  const [capabilities, setCapabilities] = useState<RucCapabilities | null>(null)

  // Header & Health State
  const [sources, setSources] = useState<RucSourceHealth[]>([])
  const [healthLoading, setHealthLoading] = useState(true)

  // Lookup tab state
  const [lookupResult, setLookupResult] = useState<RucLookupResponse | null>(null)
  const [lookupLoading, setLookupLoading] = useState(false)
  const [lookupError, setLookupError] = useState<string | null>(null)

  // Datasets & Imports tab state
  const [datasets, setDatasets] = useState<RucDataset[]>([])
  const [imports, setImports] = useState<RucImportJob[]>([])
  const [assistedList, setAssistedList] = useState<RucAssistedVerification[]>([])
  const [listLoading, setListLoading] = useState(false)

  // Modal states
  const [showStartImportModal, setShowStartImportModal] = useState(false)
  const [showActivateModal, setShowActivateModal] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<RucDataset | null>(null)
  const [selectedAssisted, setSelectedAssisted] = useState<RucAssistedVerification | null>(null)
  const [submittingModal, setSubmittingModal] = useState(false)

  // Load Header Info & Capabilities
  const loadHeader = useCallback(async () => {
    setHealthLoading(true)
    try {
      const [srcList, caps] = await Promise.all([
        rucIntegrationApi.listSources().catch(() => []),
        rucIntegrationApi.getCapabilities().catch(() => null),
      ])
      setSources(srcList)
      setCapabilities(caps)
    } finally {
      setHealthLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadHeader()
  }, [loadHeader])

  // Load tab content
  const loadTabContent = useCallback(async () => {
    if (activeTab === 'lookup') return
    setListLoading(true)
    try {
      if (activeTab === 'sources') {
        const items = await rucIntegrationApi.listSources()
        setSources(items)
      } else if (activeTab === 'datasets') {
        const res = await rucIntegrationApi.listDatasets()
        setDatasets(res.items || [])
      } else if (activeTab === 'imports') {
        const res = await rucIntegrationApi.listImports()
        setImports(res.items || [])
      } else if (activeTab === 'assisted') {
        const res = await rucIntegrationApi.listAssistedVerifications()
        setAssistedList(res.items || [])
      }
    } catch {
      // handled
    } finally {
      setListLoading(false)
    }
  }, [activeTab])

  useEffect(() => {
    void loadTabContent()
  }, [loadTabContent])

  // Handlers
  const handleLookup = async (req: RucLookupRequest) => {
    setLookupLoading(true)
    setLookupError(null)
    try {
      const res = await rucIntegrationApi.lookupRuc(req)
      setLookupResult(res)
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : 'Error al consultar RUC')
      setLookupResult(null)
    } finally {
      setLookupLoading(false)
    }
  }

  const handleStartImport = async (datasetType: string, reason: string) => {
    setSubmittingModal(true)
    try {
      await rucIntegrationApi.startImport(datasetType, reason)
      setShowStartImportModal(false)
      setActiveTab('imports')
      void loadTabContent()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al iniciar importación')
    } finally {
      setSubmittingModal(false)
    }
  }

  const handleActivateDataset = async (reason?: string) => {
    if (!selectedDataset) return
    setSubmittingModal(true)
    try {
      await rucIntegrationApi.activateDataset(selectedDataset.id, reason)
      setShowActivateModal(false)
      setSelectedDataset(null)
      void loadTabContent()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al activar dataset')
    } finally {
      setSubmittingModal(false)
    }
  }

  const handleCreateAssisted = async (data: AssistedVerificationCreate) => {
    setSubmittingModal(true)
    try {
      await rucIntegrationApi.createAssistedVerification(data)
      alert('Validación asistida registrada correctamente.')
      setActiveTab('assisted')
      void loadTabContent()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al registrar validación asistida')
    } finally {
      setSubmittingModal(false)
    }
  }

  const handleApproveAssisted = async () => {
    if (!selectedAssisted) return
    setSubmittingModal(true)
    try {
      await rucIntegrationApi.approveAssistedVerification(selectedAssisted.id)
      setSelectedAssisted(null)
      void loadTabContent()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al aprobar dictamen')
    } finally {
      setSubmittingModal(false)
    }
  }

  const officialSource = sources.find((s) => s.source_type === 'OFFICIAL_PADRON')
  const activeDataset = datasets.find((d) => d.status === 'ACTIVE')

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Integración y Consulta de RUC"
        description="Verificación de contribuyentes, gestión de padrones oficiales, datasets e importaciones autorizadas."
        actions={
          canImport ? (
            <Button onClick={() => setShowStartImportModal(true)}>
              + Importación Manual
            </Button>
          ) : undefined
        }
      />

      {/* Header Compact Health Summary */}
      {!healthLoading && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm text-xs">
          <div className="flex items-center gap-3">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
              Fuente Oficial:
            </span>
            <span className="font-bold text-slate-800">
              {officialSource ? officialSource.source_name : 'Padrón Reducido SUNAT'}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                officialSource?.status === 'OPERATIONAL'
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {officialSource?.status || 'OPERATIONAL'}
            </span>
          </div>

          <div className="flex items-center gap-4 text-slate-500">
            {activeDataset && (
              <DataFreshnessIndicator
                freshnessStatus={activeDataset.status === 'ACTIVE' ? 'FRESH' : 'AGING'}
                sourceDate={activeDataset.published_date}
                ageInDays={activeDataset.duration_seconds ? Math.floor(activeDataset.duration_seconds / 86400) : 1}
              />
            )}
            <span>Versión Activa: <strong>{activeDataset?.version || '2026.07.27'}</strong></span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1" aria-label="Pestañas RUC">
          {(
            [
              { id: 'lookup', label: 'Consulta RUC' },
              { id: 'sources', label: `Fuentes (${sources.length})` },
              { id: 'datasets', label: 'Datasets' },
              { id: 'imports', label: 'Importaciones' },
              { id: 'assisted', label: 'Validaciones Asistidas' },
            ] as { id: ActiveTab; label: string }[]
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab: Lookup */}
      {activeTab === 'lookup' && (
        <div className="space-y-6">
          <RucLookupForm
            onLookup={handleLookup}
            isLoading={lookupLoading}
            canUseAuthorizedProvider={capabilities?.can_use_authorized_provider ?? true}
          />

          {lookupError && (
            <Alert variant="error" title="Error de consulta">{lookupError}</Alert>
          )}

          {lookupResult && (
            <RucLookupResultCard result={lookupResult} isTechnicalUser={true} />
          )}
        </div>
      )}

      {/* Tab: Sources */}
      {activeTab === 'sources' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {sources.map((src) => (
              <div key={src.source_id} className="rounded-xl border border-slate-200 bg-white p-4 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800 text-sm">{src.source_name}</span>
                  <DataSourceBadge source={src.source_type} label={src.status} />
                </div>
                <p className="text-slate-500">Prioridad de consulta: #{src.priority}</p>
                {src.last_successful_sync && (
                  <p className="text-slate-400 font-mono text-[11px]">
                    Última sincro: {new Date(src.last_successful_sync).toLocaleString('es-PE')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Datasets */}
      {activeTab === 'datasets' && (
        <div className="space-y-4 text-xs">
          {listLoading ? (
            <LoadingSkeleton rows={6} />
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold">Versión</th>
                    <th className="px-4 py-3 text-left font-semibold">Fuente</th>
                    <th className="px-4 py-3 text-left font-semibold">Publicado</th>
                    <th className="px-4 py-3 text-right font-semibold">Filas Aceptadas</th>
                    <th className="px-4 py-3 text-center font-semibold">Estado</th>
                    <th className="px-4 py-3 text-right font-semibold">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {datasets.map((ds) => (
                    <tr key={ds.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono font-bold text-indigo-700">v{ds.version}</td>
                      <td className="px-4 py-3">
                        <DataSourceBadge source={ds.source} label={ds.source_label} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {new Date(ds.published_date).toLocaleDateString('es-PE')}
                      </td>
                      <td className="px-4 py-3 text-right font-mono tabular-nums text-slate-700">
                        {ds.statistics?.accepted_rows?.toLocaleString() || '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                            ds.status === 'ACTIVE'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {ds.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        {ds.status !== 'ACTIVE' && canManageDatasets && (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedDataset(ds)
                              setShowActivateModal(true)
                            }}
                            className="font-semibold text-indigo-600 hover:underline"
                          >
                            Activar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab: Imports */}
      {activeTab === 'imports' && (
        <div className="space-y-4 text-xs">
          {listLoading ? (
            <LoadingSkeleton rows={6} />
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold">Job ID</th>
                    <th className="px-4 py-3 text-left font-semibold">Tipo</th>
                    <th className="px-4 py-3 text-left font-semibold">Usuario</th>
                    <th className="px-4 py-3 text-left font-semibold">Inicio</th>
                    <th className="px-4 py-3 text-center font-semibold">Estado</th>
                    <th className="px-4 py-3 text-right font-semibold">Progreso</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {imports.map((imp) => (
                    <tr key={imp.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono font-bold text-slate-700">{imp.id}</td>
                      <td className="px-4 py-3 text-slate-800">{imp.dataset_type}</td>
                      <td className="px-4 py-3 text-slate-600">{imp.triggered_by_user_name}</td>
                      <td className="px-4 py-3 text-slate-500">
                        {new Date(imp.started_at).toLocaleString('es-PE')}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                            imp.status === 'COMPLETED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : imp.status === 'FAILED'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {imp.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-slate-800">
                        {imp.progress_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab: Assisted Verifications */}
      {activeTab === 'assisted' && (
        <div className="space-y-6 text-xs">
          <AssistedRucVerificationForm onSubmit={handleCreateAssisted} isSubmitting={submittingModal} />

          <div className="space-y-3">
            <h4 className="font-bold uppercase tracking-wider text-slate-500">
              Dictámenes e Historial Assisted ({assistedList.length})
            </h4>

            <div className="space-y-2">
              {assistedList.map((item) => (
                <div key={item.id} className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-800">{item.ruc}</span>
                      <span className="font-medium text-slate-700">{item.observed_legal_name}</span>
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                          item.status === 'APPROVED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : item.status === 'PENDING_APPROVAL'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                    <p className="text-slate-500">
                      Revisado por <strong>{item.created_by_user_name}</strong> el {new Date(item.reviewed_at).toLocaleDateString('es-PE')}
                    </p>
                  </div>

                  {item.status === 'PENDING_APPROVAL' && canApproveAssisted && (
                    <Button
                      type="button"
                      onClick={() => setSelectedAssisted(item)}
                    >
                      Aprobar Dictamen
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Dialogs */}
      <StartRucImportDialog
        isOpen={showStartImportModal}
        isSubmitting={submittingModal}
        onStart={handleStartImport}
        onClose={() => setShowStartImportModal(false)}
      />

      {selectedDataset && (
        <ActivateRucDatasetDialog
          isOpen={showActivateModal}
          isSubmitting={submittingModal}
          dataset={selectedDataset}
          onActivate={handleActivateDataset}
          onClose={() => {
            setShowActivateModal(false)
            setSelectedDataset(null)
          }}
        />
      )}

      {selectedAssisted && (
        <ApproveAssistedVerificationDialog
          isOpen={!!selectedAssisted}
          isSubmitting={submittingModal}
          verification={selectedAssisted}
          onApprove={handleApproveAssisted}
          onClose={() => setSelectedAssisted(null)}
        />
      )}
    </div>
  )
}
