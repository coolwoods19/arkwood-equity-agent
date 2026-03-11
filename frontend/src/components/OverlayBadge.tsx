import type { OverlayRating } from '../types'

const CONFIG: Record<OverlayRating, { label: string; className: string }> = {
  STRONG_SETUP: { label: 'Strong Setup', className: 'bg-emerald-100 text-emerald-700' },
  SETUP:        { label: 'Setup',        className: 'bg-teal-100 text-teal-700' },
  NEUTRAL:      { label: 'Neutral',      className: 'bg-slate-100 text-slate-500' },
  AVOID:        { label: 'Avoid',        className: 'bg-red-100 text-red-700' },
  EXTENDED:     { label: 'Extended',     className: 'bg-amber-100 text-amber-700 pulse-ring' },
}

export function OverlayBadge({ rating, small }: { rating: OverlayRating | null; small?: boolean }) {
  if (!rating) return null
  const { label, className } = CONFIG[rating] || CONFIG.NEUTRAL
  const size = small ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5'
  return (
    <span className={`inline-block font-mono font-medium rounded uppercase tracking-wide ${size} ${className}`}>
      {label}
    </span>
  )
}
