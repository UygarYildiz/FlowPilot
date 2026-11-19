const sameDay = new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit' })
const otherDay = new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'short' })
const full = new Intl.DateTimeFormat('tr-TR', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

export function shortTime(iso: string, now = new Date()): string {
  const date = new Date(iso)
  return date.toDateString() === now.toDateString() ? sameDay.format(date) : otherDay.format(date)
}

export function fullTime(iso: string): string {
  return full.format(new Date(iso))
}

export function percent(value: number): string {
  return `%${Math.round(value * 100)}`
}

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/** "Mert Özkan <x@y>" yerine adresin yerel kısmından okunur bir gönderen adı. */
export function senderLabel(address: string): { name: string; domain: string } {
  const [local, domain = ''] = address.split('@')
  return { name: local, domain }
}
