export function fmtPrice(val: number | null | undefined): string {
  if (val == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(val)
}

export function fmtLargeNumber(val: number | null | undefined): string {
  if (val == null) return '—'
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`
  return fmtPrice(val)
}

export function fmtPct(val: number | null | undefined, decimals = 1): string {
  if (val == null) return '—'
  return `${val >= 0 ? '+' : ''}${(val * 100).toFixed(decimals)}%`
}

export function fmtPctRaw(val: number | null | undefined, decimals = 1): string {
  if (val == null) return '—'
  return `${(val * 100).toFixed(decimals)}%`
}

export function fmtMultiple(val: number | null | undefined): string {
  if (val == null) return '—'
  if (val < 0) return 'N/A'
  return `${val.toFixed(1)}x`
}

export function fmtRsi(val: number | null | undefined): string {
  if (val == null) return '—'
  return val.toFixed(1)
}

export function fmtDate(val: string | null | undefined): string {
  if (!val) return '—'
  return val
}

export function signClass(val: number | null | undefined): string {
  if (val == null) return 'text-ink-3'
  return val >= 0 ? 'text-emerald-700' : 'text-red-700'
}
