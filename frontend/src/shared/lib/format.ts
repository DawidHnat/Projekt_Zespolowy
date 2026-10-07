const numberFormatter = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 })
const dateFormatter = new Intl.DateTimeFormat('pl-PL', {
  timeZone: 'Europe/Warsaw',
  day: '2-digit',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

export function formatNumber(value: number | null | undefined) {
  return value == null ? '—' : numberFormatter.format(value)
}

export function formatDate(value: string | null | undefined) {
  if (!value) return 'W trakcie'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateFormatter.format(date)
}
