const dateFormatter = new Intl.DateTimeFormat('es-PE', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return 'No disponible'
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? 'No disponible'
    : dateFormatter.format(date)
}

export function maskIpAddress(value: string | null): string {
  if (!value) {
    return 'No disponible'
  }

  if (value.includes(':')) {
    const parts = value.split(':').filter(Boolean)
    return `${parts.slice(0, 3).join(':')}:…`
  }

  const octets = value.split('.')
  return octets.length === 4
    ? `${octets[0]}.${octets[1]}.***.***`
    : 'Dirección protegida'
}
