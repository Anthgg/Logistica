import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { companyProfileApi } from '../api/company-profile-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { CompanyGeneralForm } from '../components/company/CompanyGeneralForm'
import { CompanyBrandingPanel } from '../components/company/CompanyBrandingPanel'
import { AuthorizedSignersPanel } from '../components/company/AuthorizedSignersPanel'
import { NumberingPoliciesPanel } from '../components/company/NumberingPoliciesPanel'
import { CompanyProfileVersionsPanel } from '../components/company/CompanyProfileVersionsPanel'
import { InstitutionalDocumentPreview } from '../components/company/InstitutionalDocumentPreview'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import type { AuthorizedSigner, CompanyProfile, CompanyProfileUpdate } from '../types/company-profile'
import { getErrorMessage } from '../utils/errors'

type TabType =
  | 'general'
  | 'branding'
  | 'signers'
  | 'numbering'
  | 'versions'
  | 'preview'

export function CompanyProfileSettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab: TabType = (searchParams.get('tab') as TabType) || 'general'

  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [profile, setProfile] = useState<CompanyProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadProfile = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setProfile(await companyProfileApi.getProfile())
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  const setTab = (tab: TabType) => {
    setSearchParams({ tab })
  }

  // Operaciones Mutables
  const handleUpdateGeneral = async (data: CompanyProfileUpdate) => {
    setIsSaving(true)
    try {
      setProfile(await companyProfileApi.updateProfile(data))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const handleActivateLogo = async (assetId: string) => {
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await companyProfileApi.activateAsset(assetId)
      })
      if (!executed) return
      await loadProfile()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const handleActivateVersion = async (versionId: string) => {
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await companyProfileApi.activateVersion(versionId)
      })
      if (!executed) return
      await loadProfile()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const handleRevokeSigner = (signer: AuthorizedSigner) => {
    const reason = window.prompt(`Ingresa el motivo obligatorio para revocar a ${signer.full_name}:`)
    if (!reason || reason.trim().length < 5) return

    setIsSaving(true)
    guardSensitiveAction(async () => {
      await companyProfileApi.revokeSigner(signer.id, reason.trim())
    })
      .then((executed) => {
        if (executed) void loadProfile()
      })
      .catch((err: unknown) => setError(getErrorMessage(err)))
      .finally(() => setIsSaving(false))
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Configuración institucional"
        title="Datos de la Empresa y Comprobantes"
        description="Ficha oficial, representación impresa, firmantes autorizados y reglas de numeración."
        actions={
          profile ? (
            <div className="flex items-center gap-2">
              <StatusBadge value={profile.status?.toLowerCase() ?? ''}>{profile.status}</StatusBadge>
              <Button size="small" variant="secondary" onClick={() => setTab('preview')}>
                Vista previa documental
              </Button>
            </div>
          ) : undefined
        }
      />

      {/* Advertencia persistente de irretroactividad */}
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs text-amber-900 flex items-start gap-2.5">
        <span className="font-bold text-amber-700 flex items-center gap-1.5"><LogisticsIcon name="alert" size={14} aria-hidden /> Nota de Inmutabilidad Legal:</span>
        <p className="leading-relaxed">
          Los cambios institucionales afectan únicamente a <strong>documentos futuros</strong>. Los documentos ya emitidos
          conservan de forma inmutable su información y snapshot original.
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando ficha institucional de la empresa…</p>
        </div>
      ) : profile ? (
        <section className="panel operations-section space-y-4">
          {/* Navegación por Pestañas */}
          <div className="tabs border-b border-slate-200 pb-2">
            {[
              { id: 'general', label: 'Datos generales' },
              { id: 'branding', label: 'Identidad visual (Logo)' },
              { id: 'signers', label: 'Firmantes autorizados' },
              { id: 'numbering', label: 'Reglas de numeración' },
              { id: 'versions', label: 'Versiones de la ficha' },
              { id: 'preview', label: 'Vista previa' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-700 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
                onClick={() => setTab(tab.id as TabType)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Contenido de la pestaña activa */}
          <div className="pt-2">
            {activeTab === 'general' && (
              <CompanyGeneralForm
                profile={profile}
                isSubmitting={isSaving}
                onSubmit={handleUpdateGeneral}
              />
            )}

            {activeTab === 'branding' && (
              <CompanyBrandingPanel
                activeLogoAssetId={profile.active_logo_asset_id}
                canUploadLogo={profile.capabilities?.can_upload_logo ?? false}
                canActivateLogo={profile.capabilities?.can_activate_logo ?? false}
                onActivateLogo={handleActivateLogo}
              />
            )}

            {activeTab === 'signers' && (
              <AuthorizedSignersPanel
                canManageSigners={profile.capabilities?.can_manage_signers ?? false}
                canUploadSignature={profile.capabilities?.can_upload_signature ?? false}
                canRevokeSigner={profile.capabilities?.can_revoke_signer ?? false}
                onRevokeSigner={handleRevokeSigner}
              />
            )}

            {activeTab === 'numbering' && (
              <NumberingPoliciesPanel
                canManageNumbering={profile.capabilities?.can_manage_numbering ?? false}
              />
            )}

            {activeTab === 'versions' && (
              <CompanyProfileVersionsPanel
                canActivateProfile={profile.capabilities?.can_activate_profile ?? false}
                onActivateVersion={handleActivateVersion}
              />
            )}

            {activeTab === 'preview' && <InstitutionalDocumentPreview />}
          </div>
        </section>
      ) : null}
    </div>
  )
}
