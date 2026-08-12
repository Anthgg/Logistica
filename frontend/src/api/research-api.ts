import { apiRequest } from './api-client'
import { getRequestLanguage } from './locale'
import { ApiRequestError } from '../types/api'
import type { PaginatedResponse } from '../types/operations'
import type {
  BehavioralBatch,
  BehavioralBatchResponse,
  CollectorConfiguration,
  Consent,
  ExperimentalSession,
  ExperimentalSessionAnnotation,
  FacialCaptureResponse,
  Participant,
  SelfEnrollResponse,
  SessionMutationResponse,
  SessionStartResponse,
  StartSessionRequest,
} from '../types/research'

export const researchApi = {
  getSelfParticipant: () =>
    apiRequest<Participant>({
      path: '/research/participants/me',
    }),
  selfEnroll: () =>
    apiRequest<SelfEnrollResponse>({
      path: '/research/participants/self-enroll',
      method: 'POST',
    }),
  participants: () =>
    apiRequest<PaginatedResponse<Participant>>({
      path: '/research/participants?page_size=100',
    }),
  createParticipant: (linkedUserId?: string) =>
    apiRequest<Participant>({
      path: '/research/participants',
      method: 'POST',
      body: { linked_user_id: linkedUserId || null },
    }),
  getParticipant: (id: string) =>
    apiRequest<Participant>({
      path: `/research/participants/${id}`,
    }),
  updateParticipant: (
    id: string,
    body: { linked_user_id?: string | null; is_active?: boolean | null },
  ) =>
    apiRequest<Participant>({
      path: `/research/participants/${id}`,
      method: 'PATCH',
      body,
    }),
  withdrawParticipant: (id: string) =>
    apiRequest<Participant>({
      path: `/research/participants/${id}/withdraw`,
      method: 'POST',
    }),
  currentConsent: () =>
    apiRequest<Consent>({ path: '/research/consent/current' }),
  acceptConsent: (participantId: string, version = 'frontend-v1') =>
    apiRequest<Consent>({
      path: '/research/consent',
      method: 'POST',
      body: {
        participant_id: participantId,
        consent_version: version,
        accepted: true,
      },
    }),
  withdrawConsent: (participantId: string) =>
    apiRequest<Consent>({
      path: '/research/consent/withdraw',
      method: 'POST',
      body: { participant_id: participantId },
    }),
  start: (body: Partial<StartSessionRequest> & { participant_id: string }) => {
    const fullBody: StartSessionRequest = {
      participant_id: body.participant_id,
      scenario: body.scenario ?? 'register_shipment',
      expected_duration_minutes: Math.min(
        240,
        Math.max(1, body.expected_duration_minutes ?? 10),
      ),
      client_timezone:
        body.client_timezone ??
        Intl.DateTimeFormat().resolvedOptions().timeZone ??
        'America/Lima',
      client_timezone_offset_minutes:
        body.client_timezone_offset_minutes ?? -new Date().getTimezoneOffset(),
      client_language: (
        body.client_language ??
        getRequestLanguage()
      ).slice(0, 20),
      screen_width: Math.min(
        16_384,
        Math.max(240, body.screen_width ?? window.screen.width),
      ),
      screen_height: Math.min(
        16_384,
        Math.max(240, body.screen_height ?? window.screen.height),
      ),
      screen_pixel_ratio: Math.min(
        10,
        Math.max(
          0.5,
          Number(body.screen_pixel_ratio ?? window.devicePixelRatio ?? 1),
        ),
      ),
      browser: (body.browser ?? navigator.userAgent).slice(0, 100),
      operating_system: (
        body.operating_system ??
        navigator.platform
      ).slice(0, 100),
      device_type: body.device_type ?? 'desktop',
      collector_version: body.collector_version ?? 'frontend-v1',
    }
    return apiRequest<SessionStartResponse>({
      path: '/research/sessions/start',
      method: 'POST',
      body: fullBody,
    })
  },
  listSessions: () =>
    apiRequest<PaginatedResponse<ExperimentalSession>>({
      path: '/research/sessions?page_size=100',
    }),
  getSession: (id: string) =>
    apiRequest<ExperimentalSession>({ path: `/research/sessions/${id}` }),
  sendBatch: (sessionId: string, batch: BehavioralBatch) =>
    apiRequest<BehavioralBatchResponse>({
      path: `/research/sessions/${sessionId}/behavior-batches`,
      method: 'POST',
      body: batch,
    }),
  sendCapture: async (
    sessionId: string,
    capture: {
      image: Blob
      capturedAt: string
      sequenceNumber: number
      width: number
      height: number
    },
  ) => {
    if (
      !Number.isInteger(capture.sequenceNumber) ||
      capture.sequenceNumber < 1 ||
      !Number.isInteger(capture.width) ||
      !Number.isInteger(capture.height) ||
      capture.width < 64 ||
      capture.width > 8192 ||
      capture.height < 64 ||
      capture.height > 8192
    ) {
      throw new ApiRequestError(
        'La captura no cumple las dimensiones permitidas.',
        {
          code: 'INVALID_CAPTURE_DIMENSIONS',
          status: 422,
        },
      )
    }

    const form = new FormData()
    form.append('image', capture.image, `capture-${capture.sequenceNumber}.webp`)
    form.append('captured_at', capture.capturedAt)
    form.append('sequence_number', String(capture.sequenceNumber))
    form.append('width', String(capture.width))
    form.append('height', String(capture.height))
    form.append('visibility_state', document.visibilityState)
    form.append(
      'client_timezone_offset',
      String(-new Date().getTimezoneOffset()),
    )
    form.append('capture_source', 'webcam')
    form.append('camera_facing_mode', 'user')
    return apiRequest<FacialCaptureResponse>({
      path: `/research/sessions/${sessionId}/face-captures`,
      method: 'POST',
      body: form,
    })
  },
  finish: (sessionId: string, errorCount: number) =>
    apiRequest<SessionMutationResponse>({
      path: `/research/sessions/${sessionId}/finish`,
      method: 'POST',
      body: {
        client_ended_at: new Date().toISOString(),
        client_error_count: errorCount,
      },
    }),
  cancel: (sessionId: string, reason: string) =>
    apiRequest<SessionMutationResponse>({
      path: `/research/sessions/${sessionId}/cancel`,
      method: 'POST',
      body: { reason },
    }),
  annotate: (
    sessionId: string,
    annotation: ExperimentalSessionAnnotation,
  ) =>
    apiRequest<ExperimentalSession>({
      path: `/research/sessions/${sessionId}/annotation`,
      method: 'PATCH',
      body: {
        ...annotation,
        operator_change_at: annotation.operator_change_at || null,
        source_device: annotation.source_device?.trim().slice(0, 100) || null,
        pad_source_id: annotation.pad_source_id?.trim().slice(0, 100) || null,
        annotation_notes:
          annotation.annotation_notes?.trim().slice(0, 500) || null,
      },
    }),
}

export type { CollectorConfiguration }
