import { describe, expect, it } from 'vitest'
import { ApiError } from '../types/api'
import { getErrorMessage } from './errors'

describe('mensajes de error del backend', () => {
  it.each([401, 403, 409, 413, 415, 422, 429])(
    'presenta error.message sin traducir para HTTP %i',
    (status) => {
    const backendMessage = `Mensaje localizado ${status}`
    const message = getErrorMessage(
      new ApiError(backendMessage, {
        code: `HTTP_${status}`,
        status,
      }),
    )
    expect(message).toBe(backendMessage)
    },
  )
})
