import { Component, type ErrorInfo, type ReactNode } from 'react'
import { APP_ENV } from '../../api/config'
import { Button } from './Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class AppErrorBoundary extends Component<Props, State> {
  public override state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  public override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo })
    if (APP_ENV === 'local') {
      // eslint-disable-next-line no-console
      console.error('[AppErrorBoundary] Uncaught UI Error:', error, errorInfo)
    }
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.reload()
  }

  public override render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
            <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-rose-50 text-rose-600 font-bold text-xl">
              !
            </div>
            <h1 className="text-xl font-bold text-slate-900">
              Ocurrió un error inesperado
            </h1>
            <p className="mt-2 text-xs text-slate-500 leading-relaxed">
              La plataforma ha detectado un problema en la interfaz. No te preocupes, tus datos están seguros y no se ha comprometido tu sesión.
            </p>

            {APP_ENV === 'local' && this.state.error && (
              <div className="mt-4 max-h-40 overflow-auto rounded-lg bg-slate-900 p-3 text-left font-mono text-[10px] text-rose-300">
                <p className="font-bold">{this.state.error.toString()}</p>
                <pre className="mt-1 whitespace-pre-wrap">{this.state.errorInfo?.componentStack}</pre>
              </div>
            )}

            <div className="mt-6 flex justify-center gap-3">
              <Button onClick={this.handleReset}>Recargar aplicación</Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
