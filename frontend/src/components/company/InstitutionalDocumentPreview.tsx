import { useCallback, useEffect, useMemo, useState } from 'react'
import { companyProfileApi } from '../../api/company-profile-api'
import { Alert } from '../../components/common/Alert'
import { Button } from '../../components/common/Button'
import { LogisticsIcon } from '../../components/common/LogisticsIcon'
import { SecurePdfViewer } from '../../components/common/SecurePdfViewer'
import { SelectField } from '../../components/common/FormControls'
import {
  INSTITUTIONAL_DOCUMENT_TYPES,
  type AuthorizedSigner,
  type InstitutionalPreviewRequest,
  type OrganizationAddress,
} from '../../types/company-profile'
import { getErrorMessage } from '../../utils/errors'

export function InstitutionalDocumentPreview() {
  const [selectedDocCode, setSelectedDocCode] = useState<string>('AREC')
  const [selectedBranchId, setSelectedBranchId] = useState<string>('')
  const [selectedSignerId, setSelectedSignerId] = useState<string>('')
  const [customDataJson, setCustomDataJson] = useState<string>('')
  const [customDataError, setCustomDataError] = useState<string | null>(null)
  const [showCustomDataEditor, setShowCustomDataEditor] = useState(false)

  const [addresses, setAddresses] = useState<OrganizationAddress[]>([])
  const [signers, setSigners] = useState<AuthorizedSigner[]>([])
  const [isLoadingResources, setIsLoadingResources] = useState(true)

  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [previewKey, setPreviewKey] = useState<number>(0)

  // Carga de recursos auxiliares (sedes y firmantes activos)
  useEffect(() => {
    let isMounted = true
    setIsLoadingResources(true)

    Promise.all([
      companyProfileApi.listAddresses().catch(() => [] as OrganizationAddress[]),
      companyProfileApi
        .listSigners({ status: 'ACTIVE', page_size: 100 })
        .then((res) => res.items)
        .catch(() => [] as AuthorizedSigner[]),
    ])
      .then(([addrList, signerList]) => {
        if (isMounted) {
          setAddresses(addrList.filter((a) => a.is_active))
          setSigners(signerList.filter((s) => s.status === 'ACTIVE'))
        }
      })
      .finally(() => {
        if (isMounted) setIsLoadingResources(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  // Información del documento actualmente seleccionado
  const currentDocInfo = useMemo(() => {
    return (
      INSTITUTIONAL_DOCUMENT_TYPES.find((d) => d.code === selectedDocCode) ?? {
        code: selectedDocCode,
        name: `Documento (${selectedDocCode})`,
        shortName: selectedDocCode,
        category: 'INBOUND' as const,
        categoryLabel: 'General',
        description: 'Documento institucional para validación operativa y tributaria.',
        sampleCustomData: {},
      }
    )
  }, [selectedDocCode])

  // Agrupación de tipos documentales por categoría
  const groupedDocTypes = useMemo(() => {
    const groups: Record<string, typeof INSTITUTIONAL_DOCUMENT_TYPES> = {}
    for (const item of INSTITUTIONAL_DOCUMENT_TYPES) {
      if (!groups[item.categoryLabel]) {
        groups[item.categoryLabel] = []
      }
      groups[item.categoryLabel].push(item)
    }
    return groups
  }, [])

  // Validar JSON dinámico en tiempo real
  const handleCustomDataChange = (value: string) => {
    setCustomDataJson(value)
    if (!value.trim()) {
      setCustomDataError(null)
      return
    }
    try {
      const parsed = JSON.parse(value)
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        setCustomDataError('El cuerpo dinámico debe ser un objeto JSON (ej: {"clave": "valor"}).')
      } else {
        setCustomDataError(null)
      }
    } catch (err: unknown) {
      setCustomDataError(err instanceof Error ? err.message : 'Sintaxis JSON inválida.')
    }
  }

  // Cargar datos de ejemplo según el tipo documental
  const handleLoadSampleData = () => {
    if (currentDocInfo.sampleCustomData) {
      setCustomDataJson(JSON.stringify(currentDocInfo.sampleCustomData, null, 2))
      setCustomDataError(null)
      setShowCustomDataEditor(true)
    }
  }

  // Limpiar datos personalizados
  const handleClearCustomData = () => {
    setCustomDataJson('')
    setCustomDataError(null)
  }

  // Construir objeto de solicitud para el endpoint
  const buildPreviewRequest = useCallback((): InstitutionalPreviewRequest => {
    let customData: Record<string, unknown> | null = null
    if (customDataJson.trim()) {
      try {
        const parsed = JSON.parse(customDataJson.trim())
        if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
          customData = parsed as Record<string, unknown>
        }
      } catch {
        // En caso de error, enviar objeto vacío
        customData = {}
      }
    }

    return {
      doc_type_code: selectedDocCode,
      branch_id: selectedBranchId.trim() ? selectedBranchId.trim() : null,
      signer_id: selectedSignerId.trim() ? selectedSignerId.trim() : null,
      custom_data: customData ?? {},
    }
  }, [selectedDocCode, selectedBranchId, selectedSignerId, customDataJson])

  // Disparar la vista previa
  const handleOpenPreview = () => {
    if (customDataError) {
      setPreviewError(
        'Corrige los errores de sintaxis JSON en los parámetros dinámicos antes de continuar.',
      )
      return
    }
    setPreviewError(null)
    setPreviewKey((k) => k + 1)
    setIsPreviewOpen(true)
  }

  // Sede seleccionada para mostrar en el resumen
  const selectedAddressLabel = useMemo(() => {
    if (!selectedBranchId) return 'Resolución Automática (Sede Principal Activa)'
    const addr = addresses.find(
      (a) => a.branch_id === selectedBranchId || a.id === selectedBranchId,
    )
    if (addr) {
      return `${addr.label || 'Sede'} — ${addr.branch_name || addr.district} (${addr.address_line})`
    }
    return selectedBranchId
  }, [selectedBranchId, addresses])

  // Firmante seleccionado para mostrar en el resumen
  const selectedSignerLabel = useMemo(() => {
    if (!selectedSignerId) return 'Resolución Automática (Según Políticas Institucionales)'
    const signer = signers.find((s) => s.id === selectedSignerId)
    if (signer) {
      return `${signer.full_name} (${signer.job_title} — ${signer.department})`
    }
    return selectedSignerId
  }, [selectedSignerId, signers])

  const customFieldsCount = useMemo(() => {
    if (!customDataJson.trim()) return 0
    try {
      const parsed = JSON.parse(customDataJson.trim())
      return Object.keys(parsed).length
    } catch {
      return 0
    }
  }, [customDataJson])

  return (
    <div className="space-y-6 text-xs">
      {/* Banner Informativo y Explicativo */}
      <div className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50/80 via-indigo-50/40 to-slate-50 p-4 sm:p-5 text-blue-950 shadow-xs space-y-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-xs">
            <LogisticsIcon name="document" size={20} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-blue-950">
                Motor de Vista Previa Institucional (Fase 021)
              </h3>
              <span className="rounded-full bg-blue-200/80 px-2 py-0.5 text-[10px] font-bold text-blue-900 uppercase tracking-wider">
                Cloud Run & Docker Live
              </span>
            </div>
            <p className="text-xs text-blue-900/90 leading-relaxed">
              Genera una representación impresa oficial en PDF utilizando la versión borrador de la
              ficha empresarial, logotipo activo, y membrete institucional.{' '}
              <strong>
                Esta acción es de simulación y no reserva ni consume correlativos de numeración.
              </strong>
            </p>
          </div>
        </div>

        {/* Píldoras de automatización */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t border-blue-200/60 text-[11px]">
          <div className="flex items-center gap-2 text-blue-900">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 font-bold shrink-0">
              ✓
            </span>
            <span>
              <strong>Sede opcional:</strong> Si se omite o es{' '}
              <code className="font-mono bg-blue-100/80 px-1 rounded">null</code>, el backend asigna
              la sede fiscal / principal activa.
            </span>
          </div>
          <div className="flex items-center gap-2 text-blue-900">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 font-bold shrink-0">
              ✓
            </span>
            <span>
              <strong>Firmante opcional:</strong> Si se omite o es{' '}
              <code className="font-mono bg-blue-100/80 px-1 rounded">null</code>, se resuelve por
              políticas documentales vigentes.
            </span>
          </div>
        </div>
      </div>

      {previewError && <Alert variant="error">{previewError}</Alert>}

      {/* Formulario de Configuración de la Vista Previa */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs space-y-5">
        <div className="border-b border-slate-100 pb-3">
          <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-2">
            <LogisticsIcon name="sliders" size={16} className="text-blue-700" />
            Parámetros de Generación Documental
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Selecciona el tipo documental y personaliza opcionalmente la sede o el firmante para la
            simulación.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Tipo de Documento */}
          <SelectField
            label="Tipo de Comprobante / Documento *"
            value={selectedDocCode}
            onChange={(e) => {
              setSelectedDocCode(e.target.value)
              setPreviewError(null)
            }}
            disabled={isLoadingResources}
          >
            {Object.entries(groupedDocTypes).map(([category, items]) => (
              <optgroup key={category} label={category}>
                {items.map((item) => (
                  <option key={item.code} value={item.code}>
                    [{item.code}] {item.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </SelectField>

          {/* Sede / Sucursal */}
          <SelectField
            label="Sede Operativa (branch_id)"
            value={selectedBranchId}
            onChange={(e) => setSelectedBranchId(e.target.value)}
            disabled={isLoadingResources}
          >
            <option value="">(Resolución Automática — Sede Principal Activa)</option>
            {addresses.map((addr) => (
              <option key={addr.id} value={addr.branch_id || addr.id}>
                {addr.label || 'Sede'} — {addr.branch_name || addr.district} ({addr.address_line})
                {addr.is_primary ? ' [Principal]' : ''}
              </option>
            ))}
          </SelectField>

          {/* Firmante Autorizado */}
          <SelectField
            label="Firmante Institucional (signer_id)"
            value={selectedSignerId}
            onChange={(e) => setSelectedSignerId(e.target.value)}
            disabled={isLoadingResources}
          >
            <option value="">(Resolución Automática — Según Políticas de Firma)</option>
            {signers.map((signer) => (
              <option key={signer.id} value={signer.id}>
                {signer.full_name} ({signer.job_title} — {signer.department})
              </option>
            ))}
          </SelectField>
        </div>

        {/* Ficha descriptiva del documento seleccionado */}
        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-blue-100 px-2 py-0.5 font-mono font-bold text-blue-800 text-[11px]">
                {currentDocInfo.code}
              </span>
              <span className="font-bold text-slate-900">{currentDocInfo.name}</span>
              <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700">
                {currentDocInfo.categoryLabel}
              </span>
            </div>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              {currentDocInfo.description}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {currentDocInfo.sampleCustomData && (
              <Button
                type="button"
                size="small"
                variant="secondary"
                onClick={handleLoadSampleData}
                className="text-[11px]"
              >
                <LogisticsIcon name="box" size={14} />
                Cargar datos de ejemplo
              </Button>
            )}
            <button
              type="button"
              onClick={() => setShowCustomDataEditor((v) => !v)}
              className="px-2.5 py-1.5 text-[11px] font-bold text-blue-700 hover:bg-blue-100/60 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <LogisticsIcon name="sliders" size={14} />
              {showCustomDataEditor
                ? 'Ocultar Variables Dinámicas'
                : 'Variables Dinámicas (custom_data)'}
              {customFieldsCount > 0 && (
                <span className="rounded-full bg-blue-600 text-white px-1.5 py-0.2 text-[10px] font-bold">
                  {customFieldsCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Editor de Variables Dinámicas (custom_data) */}
        {showCustomDataEditor && (
          <div className="rounded-xl border border-slate-200 bg-slate-900 text-slate-100 p-4 space-y-3 shadow-inner">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] font-bold text-emerald-400">
                  custom_data (JSON)
                </span>
                <span className="text-[10px] text-slate-400">
                  Valores inyectados dinámicamente en la plantilla institucional del comprobante.
                </span>
              </div>
              <div className="flex items-center gap-2">
                {customDataJson && (
                  <button
                    type="button"
                    onClick={handleClearCustomData}
                    className="text-[10px] font-bold text-rose-400 hover:text-rose-300 transition-colors"
                  >
                    Limpiar JSON
                  </button>
                )}
              </div>
            </div>

            <textarea
              className="w-full h-32 rounded-lg bg-slate-950 p-3 font-mono text-xs text-emerald-300 border border-slate-800 focus:border-emerald-500 focus:outline-hidden leading-relaxed resize-y"
              placeholder={`{\n  "po_number": "OC-2026-0001",\n  "observations": "Texto de prueba..."\n}`}
              value={customDataJson}
              onChange={(e) => handleCustomDataChange(e.target.value)}
              spellCheck={false}
            />

            {customDataError ? (
              <p className="text-[11px] font-semibold text-rose-400 flex items-center gap-1.5">
                <LogisticsIcon name="alert" size={13} />
                {customDataError}
              </p>
            ) : customDataJson.trim() ? (
              <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                <LogisticsIcon name="check" size={13} />
                JSON válido ({customFieldsCount} campo{customFieldsCount === 1 ? '' : 's'}{' '}
                configurado{customFieldsCount === 1 ? '' : 's'})
              </p>
            ) : (
              <p className="text-[10px] text-slate-400">
                Opcional: Si se deja vacío, el backend utiliza el diccionario vacío por defecto{' '}
                <code className="text-slate-300">{'{}'}</code>.
              </p>
            )}
          </div>
        )}

        {/* Resumen del Payload a Enviar */}
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5 space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Resumen de Resolución del Comprobante:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
            <div className="rounded-lg bg-white p-2 border border-slate-200">
              <span className="text-slate-400 block text-[10px]">Código Documental:</span>
              <strong className="text-blue-700 font-mono">{selectedDocCode}</strong>
            </div>
            <div className="rounded-lg bg-white p-2 border border-slate-200 truncate">
              <span className="text-slate-400 block text-[10px]">Sede de Emisión:</span>
              <strong className="text-slate-800 truncate" title={selectedAddressLabel}>
                {selectedBranchId ? 'Sede Específica' : '⚡ Automática (Principal)'}
              </strong>
            </div>
            <div className="rounded-lg bg-white p-2 border border-slate-200 truncate">
              <span className="text-slate-400 block text-[10px]">Firmante Responsable:</span>
              <strong className="text-slate-800 truncate" title={selectedSignerLabel}>
                {selectedSignerId ? 'Firmante Específico' : '⚡ Automático (Por Políticas)'}
              </strong>
            </div>
          </div>
        </div>

        {/* Botón de Generación de Vista Previa */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          <div className="text-[11px] text-slate-500">
            Al generar la vista previa, se abrirá el visor seguro con opciones de{' '}
            <strong>descarga</strong> e <strong>impresión</strong>.
          </div>
          <Button
            type="button"
            variant="primary"
            onClick={handleOpenPreview}
            disabled={isLoadingResources || Boolean(customDataError)}
            className="w-full sm:w-auto shadow-sm"
          >
            <LogisticsIcon name="document" size={16} />
            Generar vista previa en PDF
          </Button>
        </div>
      </div>

      {/* Visor PDF Seguro en Modal */}
      <SecurePdfViewer
        key={previewKey}
        isOpen={isPreviewOpen}
        title={`Vista Previa Institucional — ${currentDocInfo.shortName}`}
        code={`PREV-${currentDocInfo.code}-2026-00000`}
        fetchBlobUrl={async () => {
          try {
            const req = buildPreviewRequest()
            return await companyProfileApi.getPreviewDocumentBlobUrl(req)
          } catch (err: unknown) {
            const msg = getErrorMessage(err)
            setPreviewError(msg)
            throw new Error(msg)
          }
        }}
        onClose={() => setIsPreviewOpen(false)}
      />
    </div>
  )
}
