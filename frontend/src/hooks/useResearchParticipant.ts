import { useCallback, useEffect, useState } from 'react'
import { researchApi } from '../api/research-api'
import { ApiRequestError } from '../types/api'
import type { Consent, Participant } from '../types/research'
import { getErrorMessage } from '../utils/errors'

export interface UseResearchParticipantResult {
  participant: Participant | null
  consent: Consent | null
  needsEnrollment: boolean
  needsConsent: boolean
  isLoading: boolean
  isEnrolling: boolean
  isAcceptingConsent: boolean
  error: string | null
  selfEnroll: () => Promise<Participant | null>
  acceptConsent: () => Promise<Consent | null>
  withdrawConsent: () => Promise<Consent | null>
  refresh: () => Promise<void>
  clearError: () => void
}

export function useResearchParticipant(): UseResearchParticipantResult {
  const [participant, setParticipant] = useState<Participant | null>(null)
  const [consent, setConsent] = useState<Consent | null>(null)
  const [needsEnrollment, setNeedsEnrollment] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isEnrolling, setIsEnrolling] = useState<boolean>(false)
  const [isAcceptingConsent, setIsAcceptingConsent] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => setError(null), [])

  const loadConsent = useCallback(async (): Promise<Consent | null> => {
    try {
      const currentConsent = await researchApi.currentConsent()
      setConsent(currentConsent)
      return currentConsent
    } catch {
      setConsent(null)
      return null
    }
  }, [])

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const selfParticipant = await researchApi.getSelfParticipant()
      setParticipant(selfParticipant)
      setNeedsEnrollment(false)
      await loadConsent()
    } catch (caught: unknown) {
      if (
        caught instanceof ApiRequestError &&
        (caught.code === 'PARTICIPANT_NOT_FOUND' || caught.status === 404)
      ) {
        setParticipant(null)
        setNeedsEnrollment(true)
        setConsent(null)
      } else {
        setError(getErrorMessage(caught))
      }
    } finally {
      setIsLoading(false)
    }
  }, [loadConsent])

  useEffect(() => {
    let isMounted = true
    void refresh().then(() => {
      if (!isMounted) return
    })
    return () => {
      isMounted = false
    }
  }, [refresh])

  const selfEnroll = useCallback(async (): Promise<Participant | null> => {
    setIsEnrolling(true)
    setError(null)
    try {
      const response = await researchApi.selfEnroll()
      setParticipant(response.participant)
      setNeedsEnrollment(false)
      await loadConsent()
      return response.participant
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
      return null
    } finally {
      setIsEnrolling(false)
    }
  }, [loadConsent])

  const acceptConsent = useCallback(async (): Promise<Consent | null> => {
    if (!participant) {
      setError('Debes estar inscrito como participante para aceptar el consentimiento.')
      return null
    }
    setIsAcceptingConsent(true)
    setError(null)
    try {
      const newConsent = await researchApi.acceptConsent(
        participant.id,
        'frontend-v1',
      )
      setConsent(newConsent)
      return newConsent
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
      return null
    } finally {
      setIsAcceptingConsent(false)
    }
  }, [participant])

  const withdrawConsent = useCallback(async (): Promise<Consent | null> => {
    if (!participant) return null
    setError(null)
    try {
      const withdrawnConsent = await researchApi.withdrawConsent(participant.id)
      setConsent(withdrawnConsent)
      return withdrawnConsent
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
      return null
    }
  }, [participant])

  const needsConsent =
    Boolean(participant) &&
    (!consent || consent.accepted !== true || consent.withdrawn_at !== null)

  return {
    participant,
    consent,
    needsEnrollment,
    needsConsent,
    isLoading,
    isEnrolling,
    isAcceptingConsent,
    error,
    selfEnroll,
    acceptConsent,
    withdrawConsent,
    refresh,
    clearError,
  }
}
