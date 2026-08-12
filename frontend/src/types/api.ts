export interface ApiErrorResponse {
  success: boolean
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export interface ValidationIssue {
  loc: Array<string | number>
  msg: string
  type: string
}

export class ApiError extends Error {
  readonly code: string
  readonly status: number | null
  readonly details?: unknown

  constructor(
    message: string,
    options: {
      code: string
      status?: number | null
      details?: unknown
    },
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = options.code
    this.status = options.status ?? null
    this.details = options.details
  }
}

export { ApiError as ApiRequestError }
