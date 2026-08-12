import { Link } from 'react-router-dom'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'

export function TerminatedSessionScreen() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-lg">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-700">
          <LogisticsIcon name="shield" size={28} />
        </span>
        <h1 className="mt-5 text-2xl font-bold text-slate-950">
          Tu sesión fue finalizada por seguridad
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Para proteger tu cuenta, inicia sesión nuevamente. Si esta situación
          se repite, contacta al equipo de soporte de tu organización.
        </p>
        <Link
          to="/login"
          className="mt-6 inline-flex min-h-11 items-center justify-center rounded-lg bg-blue-700 px-5 text-sm font-bold text-white no-underline hover:bg-blue-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
        >
          Volver a iniciar sesión
        </Link>
      </section>
    </main>
  )
}
