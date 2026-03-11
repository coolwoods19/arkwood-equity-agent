import { useState, useRef, useCallback } from 'react'
import type { PortfolioTotals, RefreshEvent, RefreshComplete } from '../types'
import { fmtPrice, fmtPct, signClass } from '../utils/formatters'

interface Props {
  totals: PortfolioTotals | null
  snapshotDate: string | null
  snapshotDaysOld: number | null
  onRefreshComplete: () => void
}

type LogEntry = { step: string; status: 'running' | 'done' | 'error'; message: string }

export function Header({ totals, snapshotDate, snapshotDaysOld, onRefreshComplete }: Props) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [log, setLog] = useState<LogEntry[]>([])
  const [complete, setComplete] = useState<RefreshComplete | null>(null)
  const esRef = useRef<EventSource | null>(null)

  const startRefresh = useCallback(() => {
    if (refreshing) return
    setLog([])
    setComplete(null)
    setDrawerOpen(true)
    setRefreshing(true)

    const es = new EventSource('/api/refresh/stream')
    esRef.current = es

    es.addEventListener('progress', (e) => {
      const data: RefreshEvent = JSON.parse(e.data)
      setLog((prev) => {
        // Replace running entry with update, or append
        const idx = prev.findIndex((l) => l.step === data.step && l.status === 'running')
        if (idx >= 0) {
          const next = [...prev]
          next[idx] = data
          return next
        }
        return [...prev, data]
      })
    })

    es.addEventListener('complete', (e) => {
      const data: RefreshComplete = JSON.parse(e.data)
      setComplete(data)
      setRefreshing(false)
      es.close()
      onRefreshComplete()
    })

    es.addEventListener('error', (e) => {
      if ('data' in e) {
        const data = JSON.parse((e as MessageEvent).data)
        setLog((prev) => [...prev, { step: data.step, status: 'error', message: data.message }])
        if (data.fatal) { setRefreshing(false); es.close() }
      } else {
        setRefreshing(false)
        es.close()
      }
    })
  }, [refreshing, onRefreshComplete])

  const statusIcon = (status: LogEntry['status']) => {
    if (status === 'running') return <span className="text-amber-600 animate-pulse">●</span>
    if (status === 'done') return <span className="text-emerald-600">✓</span>
    return <span className="text-red-600">✗</span>
  }

  return (
    <>
      <header className="h-12 border-b border-border bg-bg flex items-center px-4 gap-6 flex-shrink-0">
        {/* Brand */}
        <span className="font-serif text-base text-ink tracking-wide">ARKWOOD FIU</span>

        {/* Stale data warning */}
        {snapshotDaysOld != null && snapshotDaysOld > 1 && (
          <span className="text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded">
            Data as of {snapshotDate} ({snapshotDaysOld}d old)
          </span>
        )}

        <div className="flex-1" />

        {/* Portfolio totals */}
        {totals && (
          <div className="flex items-center gap-5 text-right">
            {totals.active_alerts > 0 && (
              <span className="text-[10px] font-mono bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded">
                {totals.active_alerts} ALERT{totals.active_alerts > 1 ? 'S' : ''}
              </span>
            )}
            <div>
              <p className="text-[10px] font-mono text-ink-3 uppercase tracking-wider">Total Value</p>
              <p className="font-mono text-sm font-semibold text-ink">{fmtPrice(totals.total_market_value)}</p>
            </div>
            <div>
              <p className="text-[10px] font-mono text-ink-3 uppercase tracking-wider">P&amp;L</p>
              <p className={`font-mono text-sm font-semibold ${signClass(totals.total_unrealized_pnl_pct)}`}>
                {fmtPct(totals.total_unrealized_pnl_pct)}
              </p>
            </div>
          </div>
        )}

        {/* Refresh button */}
        <button
          onClick={startRefresh}
          disabled={refreshing}
          className="text-[11px] font-mono border border-border bg-surface hover:bg-border text-ink-2 px-3 py-1 rounded transition-colors disabled:opacity-50"
        >
          {refreshing ? 'Refreshing…' : '↻ Refresh'}
        </button>
      </header>

      {/* Refresh drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-end pointer-events-none">
          <div className="pointer-events-auto w-96 mr-4 mb-4 bg-bg border border-border rounded-lg shadow-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface">
              <span className="text-xs font-mono font-semibold text-ink-2 uppercase tracking-widest">Data Refresh</span>
              <button onClick={() => setDrawerOpen(false)} className="text-ink-4 hover:text-ink text-sm leading-none">×</button>
            </div>
            <div className="px-4 py-3 max-h-72 overflow-y-auto space-y-1.5">
              {log.map((entry, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="font-mono text-xs mt-px w-4 flex-shrink-0">{statusIcon(entry.status)}</span>
                  <div>
                    <p className="text-[10px] font-mono text-ink-3 uppercase">{entry.step}</p>
                    <p className="text-xs text-ink-2">{entry.message}</p>
                  </div>
                </div>
              ))}
              {log.length === 0 && <p className="text-xs text-ink-4 font-mono">Starting…</p>}
            </div>
            {complete && (
              <div className={`px-4 py-2 border-t border-border text-xs font-mono ${complete.success ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'}`}>
                {complete.success
                  ? `✓ Done in ${complete.duration_seconds}s${complete.steps_failed.length ? ` (${complete.steps_failed.length} skipped)` : ''}`
                  : '✗ Refresh failed'}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
