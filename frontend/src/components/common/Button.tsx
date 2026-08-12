import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'small' | 'medium'
  isLoading?: boolean
  loadingLabel?: string
  fullWidth?: boolean
  children: ReactNode
}

const variantClasses = {
  primary:   'bg-primary text-white hover:bg-primary-mid border-transparent',
  secondary: 'bg-white text-ink border-[#DDE4E8] hover:bg-[#F0F4F7] hover:border-[#C8D4DC]',
  danger:    'bg-danger text-white border-transparent hover:brightness-90',
  ghost:     'bg-transparent text-muted border-transparent hover:bg-[#F0F4F7] hover:text-ink',
}

const sizeClasses = {
  small:  'min-h-11 px-3 text-[11px] rounded-lg',
  medium: 'min-h-11 px-3.5 text-xs rounded-lg',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = 'primary',
      size = 'medium',
      isLoading = false,
      loadingLabel = 'Procesando…',
      fullWidth = false,
      disabled,
      className = '',
      children,
      ...props
    },
    ref,
  ) {
    return (
      <button
        ref={ref}
        className={`
          inline-flex items-center justify-center gap-1.5 font-semibold border
          transition-colors duration-150 cursor-pointer font-sans whitespace-nowrap
          focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          ${fullWidth ? 'w-full' : ''}
          ${className}
        `.trim()}
        disabled={Boolean(disabled || isLoading)}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading && (
          <span
            className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"
            aria-hidden="true"
          />
        )}
        <span>{isLoading ? loadingLabel : children}</span>
      </button>
    )
  },
)
