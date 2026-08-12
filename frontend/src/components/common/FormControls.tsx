import { useId, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

export function SelectField({
  label,
  children,
  id,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: ReactNode }) {
  const generated = useId()
  const fieldId = id ?? generated
  return (
    <div className="field">
      <label className="field__label" htmlFor={fieldId}>{label}</label>
      <div className="field__control">
        <select id={fieldId} className="field__input" {...props}>{children}</select>
      </div>
    </div>
  )
}

export function TextareaField({
  label,
  id,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string }) {
  const generated = useId()
  const fieldId = id ?? generated
  return (
    <div className="field">
      <label className="field__label" htmlFor={fieldId}>{label}</label>
      <div className="field__control">
        <textarea id={fieldId} className="field__input field__textarea" {...props} />
      </div>
    </div>
  )
}
