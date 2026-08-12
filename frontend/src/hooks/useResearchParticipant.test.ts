import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useResearchParticipant } from './useResearchParticipant'
import { researchApi } from '../api/research-api'
import { ApiRequestError } from '../types/api'

vi.mock('../api/research-api', () => ({
  researchApi: {
    getSelfParticipant: vi.fn(),
    selfEnroll: vi.fn(),
    currentConsent: vi.fn(),
    acceptConsent: vi.fn(),
    withdrawConsent: vi.fn(),
  },
}))

describe('useResearchParticipant', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('maneja el estado cuando el participante no existe (404 PARTICIPANT_NOT_FOUND)', async () => {
    vi.mocked(researchApi.getSelfParticipant).mockRejectedValueOnce(
      new ApiRequestError('No participante', {
        code: 'PARTICIPANT_NOT_FOUND',
        status: 404,
      }),
    )

    const { result } = renderHook(() => useResearchParticipant())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.needsEnrollment).toBe(true)
    expect(result.current.participant).toBeNull()
    expect(result.current.needsConsent).toBe(false)
  })

  it('realiza autoinscripción exitosamente con selfEnroll()', async () => {
    vi.mocked(researchApi.getSelfParticipant).mockRejectedValueOnce(
      new ApiRequestError('No participante', {
        code: 'PARTICIPANT_NOT_FOUND',
        status: 404,
      }),
    )

    vi.mocked(researchApi.selfEnroll).mockResolvedValueOnce({
      success: true,
      created: true,
      participant: {
        id: 'p-uuid-123',
        linked_user_id: 'user-uuid-1',
        participant_code: 'P-0001',
        is_active: true,
        enrollment_date: '2026-07-25T00:00:00Z',
        withdrawal_date: null,
        created_at: '2026-07-25T00:00:00Z',
        updated_at: '2026-07-25T00:00:00Z',
      },
    })

    vi.mocked(researchApi.currentConsent).mockRejectedValueOnce(new Error('No consent'))

    const { result } = renderHook(() => useResearchParticipant())

    await waitFor(() => {
      expect(result.current.needsEnrollment).toBe(true)
    })

    await act(async () => {
      await result.current.selfEnroll()
    })

    expect(result.current.participant?.participant_code).toBe('P-0001')
    expect(result.current.needsEnrollment).toBe(false)
    expect(result.current.needsConsent).toBe(true)
  })

  it('registra consentimiento exitosamente con acceptConsent()', async () => {
    vi.mocked(researchApi.getSelfParticipant).mockResolvedValueOnce({
      id: 'p-uuid-123',
      linked_user_id: 'user-uuid-1',
      participant_code: 'P-0001',
      is_active: true,
      enrollment_date: '2026-07-25T00:00:00Z',
      withdrawal_date: null,
      created_at: '2026-07-25T00:00:00Z',
      updated_at: '2026-07-25T00:00:00Z',
    })

    vi.mocked(researchApi.currentConsent).mockRejectedValueOnce(new Error('404'))

    vi.mocked(researchApi.acceptConsent).mockResolvedValueOnce({
      id: 'c-1',
      participant_id: 'p-uuid-123',
      consent_version: 'frontend-v1',
      accepted: true,
      accepted_at: '2026-07-25T12:00:00Z',
      withdrawn_at: null,
    })

    const { result } = renderHook(() => useResearchParticipant())

    await waitFor(() => {
      expect(result.current.needsConsent).toBe(true)
    })

    await act(async () => {
      await result.current.acceptConsent()
    })

    expect(result.current.consent?.accepted).toBe(true)
    expect(result.current.needsConsent).toBe(false)
    expect(researchApi.acceptConsent).toHaveBeenCalledWith(
      'p-uuid-123',
      'frontend-v1',
    )
  })
})
