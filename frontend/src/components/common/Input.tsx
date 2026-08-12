import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
} from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: ReactNode
  endAdornment?: ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  function Input(
    {
      label,
      error,
      hint,
      endAdornment,
      id,
      className = '',
      ...props
    },
    ref,
  ) {
    const generatedId = useId()
    const inputId = id ?? generatedId
    const helpId = `${inputId}-help`

    return (
      <div className={`field ${error ? 'field--error' : ''} ${className}`.trim()}>
        <label className="field__label" htmlFor={inputId}>
          {label}
        </label>
        <div className="field__control">
          <input
            ref={ref}
            id={inputId}
            className="field__input"
            aria-invalid={Boolean(error)}
            aria-describedby={error || hint ? helpId : undefined}
            {...props}
          />
          {endAdornment && (
            <div className="field__adornment">{endAdornment}</div>
          )}
        </div>
        {(error || hint) && (
          <div
            id={helpId}
            className={`field__help ${error ? 'field__help--error' : ''}`}
          >
            {error ?? hint}
          </div>
        )}
      </div>
    )
  },
)
