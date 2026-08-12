const TIME_FMT = new Intl.DateTimeFormat('es-PE', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: true,
})

const DAY_FMT = new Intl.DateTimeFormat('es-PE', { weekday: 'long' })

const FULL_FMT = new Intl.DateTimeFormat('es-PE', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: true,
})

export function formatSessionDate(value: string | null | undefined): string {
  if (!value) return 'No disponible'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No disponible'

  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  const timeStr = TIME_FMT.format(date)

  if (diffDays === 0) {
    return `Hoy, ${timeStr}`
  }

  if (diffDays === 1) {
    return `Ayer, ${timeStr}`
  }

  if (diffDays > 0 && diffDays < 7) {
    const dayName = DAY_FMT.format(date).replace(/^\w/, (c) => c.toUpperCase())
    return `${dayName}, ${timeStr}`
  }

  return FULL_FMT.format(date)
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return 'No disponible'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No disponible'

  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHours = Math.floor(diffMin / 60)

  if (diffSec < 10) return 'Hace unos segundos'
  if (diffMin < 1) return 'Hace menos de un minuto'
  if (diffMin === 1) return 'Hace 1 minuto'
  if (diffMin < 60) return `Hace ${diffMin} minutos`
  if (diffHours === 1) return 'Hace 1 hora'
  if (diffHours < 24) return `Hace ${diffHours} horas`
  if (diffHours < 48) return 'Hace 1 día'
  return `Hace ${Math.floor(diffHours / 24)} días`
}

export function formatExpiry(value: string | null | undefined): string {
  if (!value) return 'No disponible'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No disponible'

  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffMin = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMin / 60)

  if (diffMs < 0) return 'Expirada'

  if (diffMin < 1) return 'Expira en menos de 1 min'
  if (diffMin < 60) return `Expira en ${diffMin} min`
  if (diffHours < 24) return `Expira en ${diffHours} h`

  const days = Math.floor(diffHours / 24)
  return `Expira en ${days} ${days === 1 ? 'día' : 'días'}`
}

export function isExpiringSoon(value: string | null | undefined): boolean {
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false
  const diffMs = date.getTime() - Date.now()
  return diffMs > 0 && diffMs < 15 * 60 * 1000
}

export function isExpired(value: string | null | undefined): boolean {
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false
  return date.getTime() < Date.now()
}