import { useCallback, useState } from 'react'
import { getErrorMessage } from '../utils/errors'

export function useAsyncAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
) {
  const [isPending, setIsPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(
    async (...args: TArgs): Promise<TResult | undefined> => {
      if (isPending) {
        return undefined
      }

      setIsPending(true)
      setError(null)

      try {
        return await action(...args)
      } catch (caughtError: unknown) {
        setError(getErrorMessage(caughtError))
        return undefined
      } finally {
        setIsPending(false)
      }
    },
    [action, isPending],
  )

  return {
    execute,
    isPending,
    error,
    clearError: () => setError(null),
  }
}
