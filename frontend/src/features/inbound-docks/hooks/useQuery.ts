import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiRequest } from '../../../api/api-client'
import { getErrorMessage } from '../../../utils/errors'
import { ApiRequestError } from '../../../types/api'

export type QueryKey = readonly unknown[]

export interface QueryState<T> {
  data: T | undefined
  isLoading: boolean
  isFetching: boolean
  isError: boolean
  error: string | null
  errorCode: string | null
  status: number | null
  refetch: () => Promise<void>
  setData: (updater: T | ((previous: T | undefined) => T)) => void
}

export interface QueryOptions {
  enabled?: boolean
  refetchIntervalMs?: number | null
  refetchOnWindowFocus?: boolean
  onError?: (error: ApiRequestError) => void
}

function keysAreEqual(a: QueryKey | undefined, b: QueryKey | undefined): boolean {
  if (a === b) return true
  if (!a || !b) return false
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] !== b[i]) return false
  }
  return true
}

function buildUrl(path: string, params?: Record<string, unknown>): string {
  if (!params) return path
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value == null) continue
    if (value instanceof Date) {
      search.set(key, value.toISOString())
    } else if (Array.isArray(value)) {
      search.set(key, value.join(','))
    } else if (typeof value === 'boolean') {
      search.set(key, String(value))
    } else {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `${path}?${qs}` : path
}

export function useQuery<T>(
  key: QueryKey,
  path: string,
  params?: Record<string, unknown>,
  options: QueryOptions = {},
): QueryState<T> {
  const [data, setData] = useState<T | undefined>(undefined)
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(options.enabled ?? true))
  const [isFetching, setIsFetching] = useState<boolean>(false)
  const [isError, setIsError] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [errorCode, setErrorCode] = useState<string | null>(null)
  const [status, setStatus] = useState<number | null>(null)
  const lastKeyRef = useRef<QueryKey | undefined>(undefined)
  const enabled = options.enabled ?? true
  const paramsRef = useRef<string>('')
  const paramsSnapshot = useMemo(() => JSON.stringify(params ?? {}), [params])
  const pathRef = useRef<string>(path)
  pathRef.current = path

  const fetchData = useCallback(async () => {
    if (!enabled) return
    setIsFetching(true)
    try {
      const url = buildUrl(pathRef.current, params)
      const result = await apiRequest<T>({ path: url, method: 'GET' })
      setData(result)
      setIsError(false)
      setError(null)
      setErrorCode(null)
      setStatus(null)
    } catch (caught) {
      if (caught instanceof ApiRequestError) {
        setIsError(true)
        setError(getErrorMessage(caught))
        setErrorCode(caught.code)
        setStatus(caught.status)
        if (options.onError) options.onError(caught)
      } else {
        setIsError(true)
        setError(getErrorMessage(caught))
      }
    } finally {
      setIsFetching(false)
      setIsLoading(false)
    }
  }, [enabled, params, options])

  useEffect(() => {
    const keyChanged = !keysAreEqual(lastKeyRef.current, key)
    const paramsChanged = paramsRef.current !== paramsSnapshot
    if (keyChanged || paramsChanged) {
      lastKeyRef.current = key
      paramsRef.current = paramsSnapshot
      setIsLoading(Boolean(enabled))
      setData(undefined)
      setIsError(false)
      setError(null)
      setErrorCode(null)
      setStatus(null)
      if (enabled) {
        void fetchData()
      }
    }
  }, [key, paramsSnapshot, enabled, fetchData])

  useEffect(() => {
    if (!options.refetchIntervalMs) return
    const id = window.setInterval(() => {
      void fetchData()
    }, options.refetchIntervalMs)
    return () => window.clearInterval(id)
  }, [options.refetchIntervalMs, fetchData])

  useEffect(() => {
    if (!options.refetchOnWindowFocus) return
    const handler = () => {
      void fetchData()
    }
    window.addEventListener('focus', handler)
    return () => window.removeEventListener('focus', handler)
  }, [options.refetchOnWindowFocus, fetchData])

  const refetch = useCallback(async () => {
    await fetchData()
  }, [fetchData])

  const setDataSafe = useCallback((updater: T | ((previous: T | undefined) => T)) => {
    setData((previous) => (typeof updater === 'function'
      ? (updater as (p: T | undefined) => T)(previous)
      : updater))
  }, [])

  return { data, isLoading, isFetching, isError, error, errorCode, status, refetch, setData: setDataSafe }
}

export function useMutation<TInput, TResult = unknown>(
  action: (input: TInput) => Promise<TResult>,
  options: {
    onSuccess?: (result: TResult, input: TInput) => void
    onError?: (error: ApiRequestError, input: TInput) => void
  } = {},
) {
  const [isPending, setIsPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorCode, setErrorCode] = useState<string | null>(null)
  const [status, setStatus] = useState<number | null>(null)

  const mutate = useCallback(
    async (input: TInput): Promise<TResult | undefined> => {
      setIsPending(true)
      setError(null)
      setErrorCode(null)
      setStatus(null)
      try {
        const result = await action(input)
        if (options.onSuccess) options.onSuccess(result, input)
        return result
      } catch (caught) {
        if (caught instanceof ApiRequestError) {
          setError(getErrorMessage(caught))
          setErrorCode(caught.code)
          setStatus(caught.status)
          if (options.onError) options.onError(caught, input)
        } else {
          setError(getErrorMessage(caught))
        }
        return undefined
      } finally {
        setIsPending(false)
      }
    },
    [action, options],
  )

  return { mutate, isPending, error, errorCode, status, reset: () => {
    setError(null); setErrorCode(null); setStatus(null)
  } }
}
