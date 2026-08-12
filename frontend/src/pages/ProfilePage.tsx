import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useAuth } from '../hooks/useAuth'
import { useTranslations } from '../hooks/useTranslations'
import { formatDateTime } from '../utils/date'
import { APP_ENV, APP_VERSION, BUILD_SHA } from '../api/config'

export function ProfilePage() {
  const { user, currentSession } = useAuth()
  const { translate } = useTranslations()
  if (!user) return null
  return (
    <div className="page">
      <PageHeader
        eyebrow="Cuenta de operador"
        title={`Hola, ${user.full_name.split(' ')[0]}`}
        description="Identidad y contexto de la sesión autenticada."
      />
      <div className="operations-grid">
        <section className="panel operations-section">
          <div className="section-heading">
            <div><p className="eyebrow">Identidad</p><h2>Información de la cuenta</h2></div>
            <StatusBadge value={user.is_active ? 'active' : 'inactive'} />
          </div>
          <dl className="detail-list detail-list--compact">
            <div><dt>Nombre completo</dt><dd>{user.full_name}</dd></div>
            <div><dt>Correo</dt><dd>{user.email}</dd></div>
            <div><dt>Rol operativo</dt><dd>{translate('common', user.role, user.role)}</dd></div>
            <div><dt>Cuenta creada</dt><dd>{formatDateTime(user.created_at)}</dd></div>
          </dl>
        </section>
        <section className="panel operations-section">
          <div className="section-heading"><div><p className="eyebrow">Acceso actual</p><h2>Sesión segura</h2></div></div>
          <dl className="detail-list detail-list--compact">
            <div><dt>Nivel</dt><dd>{currentSession ? translate('auth_level', currentSession.authentication_level, currentSession.authentication_level) : 'Estándar'}</dd></div>
            <div><dt>Inicio</dt><dd>{formatDateTime(currentSession?.created_at)}</dd></div>
            <div><dt>Última actividad</dt><dd>{formatDateTime(currentSession?.last_activity_at)}</dd></div>
            <div><dt>Expira</dt><dd>{formatDateTime(currentSession?.expires_at)}</dd></div>
            <div><dt>Versión build</dt><dd><span className="font-mono text-xs">{APP_VERSION} ({BUILD_SHA}) — {APP_ENV}</span></dd></div>
          </dl>
        </section>
      </div>
    </div>
  )
}
