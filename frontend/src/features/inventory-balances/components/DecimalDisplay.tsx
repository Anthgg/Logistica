import type { DecimalValue } from '../types/inventory-balances'

export function DecimalDisplay({
  value,
  className,
}: {
  value: DecimalValue
  className?: string
}) {
  const formatted = formatDecimal(value)
  return (
    <span className={className} title={`${value.value} (escala ${value.scale})`}>
      {formatted}
    </span>
  )
}

function formatDecimal(d: DecimalValue): string {
  const num = d.value
  const scale = d.scale
  if (scale === 0) return num.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  const intPart = num.slice(0, -scale) || '0'
  const decPart = num.slice(-scale)
  const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return `${formattedInt}.${decPart}`
}
