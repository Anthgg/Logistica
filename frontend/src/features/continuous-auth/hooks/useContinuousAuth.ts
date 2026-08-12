import { useContext } from 'react'
import { ContinuousAuthContext } from '../contexts/continuous-auth-context'

export function useContinuousAuth() {
  const context = useContext(ContinuousAuthContext)

  if (!context) {
    throw new Error(
      'useContinuousAuth debe utilizarse dentro de ContinuousAuthProvider.',
    )
  }

  return context
}
