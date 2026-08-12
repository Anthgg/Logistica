import { useEffect, useState } from 'react'
import { companyProfileApi } from '../../api/company-profile-api'
import { Button } from '../../components/common/Button'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { OrganizationAsset } from '../../types/company-profile'
import { formatDateTime } from '../../utils/date'
import { getErrorMessage } from '../../utils/errors'

interface CompanyBrandingPanelProps {
  activeLogoAssetId: string | null
  canUploadLogo: boolean
  canActivateLogo: boolean
  onActivateLogo: (assetId: string) => Promise<void>
}

export function CompanyBrandingPanel({
  activeLogoAssetId,
  canUploadLogo,
  canActivateLogo,
  onActivateLogo,
}: CompanyBrandingPanelProps) {
  const [assets, setAssets] = useState<OrganizationAsset[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadAssets = async () => {
    setIsLoading(true)
    try {
      setAssets(await companyProfileApi.listAssets())
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadAssets()
  }, [])

  const handleFileChange = (file: File | null) => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
    if (!file) {
      setSelectedFile(null)
      return
    }

    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
      setError('Formato no permitido. Utiliza PNG, JPEG o WebP.')
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      setError('El archivo excede el tamaño máximo permitido de 2 MB.')
      return
    }

    setError(null)
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setIsUploading(true)
    try {
      await companyProfileApi.uploadLogo(selectedFile)
      setSelectedFile(null)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
      await loadAssets()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-6 text-xs">
      {/* Subir nuevo logotipo */}
      {canUploadLogo && (
        <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
          <h3 className="font-bold text-slate-900">Subir nuevo logotipo oficial</h3>
          <p className="text-[11px] text-slate-500">
            Formato PNG o WebP recomendado sobre fondo transparente. Tamaño máximo 2 MB.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="text-xs text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-50 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
              onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
            />

            {selectedFile && (
              <Button size="small" onClick={() => void handleUpload()} isLoading={isUploading}>
                Subir asset
              </Button>
            )}
          </div>

          {previewUrl && (
            <div className="mt-2 rounded-lg border border-slate-300 bg-white p-2 w-fit">
              <span className="text-[10px] font-bold text-slate-400 block mb-1">
                Vista previa local temporal:
              </span>
              <img src={previewUrl} alt="Vista previa del logo" className="h-12 object-contain" />
            </div>
          )}

          {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}
        </section>
      )}

      {/* Lista de logotipos subidos */}
      <section className="space-y-3">
        <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
          Historial de logotipos institucionales
        </h3>

        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando activos de imagen…</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {assets.map((asset) => {
              const isActive = asset.id === activeLogoAssetId
              return (
                <div
                  key={asset.id}
                  className={`flex flex-col justify-between rounded-xl border p-3 bg-white shadow-xs ${
                    isActive ? 'border-emerald-300 bg-emerald-50/20' : 'border-slate-200'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] font-bold text-slate-400">
                        {asset.file_name}
                      </span>
                      {isActive && <StatusBadge value="active">Activo</StatusBadge>}
                    </div>

                    <div className="flex h-16 items-center justify-center rounded-lg border border-slate-100 bg-slate-50 p-2">
                      <span className="text-[10px] font-mono text-slate-400">
                        {asset.mime_type} · {(asset.file_size_bytes / 1024).toFixed(1)} KB
                      </span>
                    </div>

                    <div className="text-[10px] text-slate-500 space-y-0.5">
                      <p>Subido por: {asset.uploaded_by_user_name}</p>
                      <p>Fecha: {formatDateTime(asset.uploaded_at)}</p>
                    </div>
                  </div>

                  {!isActive && canActivateLogo && (
                    <div className="mt-3 pt-2 border-t border-slate-100 flex justify-end">
                      <Button
                        size="small"
                        variant="ghost"
                        onClick={() => void onActivateLogo(asset.id)}
                      >
                        Activar en documentos
                      </Button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
