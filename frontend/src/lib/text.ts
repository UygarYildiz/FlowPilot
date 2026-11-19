// Ekrandaki sabit metinler tek yerde: panel dili değişirse yalnızca bu dosya çevrilir.
import type { Counts, EmailStatus, Priority, ProposalStatus } from './api'

export const priorityLabel: Record<Priority, string> = {
  low: 'Düşük',
  normal: 'Normal',
  high: 'Yüksek',
  urgent: 'Acil',
}

export const statusLabel: Record<EmailStatus, string> = {
  received: 'Sınıflandırılmayı bekliyor',
  classifying: 'Sınıflandırılıyor',
  routed: 'Yönlendirildi',
  needs_review: 'İnceleme bekliyor',
  processing: 'İşleniyor',
  awaiting_approval: 'Onay bekliyor',
  done: 'Kapandı',
}

const actionLabel: Record<string, string> = {
  'email.received': 'E-posta alındı',
  'email.duplicate_ignored': 'Aynı e-posta tekrar geldi, yeni kayıt açılmadı',
  'email.classified': 'Yapay zekâ yönlendirdi',
  'email.rerouted': 'Yönlendirme düzeltildi',
  'email.dismissed': 'İlgisiz olarak kapatıldı',
  'route.done': 'Departman işi kapattı',
  'users.demo_ensured': 'Demo kullanıcıları hazırlandı',
  'agent.ran': 'Ajan e-postayı inceledi',
  'agent.failed': 'Ajan çalışamadı',
  'proposal.created': 'Ajan öneri hazırladı',
  'proposal.approved': 'Öneri onaylandı',
  'proposal.rejected': 'Öneri reddedildi',
  'proposal.executed': 'Öneri uygulandı',
  'proposal.failed': 'Öneri uygulanırken hata oldu',
}

export const proposalStatusLabel: Record<ProposalStatus, string> = {
  pending: 'Onay bekliyor',
  approved: 'Onaylandı, uygulanıyor',
  rejected: 'Reddedildi',
  executed: 'Uygulandı',
  failed: 'Uygulanamadı',
}

export function describeAction(action: string): string {
  return actionLabel[action] ?? action
}

export function describeActor(actor: string): string {
  if (actor === 'system') return 'Sistem'
  if (actor.startsWith('user:')) return actor.slice(5)
  if (actor.startsWith('decision_engine:')) return `Yapay zekâ (${actor.split(':').slice(1).join(':')})`
  if (actor.startsWith('agent:')) return `Ajan (${actor.slice(6)})`
  return actor
}

export const UNKNOWN = 'unknown'

export function departmentName(counts: Counts | undefined, key: string): string {
  if (key === UNKNOWN) return 'Hiçbir departman'
  return counts?.departments.find((d) => d.key === key)?.name ?? key
}

export function intentLabel(counts: Counts | undefined, department: string, intent: string | null) {
  if (!intent) return 'İlgisiz ya da belirsiz'
  const found = counts?.departments
    .find((d) => d.key === department)
    ?.intents.find((i) => i.key === intent)
  return found?.label ?? intent
}

export function deptColor(key: string): string {
  return `var(--color-dept-${key}, var(--color-dept-unknown))`
}

// Öneri verisindeki alan adlarının okunur karşılıkları (bilinmeyen ad olduğu gibi gösterilir).
const FIELD_LABELS: Record<string, string> = {
  source_filename: 'Belge',
  supplier: 'Tedarikçi',
  quote_no: 'Teklif no',
  request_no: 'Talep no',
  currency: 'Para birimi',
  valid_until: 'Geçerlilik',
  lines: 'Satırlar',
  subtotal: 'Ara toplam',
  vat: 'KDV',
  total: 'Genel toplam',
  product_code: 'Kod',
  description: 'Ürün',
  quantity: 'Miktar',
  unit: 'Birim',
  unit_price: 'Birim fiyat',
  line_total: 'Tutar',
  lead_time_days: 'Teslim (gün)',
  reasoning: 'Gerekçe',
  fx_note: 'Kur notu',
  chosen: 'Seçilen teklif',
  alternatives: 'Alternatifler',
  line_total_try: 'Tutar (TRY)',
  unit_price_try: 'Birim fiyat (TRY)',
}

export function fieldLabel(key: string): string {
  return FIELD_LABELS[key] ?? key
}

const FIELD_ORDER = Object.keys(FIELD_LABELS)

/** Alanları sözlükteki sıraya koyar (veritabanı JSON anahtar sırasını korumaz); bilinmeyenler sonda. */
export function byFieldOrder(a: string, b: string): number {
  const rank = (k: string) => (FIELD_ORDER.includes(k) ? FIELD_ORDER.indexOf(k) : FIELD_ORDER.length)
  return rank(a) - rank(b)
}
