import type { Rating } from '../types'

const CONFIG: Record<Rating, string> = {
  'STRONG BUY': 'text-emerald-700 border-emerald-300 bg-emerald-50',
  'BUY':        'text-teal-700 border-teal-300 bg-teal-50',
  'HOLD':       'text-ink-3 border-border bg-surface',
  'SELL':       'text-red-700 border-red-300 bg-red-50',
}

export function RatingPill({ rating }: { rating: Rating | null }) {
  if (!rating) return <span className="text-xs text-ink-4">—</span>
  return (
    <span className={`inline-block text-[10px] font-sans font-semibold border rounded px-1.5 py-0.5 uppercase tracking-wide ${CONFIG[rating]}`}>
      {rating}
    </span>
  )
}
