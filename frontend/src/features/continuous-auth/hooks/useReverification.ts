import { useContinuousAuth } from './useContinuousAuth'

export function useReverification() {
  const {
    isReverificationOpen,
    isReverifying,
    requestReverification,
    closeReverification,
    reverify,
  } = useContinuousAuth()

  return {
    isOpen: isReverificationOpen,
    isSubmitting: isReverifying,
    open: requestReverification,
    close: closeReverification,
    submit: reverify,
  }
}
