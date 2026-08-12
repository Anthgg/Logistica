export function normalizeComponentName(name: string): string {
  const normalized = name.trim().toLowerCase()

  if (normalized.includes('pad') || normalized.includes('presence')) {
    return 'PAD'
  }

  if (normalized.includes('behavior') || normalized.includes('conduct')) {
    return 'Conductual'
  }

  if (normalized.includes('facial') || normalized.includes('face')) {
    return 'Facial'
  }

  return name
}
