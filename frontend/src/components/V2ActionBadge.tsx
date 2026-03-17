import type { V2Action } from '../types'

const CONFIG: Partial<Record<V2Action, { label: string; className: string }>> = {
  SELL:         { label: 'SELL',       className: 'bg-red-100 text-red-700 border-red-300' },
  WATCH_EXIT:   { label: 'WATCH EXIT', className: 'bg-red-50 text-red-600 border-red-200' },
  RISK_OFF_HOLD:{ label: 'RISK OFF',   className: 'bg-orange-100 text-orange-700 border-orange-300' },
  HOLD_EXTENDED:{ label: 'EXTENDED',   className: 'bg-amber-100 text-amber-700 border-amber-300' },
  ADD:          { label: 'ADD',        className: 'bg-emerald-100 text-emerald-700 border-emerald-300' },
  WAIT:         { label: 'WAIT',       className: 'bg-slate-100 text-slate-500 border-slate-300' },
  HOLD:         { label: 'HOLD',       className: 'bg-slate-100 text-slate-400 border-slate-200' },
  DATA_MISSING: { label: 'NO DATA',    className: 'bg-slate-50 text-slate-400 border-slate-200' },
}

export function V2ActionBadge({ action, small }: { action: V2Action | null; small?: boolean }) {
  if (!action) return <span className="text-xs text-ink-4">—</span>
  const cfg = CONFIG[action] ?? { label: action, className: 'bg-slate-100 text-slate-500 border-slate-200' }
  const size = small ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5'
  return (
    <span className={`inline-block font-mono font-semibold border rounded uppercase tracking-wide ${size} ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}
