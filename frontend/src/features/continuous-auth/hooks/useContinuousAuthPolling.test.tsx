import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useContinuousAuthPolling } from './useContinuousAuthPolling'

function setVisibility(value: 'visible' | 'hidden') {
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    value,
  })
  document.dispatchEvent(new Event('visibilitychange'))
}

function PollingHarness({
  onPoll,
  onFailureLimit = () => undefined,
}: {
  onPoll: (signal: AbortSignal) => Promise<void>
  onFailureLimit?: () => void
}) {
  const { isPolling, stopPolling, startPolling } =
    useContinuousAuthPolling({
      enabled: true,
      authenticationLevel: 'continuously_verified',
      nextEvaluationAfter: null,
      hasExperimentalSession: true,
      intervalMs: 1_000,
      maxFailures: 2,
      onPoll,
      onFailureLimit,
    })

  return (
    <div>
      <span>{isPolling ? 'activo' : 'detenido'}</span>
      <button type="button" onClick={stopPolling}>
        Detener
      </button>
      <button type="button" onClick={startPolling}>
        Iniciar
      </button>
    </div>
  )
}

describe('useContinuousAuthPolling', () => {
  afterEach(() => {
    vi.useRealTimers()
    setVisibility('visible')
  })

  it('pausa al ocultar la pestaña y reanuda al volver visible', async () => {
    vi.useFakeTimers()
    setVisibility('visible')
    const onPoll = vi.fn(async () => undefined)
    render(<PollingHarness onPoll={onPoll} />)

    await act(() => vi.advanceTimersByTimeAsync(1_000))
    expect(onPoll).toHaveBeenCalledOnce()

    act(() => setVisibility('hidden'))
    await act(() => vi.advanceTimersByTimeAsync(5_000))
    expect(onPoll).toHaveBeenCalledOnce()
    expect(screen.getByText('detenido')).toBeVisible()

    act(() => setVisibility('visible'))
    await act(() => vi.advanceTimersByTimeAsync(1_000))
    expect(onPoll).toHaveBeenCalledTimes(2)
  })

  it('no solapa solicitudes mientras una sigue pendiente', async () => {
    vi.useFakeTimers()
    setVisibility('visible')
    let resolveRequest: (() => void) | null = null
    const onPoll = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveRequest = resolve
        }),
    )
    render(<PollingHarness onPoll={onPoll} />)

    await act(() => vi.advanceTimersByTimeAsync(5_000))
    expect(onPoll).toHaveBeenCalledOnce()

    await act(async () => {
      resolveRequest?.()
      await Promise.resolve()
    })
    await act(() => vi.advanceTimersByTimeAsync(1_000))
    expect(onPoll).toHaveBeenCalledTimes(2)
  })

  it('se suspende al alcanzar el máximo de fallos', async () => {
    vi.useFakeTimers()
    setVisibility('visible')
    const onFailureLimit = vi.fn()
    const onPoll = vi.fn(async () => {
      throw new Error('network')
    })
    render(
      <PollingHarness
        onPoll={onPoll}
        onFailureLimit={onFailureLimit}
      />,
    )

    await act(() => vi.advanceTimersByTimeAsync(1_000))
    await act(() => vi.advanceTimersByTimeAsync(2_000))

    expect(onPoll).toHaveBeenCalledTimes(2)
    expect(onFailureLimit).toHaveBeenCalledOnce()
    expect(screen.getByText('detenido')).toBeVisible()
  })
})
