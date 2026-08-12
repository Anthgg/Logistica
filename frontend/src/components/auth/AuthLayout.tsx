import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { APP_NAME } from '../../api/config'
import { LanguageSwitcher } from '../common/LanguageSwitcher'

export function AuthLayout() {
  const { pathname } = useLocation()

  useEffect(() => {
    document.documentElement.scrollTop = 0
    document.body.scrollTop = 0
  }, [pathname])

  return (
    <main className="auth-layout">
      <section className="auth-layout__brand" aria-label="Presentación">
        <div className="auth-layout__brand-content">
          <div className="brand-lockup">
            <span className="brand-mark" aria-hidden="true">
              <LogisticsIcon name="route" size={24} />
            </span>
            <span>{APP_NAME}</span>
          </div>
          <div className="auth-layout__message">
            <p className="eyebrow eyebrow--light">Operación confiable</p>
            <h1>Tu operación logística, siempre en movimiento.</h1>
            <p>
              Coordina envíos, almacenes, rutas e incidencias desde un único
              centro de control seguro.
            </p>
          </div>
          <div className="auth-route-map" aria-hidden="true">
            <div className="auth-route-map__line" />
            <span className="auth-route-map__node auth-route-map__node--origin">
              <LogisticsIcon name="building" size={20} />
            </span>
            <span className="auth-route-map__vehicle">
              <LogisticsIcon name="truck" size={22} />
            </span>
            <span className="auth-route-map__node auth-route-map__node--destination">
              <LogisticsIcon name="location" size={20} />
            </span>
          </div>
          <div className="auth-feature-list" aria-label="Capacidades de la plataforma">
            <div>
              <LogisticsIcon name="activity" size={18} />
              <span>Seguimiento operativo</span>
            </div>
            <div>
              <LogisticsIcon name="shield" size={18} />
              <span>Acceso protegido</span>
            </div>
            <div>
              <LogisticsIcon name="reports" size={18} />
              <span>Decisiones con datos</span>
            </div>
          </div>
          <div className="auth-layout__security-note">
            <span className="security-pulse" aria-hidden="true" />
            <div>
              <strong>Conexión protegida</strong>
              <span>Cookies HttpOnly y validación CSRF</span>
            </div>
          </div>
        </div>
      </section>
      <section className="auth-layout__form">
        <div className="absolute right-4 top-4">
          <LanguageSwitcher />
        </div>
        <div className="auth-layout__mobile-brand">
          <span className="brand-mark" aria-hidden="true">
            <LogisticsIcon name="route" size={21} />
          </span>
          <span>{APP_NAME}</span>
        </div>
        <div className="auth-card">
          <Outlet />
        </div>
        <p className="auth-layout__footer">
          AndesLog Operaciones S.A.C. · Acceso seguro
        </p>
      </section>
    </main>
  )
}
