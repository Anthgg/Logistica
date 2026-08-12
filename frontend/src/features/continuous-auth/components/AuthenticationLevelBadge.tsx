import { useTranslations } from '../../../hooks/useTranslations'
import type { AuthenticationLevel } from '../types/continuous-auth'

const styles: Record<AuthenticationLevel, string> = {
  traditional: 'border-slate-200 bg-slate-50 text-slate-700',
  continuously_verified:
    'border-blue-200 bg-blue-50 text-blue-700',
  verification_required:
    'border-amber-200 bg-amber-50 text-amber-800',
  restricted: 'border-orange-200 bg-orange-50 text-orange-800',
  terminated: 'border-rose-200 bg-rose-50 text-rose-800',
}

export function AuthenticationLevelBadge({
  level,
}: {
  level: AuthenticationLevel
}) {
  const { translate } = useTranslations()
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[level]}`}
    >
      {translate('auth_level', level, level)}
    </span>
  )
}
