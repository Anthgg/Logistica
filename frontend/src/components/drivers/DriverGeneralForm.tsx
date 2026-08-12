import { useState } from 'react'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import type {
  DriverCreate,
  DriverIdentityDocumentType,
  DriverUpdate,
} from '../../types/drivers'
import { LOGISTICS_PERMISSIONS } from '../../features/logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../features/logistics-permissions/hooks/useLogisticsPermissions'

const IDENTITY_TYPES: { value: DriverIdentityDocumentType; label: string }[] = [
  { value: 'DNI', label: 'DNI' },
  { value: 'CE', label: 'Carnet de Extranjería' },
  { value: 'PASSPORT', label: 'Pasaporte' },
  { value: 'FOREIGN_ID', label: 'ID Extranjero' },
  { value: 'OTHER', label: 'Otro' },
]

interface Props {
  initial?: Partial<DriverCreate & DriverUpdate>
  onSubmit: (data: DriverCreate | DriverUpdate) => Promise<void>
  onCancel: () => void
  isSubmitting?: boolean
  mode?: 'create' | 'edit'
}

export function DriverGeneralForm({ initial, onSubmit, onCancel, isSubmitting, mode = 'create' }: Props) {
  const auth = useLogisticsPermissions()
  const canManage = auth.hasPermission(LOGISTICS_PERMISSIONS.drivers.manage)

  const [firstName, setFirstName] = useState(initial?.first_name ?? '')
  const [secondName, setSecondName] = useState(initial?.second_name ?? '')
  const [paternalSurname, setPaternalSurname] = useState(initial?.paternal_surname ?? '')
  const [maternalSurname, setMaternalSurname] = useState(initial?.maternal_surname ?? '')
  const [birthDate, setBirthDate] = useState(initial?.birth_date ?? '')
  const [nationality, setNationality] = useState(initial?.nationality ?? '')
  const [identityType, setIdentityType] = useState<DriverIdentityDocumentType>(
    (initial?.identity_document_type as DriverIdentityDocumentType) ?? 'DNI',
  )
  const [identityNumber, setIdentityNumber] = useState(
    initial?.identity_document_number ?? '',
  )
  const [notes, setNotes] = useState(initial?.notes ?? '')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!firstName.trim() || !paternalSurname.trim() || !identityNumber.trim()) return
    if (mode === 'create') {
      await onSubmit({
        first_name: firstName.trim(),
        second_name: secondName.trim() || undefined,
        paternal_surname: paternalSurname.trim(),
        maternal_surname: maternalSurname.trim() || undefined,
        birth_date: birthDate || undefined,
        nationality: nationality.trim() || undefined,
        identity_document_type: identityType,
        identity_document_number: identityNumber.trim(),
        notes: notes.trim() || undefined,
      } satisfies DriverCreate)
    } else {
      await onSubmit({
        first_name: firstName.trim(),
        second_name: secondName.trim() || undefined,
        paternal_surname: paternalSurname.trim(),
        maternal_surname: maternalSurname.trim() || undefined,
        birth_date: birthDate || undefined,
        nationality: nationality.trim() || undefined,
        notes: notes.trim() || undefined,
      } satisfies DriverUpdate)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Nombres"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
          disabled={!canManage}
        />
        <Input
          label="Segundo nombre (opcional)"
          value={secondName}
          onChange={(e) => setSecondName(e.target.value)}
          disabled={!canManage}
        />
        <Input
          label="Apellido paterno"
          value={paternalSurname}
          onChange={(e) => setPaternalSurname(e.target.value)}
          required
          disabled={!canManage}
        />
        <Input
          label="Apellido materno (opcional)"
          value={maternalSurname}
          onChange={(e) => setMaternalSurname(e.target.value)}
          disabled={!canManage}
        />
        <Input
          label="Fecha de nacimiento (opcional)"
          type="date"
          value={birthDate}
          onChange={(e) => setBirthDate(e.target.value)}
          disabled={!canManage}
        />
        <Input
          label="Nacionalidad (opcional)"
          value={nationality}
          onChange={(e) => setNationality(e.target.value)}
          disabled={!canManage}
        />
      </div>

      {mode === 'create' && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Tipo de documento</span>
            <select
              value={identityType}
              onChange={(e) => setIdentityType(e.target.value as DriverIdentityDocumentType)}
              disabled={!canManage}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
            >
              {IDENTITY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </label>
          <Input
            label="Número de documento"
            value={identityNumber}
            onChange={(e) => setIdentityNumber(e.target.value)}
            required
            disabled={!canManage}
            inputMode="text"
          />
        </div>
      )}

      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium text-slate-700">Notas (opcional)</span>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          disabled={!canManage}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
        />
      </label>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isSubmitting || !canManage} isLoading={isSubmitting}>
          {mode === 'create' ? 'Crear conductor' : 'Guardar cambios'}
        </Button>
      </div>
    </form>
  )
}