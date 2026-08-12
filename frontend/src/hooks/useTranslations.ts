import { useContext } from 'react'
import { I18nContext } from '../contexts/i18n-context'

export function useTranslations() {
  const context = useContext(I18nContext)

  if (!context) {
    throw new Error(
      'useTranslations debe utilizarse dentro de I18nProvider.',
    )
  }

  return context
}
