import type { Holding, WatchlistItem } from '../types'
import { OverlayBadge } from './OverlayBadge'
import { V2ActionBadge } from './V2ActionBadge'
import { fmtPrice, fmtPct, signClass } from '../utils/formatters'

interface Props {
  holdings: Holding[]
  watchlist: WatchlistItem[]
  selected: string | null
  onSelect: (ticker: string) => void
}

export function Sidebar({ holdings, watchlist, selected, onSelect }: Props) {
  return (
    <aside className="w-56 flex-shrink-0 border-r border-border bg-bg flex flex-col overflow-y-auto">
      {/* Portfolio section */}
      <div className="px-3 pt-4 pb-1">
        <p className="text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-3">
          Portfolio <span className="ml-1 text-ink-4">({holdings.length})</span>
        </p>
      </div>

      {holdings.map((h) => {
        const isSelected = h.ticker === selected
        return (
          <button
            key={h.ticker}
            onClick={() => onSelect(h.ticker)}
            className={`w-full text-left px-3 py-2.5 border-b border-border transition-colors ${
              isSelected ? 'bg-surface' : 'hover:bg-surface/60'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono font-semibold text-sm text-ink tracking-wide flex items-center gap-1">
                {h.ticker}
                {h.alert_triggered && (
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" title={`Alert: price ${h.alert_direction === 'BELOW' ? 'below' : 'above'} threshold`} />
                )}
                {h.stock_class && (
                  <span className="text-[9px] font-mono text-ink-4 border border-border rounded px-1">{h.stock_class}</span>
                )}
              </span>
              <V2ActionBadge action={h.v2_action} small />
            </div>

            <div className="flex items-center justify-between">
              <OverlayBadge rating={h.overlay_rating} small />
              <span className={`font-mono text-[11px] ${signClass(h.unrealized_pnl_pct)}`}>
                {fmtPct(h.unrealized_pnl_pct)}
              </span>
            </div>

            {h.current_price != null && (
              <p className="text-[11px] text-ink-3 font-mono mt-0.5">{fmtPrice(h.current_price)}</p>
            )}
          </button>
        )
      })}

      {/* Watchlist section */}
      <div className="px-3 pt-4 pb-1">
        <p className="text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-3">
          Watchlist <span className="ml-1 text-ink-4">({watchlist.length})</span>
        </p>
      </div>

      {watchlist.map((w) => {
        const isSelected = w.ticker === selected
        return (
          <button
            key={w.ticker}
            onClick={() => onSelect(w.ticker)}
            className={`w-full text-left px-3 py-2.5 border-b border-border transition-colors ${
              isSelected ? 'bg-surface' : 'hover:bg-surface/60'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono font-semibold text-sm text-ink tracking-wide">{w.ticker}</span>
              <span className="text-[10px] text-ink-4">Watching</span>
            </div>
            <div className="flex items-center justify-between">
              <OverlayBadge rating={w.overlay_rating} small />
              {w.current_price != null && (
                <span className="font-mono text-[11px] text-ink-3">{fmtPrice(w.current_price)}</span>
              )}
            </div>
            <p className="text-[10px] text-ink-4 mt-0.5 truncate">{w.why_watching}</p>
          </button>
        )
      })}

      <div className="flex-1" />
    </aside>
  )
}
