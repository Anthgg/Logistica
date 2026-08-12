import { AuthProvider } from './contexts/AuthContext'
import { I18nProvider } from './contexts/I18nProvider'
import { AppRouter } from './router/AppRouter'

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </I18nProvider>
  )
}
