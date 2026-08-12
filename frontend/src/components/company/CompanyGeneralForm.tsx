import { useState, type FormEvent } from 'react'
import { Button } from '../../components/common/Button'
import { Input } from '../../components/common/Input'
import { SelectField } from '../../components/common/FormControls'
import type { CompanyProfile, CompanyProfileUpdate } from '../../types/company-profile'

interface CompanyGeneralFormProps {
  profile: CompanyProfile
  isSubmitting?: boolean
  onSubmit: (data: CompanyProfileUpdate) => Promise<void>
}

export function CompanyGeneralForm({
  profile,
  isSubmitting,
  onSubmit,
}: CompanyGeneralFormProps) {
  const [form, setForm] = useState<CompanyProfileUpdate>({
    business_name: profile.business_name,
    trade_name: profile.trade_name || '',
    ruc: profile.ruc,
    entity_type: profile.entity_type || '',
    economic_activity: profile.economic_activity || '',
    primary_email: profile.primary_email,
    primary_phone: profile.primary_phone,
    website_url: profile.website_url || '',
    country_code: profile.country_code,
    timezone: profile.timezone,
    document_language: profile.document_language,
    default_currency: profile.default_currency,
  })

  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.business_name.trim()) {
      setError('La Razón Social es obligatoria.')
      return
    }
    if (!form.ruc.trim()) {
      setError('El RUC es obligatorio.')
      return
    }
    setError(null)
    await onSubmit(form)
  }

  const update = (key: keyof CompanyProfileUpdate, value: string) => {
    setForm((curr) => ({ ...curr, [key]: value }))
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Input
          label="Razón social (Obligatoria)"
          value={form.business_name}
          onChange={(e) => update('business_name', e.target.value)}
          required
        />

        <Input
          label="Nombre comercial"
          value={form.trade_name || ''}
          onChange={(e) => update('trade_name', e.target.value)}
        />

        <div>
          <Input
            label="RUC (Número de Identificación Fiscal)"
            value={form.ruc}
            onChange={(e) => update('ruc', e.target.value)}
            required
          />
          <div className="mt-1 flex items-center gap-1.5 text-[10px]">
            <span className="font-semibold text-slate-400 uppercase">Estado RUC:</span>
            <span className="font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
              {profile.ruc_verification_status}
            </span>
          </div>
        </div>

        <Input
          label="Tipo de entidad / Personería"
          value={form.entity_type || ''}
          onChange={(e) => update('entity_type', e.target.value)}
          placeholder="Ej: Sociedad Anónima Cerrada (S.A.C.)"
        />

        <Input
          label="Correo principal institucional"
          type="email"
          value={form.primary_email}
          onChange={(e) => update('primary_email', e.target.value)}
          required
        />

        <Input
          label="Teléfono central"
          value={form.primary_phone}
          onChange={(e) => update('primary_phone', e.target.value)}
          required
        />

        <Input
          label="Sitio web (URL)"
          type="url"
          value={form.website_url || ''}
          onChange={(e) => update('website_url', e.target.value)}
          placeholder="https://andeslog.pe"
        />

        <SelectField
          label="País fiscal"
          value={form.country_code}
          onChange={(e) => update('country_code', e.target.value)}
        >
          <option value="PE">Perú (PE)</option>
          <option value="CL">Chile (CL)</option>
          <option value="CO">Colombia (CO)</option>
          <option value="EC">Ecuador (EC)</option>
        </SelectField>

        <SelectField
          label="Zona horaria principal"
          value={form.timezone}
          onChange={(e) => update('timezone', e.target.value)}
        >
          <option value="America/Lima">America/Lima (UTC-5)</option>
          <option value="America/Santiago">America/Santiago (UTC-3)</option>
          <option value="America/Bogota">America/Bogota (UTC-5)</option>
        </SelectField>

        <SelectField
          label="Moneda predeterminada"
          value={form.default_currency}
          onChange={(e) => update('default_currency', e.target.value)}
        >
          <option value="PEN">Soles (PEN - S/)</option>
          <option value="USD">Dólares (USD - $)</option>
        </SelectField>
      </div>

      <div className="flex justify-end pt-3 border-t border-slate-100">
        <Button type="submit" isLoading={isSubmitting}>
          Guardar borrador de datos
        </Button>
      </div>
    </form>
  )
}
