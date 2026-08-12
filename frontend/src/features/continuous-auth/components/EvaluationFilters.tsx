import { useState, type FormEvent } from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { SelectField } from '../../../components/common/FormControls'
import { useTranslations } from '../../../hooks/useTranslations'
import type { EvaluationFiltersValue } from '../types/continuous-auth'

const emptyFilters: EvaluationFiltersValue = {
  user_id: '',
  session_id: '',
  participant_id: '',
  risk_level: '',
  authentication_level: '',
  date_from: '',
  date_to: '',
}
const riskLevels = ['low', 'medium', 'high', 'critical'] as const
const authenticationLevels = [
  'traditional',
  'continuously_verified',
  'verification_required',
  'restricted',
  'terminated',
] as const

export function EvaluationFilters({
  value,
  onApply,
}: {
  value: EvaluationFiltersValue
  onApply: (filters: EvaluationFiltersValue) => void
}) {
  const { translate } = useTranslations()
  const [draft, setDraft] = useState(value)
  const [isExpanded, setIsExpanded] = useState(false)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onApply(draft)
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900">
            Filtros de evaluación
          </h2>
          <p className="text-xs text-slate-500">
            Acota la consulta antes de cargar registros.
          </p>
        </div>
        <button
          type="button"
          className="min-h-11 rounded-lg px-3 text-xs font-semibold text-blue-700 md:hidden"
          onClick={() => setIsExpanded((current) => !current)}
          aria-expanded={isExpanded}
        >
          {isExpanded ? 'Ocultar filtros' : 'Mostrar filtros'}
        </button>
      </div>

      <form
        className={`${isExpanded ? 'grid' : 'hidden'} mt-4 gap-3 md:grid md:grid-cols-2 xl:grid-cols-4`}
        onSubmit={handleSubmit}
      >
        <Input
          label="ID de usuario"
          value={draft.user_id}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              user_id: event.target.value,
            }))
          }
        />
        <Input
          label="ID de sesión"
          value={draft.session_id}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              session_id: event.target.value,
            }))
          }
        />
        <Input
          label="ID de participante"
          value={draft.participant_id}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              participant_id: event.target.value,
            }))
          }
        />
        <SelectField
          label="Nivel de riesgo"
          value={draft.risk_level}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              risk_level:
                event.target.value as EvaluationFiltersValue['risk_level'],
            }))
          }
        >
          <option value="">Todos</option>
          {riskLevels.map((level) => (
            <option key={level} value={level}>
              {translate('risk', level, level)}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Nivel de autenticación"
          value={draft.authentication_level}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              authentication_level:
                event.target
                  .value as EvaluationFiltersValue['authentication_level'],
            }))
          }
        >
          <option value="">Todos</option>
          {authenticationLevels.map((level) => (
            <option key={level} value={level}>
              {translate('auth_level', level, level)}
            </option>
          ))}
        </SelectField>
        <Input
          label="Desde"
          type="datetime-local"
          value={draft.date_from}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              date_from: event.target.value,
            }))
          }
        />
        <Input
          label="Hasta"
          type="datetime-local"
          value={draft.date_to}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              date_to: event.target.value,
            }))
          }
        />
        <div className="flex items-end gap-2">
          <Button type="submit">Aplicar filtros</Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setDraft(emptyFilters)
              onApply(emptyFilters)
            }}
          >
            Limpiar
          </Button>
        </div>
      </form>
    </section>
  )
}
