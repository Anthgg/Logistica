import { createContext } from 'react'
import type { CollectorConfiguration, ResearchScenario } from '../types/research'

export interface ResearchCounters {
  keyboard: number
  mouse: number
  captures: number
  batches: number
  errors: number
}

export interface ResearchSessionContextValue {
  configuration: CollectorConfiguration | null
  participantId: string | null
  isActive: boolean
  hasCamera: boolean
  startedAtEpoch: number | null
  experimentalSessionId: string | null
  latestAcceptedFacialCaptureId: string | null
  latestBehavioralWindowId: string | null
  lastCaptureConfirmedAt: string | null
  lastBehaviorBatchConfirmedAt: string | null
  counters: ResearchCounters
  startSession: (options: {
    participantId: string
    scenario: ResearchScenario
    expectedDurationMinutes: number
  }) => Promise<void>
  finishSession: () => Promise<void>
  cancelSession: (reason: string) => Promise<void>
  stopForSecurity: () => void
}

export const ResearchSessionContext =
  createContext<ResearchSessionContextValue | null>(null)
