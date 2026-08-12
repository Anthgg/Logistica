import { useContext } from 'react'
import {
  LogisticsAccessContext,
  defaultLogisticsAccessState,
  type LogisticsAccessState,
} from '../contexts/logistics-access-context'

export function useLogisticsAccess(): LogisticsAccessState {
  const context = useContext(LogisticsAccessContext)
  if (context === undefined) {
    return defaultLogisticsAccessState
  }
  return context
}

export type { LogisticsAccessState } from '../contexts/logistics-access-context'