import { useContext } from 'react'
import { ResearchSessionContext } from '../contexts/research-session-context'

export function useResearchSession() {
  const context = useContext(ResearchSessionContext)
  if (!context) throw new Error('useResearchSession debe usarse dentro del proveedor.')
  return context
}
