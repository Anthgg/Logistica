import { describe, expect, it, vi } from 'vitest'
import {
  containsSensitiveField,
  KeyboardTimingCollector,
  makeBatch,
  mouseBehaviorEvent,
  retryWithBackoff,
} from './telemetry'

describe('telemetría de comportamiento', () => {
  it('calcula tiempos sin emitir tecla, code, texto ni objetivo', () => {
    const input = document.createElement('input')
    input.value = 'dato-privado'
    let sequence = 1
    const collector = new KeyboardTimingCollector(() => sequence++)
    const down = new KeyboardEvent('keydown', {
      key: 'S',
      code: 'KeyS',
    })
    const up = new KeyboardEvent('keyup', {
      key: 'S',
      code: 'KeyS',
    })
    Object.defineProperty(down, 'target', { value: input })
    Object.defineProperty(up, 'target', { value: input })

    expect(collector.handle(down, 1_000)).toBeNull()
    const result = collector.handle(up, 1_120)

    expect(result).toMatchObject({
      type: 'keyboard',
      event: 'timing',
      sequence_index: 1,
      category: 'alphanumeric',
      dwell_time_ms: 120,
      is_backspace: false,
      is_modifier: false,
    })
    expect(containsSensitiveField(result)).toBe(false)
    expect(JSON.stringify(result)).not.toContain('dato-privado')
    expect(JSON.stringify(result)).not.toContain('KeyS')
  })

  it('ignora campos de contraseña, correo y contraseñas visibles', () => {
    let sequence = 1
    const collector = new KeyboardTimingCollector(() => sequence++)
    for (const type of ['password', 'email']) {
      const input = document.createElement('input')
      input.type = type
      const event = new KeyboardEvent('keydown', { key: 'x' })
      Object.defineProperty(event, 'target', { value: input })
      expect(collector.handle(event, 1_000)).toBeNull()
    }
    const revealedPassword = document.createElement('input')
    revealedPassword.type = 'text'
    revealedPassword.dataset.privateInput = 'true'
    const event = new KeyboardEvent('keydown', { key: 'x' })
    Object.defineProperty(event, 'target', { value: revealedPassword })
    expect(collector.handle(event, 1_000)).toBeNull()
    expect(sequence).toBe(1)
  })

  it('normaliza el mouse y calcula delta, distancia y velocidad', () => {
    const event = new MouseEvent('mousemove', {
      clientX: window.innerWidth * 2,
      clientY: -20,
    })
    const result = mouseBehaviorEvent(
      event,
      'move',
      2,
      { x: 0, y: 0, at: 1_000 },
      2_000,
    ).behavior

    expect(result.normalized_x).toBe(1)
    expect(result.normalized_y).toBe(0)
    expect(result.sequence_index).toBe(2)
    expect(result.distance).toBeGreaterThan(0)
    expect(result.velocity).toBeGreaterThan(0)
    expect(containsSensitiveField(result)).toBe(false)
  })

  it('crea lotes idempotentes con UUID y secuencia', () => {
    const batch = makeBatch([
      {
        type: 'mouse',
        event: 'click',
        timestamp: '2026-07-23T00:00:00.000Z',
        sequence_index: 1,
        normalized_x: 0.5,
        normalized_y: 0.5,
        delta_x: 0,
        delta_y: 0,
        distance: 0,
        velocity: 0,
        button_category: 'primary',
        scroll_delta: 0,
      },
    ], 4)
    expect(batch.batch_id).toMatch(/^[0-9a-f-]{36}$/i)
    expect(batch.sequence_number).toBe(4)
  })

  it('reintenta el mismo trabajo con espera incremental', async () => {
    vi.useFakeTimers()
    const operation = vi
      .fn<() => Promise<string>>()
      .mockRejectedValueOnce(new Error('uno'))
      .mockRejectedValueOnce(new Error('dos'))
      .mockResolvedValue('ok')
    const promise = retryWithBackoff(operation, 3, [10, 20, 30])
    await vi.runAllTimersAsync()
    await expect(promise).resolves.toBe('ok')
    expect(operation).toHaveBeenCalledTimes(3)
    vi.useRealTimers()
  })
})
