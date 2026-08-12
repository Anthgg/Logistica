import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="error-page">
      <div className="error-page__code">404</div>
      <p className="eyebrow">Página no encontrada</p>
      <h1>Este destino no existe</h1>
      <p>Comprueba la dirección o vuelve al inicio.</p>
      <Link className="button button--primary button--medium" to="/profile">
        Volver al perfil
      </Link>
    </main>
  )
}
