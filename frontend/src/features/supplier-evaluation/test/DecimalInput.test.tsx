import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DecimalInput } from '../components/ui/DecimalInput'

function getInput(): HTMLInputElement {
  return screen.getByRole('textbox') as HTMLInputElement
}

describe('DecimalInput', () => {
  it('mantiene el valor como string sin usar Number para almacenar', () => {
    const onChange = vi.fn()
    render(<DecimalInput value="25.5000" onChange={onChange} label="Peso" />)
    expect(getInput().value).toBe('25.5000')
  })

  it('acepta dígitos y un punto decimal', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<DecimalInput value="1" onChange={onChange} />)
    const input = getInput()
    input.focus()
    await user.keyboard('2')
    expect(onChange).toHaveBeenCalled()
    expect(typeof onChange.mock.calls[0]?.[0]).toBe('string')
  })

  it('rechaza caracteres no decimales', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(<DecimalInput value="1" onChange={onChange} />)
    await user.type(getInput(), 'a')
    // onChange no se llama con 'a' porque el regex la rechaza
    expect(onChange).not.toHaveBeenCalledWith('a')
  })

  it('expone aria-invalid cuando es inválido', () => {
    render(<DecimalInput value="x" onChange={() => {}} invalid label="Peso" />)
    expect(getInput().getAttribute('aria-invalid')).toBe('true')
  })
})