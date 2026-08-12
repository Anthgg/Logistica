interface LoadingScreenProps {
  message?: string
}

export function LoadingScreen({
  message = 'Verificando tu sesión…',
}: LoadingScreenProps) {
  return (
    <div className="loading-screen" role="status" aria-live="polite">
      <div className="brand-mark brand-mark--large" aria-hidden="true">
        AL
      </div>
      <p>{message}</p>
      <div className="loading-screen__track" aria-hidden="true">
        <span />
      </div>
    </div>
  )
}
