import { useState, useEffect } from 'react'
import type { TickerDetail } from '../types'
import { OverlayBadge } from './OverlayBadge'
import { RatingPill } from './RatingPill'
import { OverviewTab } from './OverviewTab'
import { ThesisTab } from './ThesisTab'
import { ScoresTab } from './ScoresTab'
import { fmtPrice, fmtPct, signClass } from '../utils/formatters'

type Tab = 'overview' | 'thesis' | 'scores'

interface Props {
  ticker: string | null
}

export function DetailPanel({ ticker }: Props) {
  const [detail, setDetail] = useState<TickerDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('overview')

  useEffect(() => {
    if (!ticker) { setDetail(null); return }
    setLoading(true)
    setError(null)
    fetch(`/api/ticker/${ticker}`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json() })
      .then((data) => { setDetail(data); setLoading(false) })
      .catch((e) => { setError(e.message); setLoading(false) })
  }, [ticker])

  if (!ticker) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg">
        <div className="text-center">
          <p className="font-serif text-2xl text-ink-3 mb-2">ARKWOOD FIU</p>
          <p className="text-sm text-ink-4">Select a holding or watchlist item to begin analysis</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-ink-3 font-mono animate-pulse">Loading {ticker}…</p>
      </div>
    )
  }

  if (error || !detail) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-red-700 font-mono">Error loading {ticker}: {error}</p>
      </div>
    )
  }

  const h = detail.holding
  const pnlPct = h && h.avg_cost && detail.market.current_price
    ? (detail.market.current_price - h.avg_cost) / h.avg_cost
    : null

  const TABS: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'thesis', label: 'Thesis' },
    { id: 'scores', label: 'Scores' },
  ]

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-bg">
      {/* Header */}
      <div className="px-6 pt-5 pb-0 border-b border-border">
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="font-mono font-bold text-2xl text-ink tracking-wide">{detail.ticker}</h1>
              <RatingPill rating={detail.rating} />
              <OverlayBadge rating={detail.scores.technical_overlay?.overlay_rating ?? null} />
              {detail.data_quality !== 'FULL' && (
                <span className="text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded">
                  {detail.data_quality} DATA
                </span>
              )}
            </div>
            <p className="text-sm text-ink-2 font-sans">{detail.market.sector} · {detail.market.industry || detail.market.sector}</p>
          </div>
          <div className="text-right">
            <p className="font-mono text-2xl font-semibold text-ink">{fmtPrice(detail.market.current_price)}</p>
            {pnlPct != null && (
              <p className={`font-mono text-sm ${signClass(pnlPct)}`}>
                {fmtPct(pnlPct)} vs cost
              </p>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-0 -mb-px">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-xs font-sans font-medium border-b-2 transition-colors ${
                tab === t.id
                  ? 'border-ink text-ink'
                  : 'border-transparent text-ink-3 hover:text-ink-2'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'overview' && <OverviewTab detail={detail} />}
        {tab === 'thesis' && <ThesisTab ticker={detail.ticker} markdown={detail.thesis_markdown} />}
        {tab === 'scores' && <ScoresTab scores={detail.scores} />}
      </div>
    </div>
  )
}
