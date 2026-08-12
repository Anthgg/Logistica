import { Link } from 'react-router-dom'

export function UnauthorizedPage() {
  return (
    <main className="error-page">
      <div className="error-page__code">403</div>
      <p className="eyebrow">Acceso restringido</p>
      <h1>No tienes permisos para esta sección</h1>
      <p>Vuelve al panel o inicia sesión con otra cuenta.</p>
      <Link className="button button--primary button--medium" to="/profile">
        Volver al perfil
      </Link>
    </main>
  )
}
