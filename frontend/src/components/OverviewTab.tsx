import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from 'recharts'
import type { TickerDetail } from '../types'
import { OverlayBadge } from './OverlayBadge'
import { V2ActionBadge } from './V2ActionBadge'
import { fmtPrice, fmtPct, fmtPctRaw, fmtMultiple, fmtRsi, fmtLargeNumber, signClass } from '../utils/formatters'

function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-surface rounded-lg p-4 border border-border">
      <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-1">{label}</p>
      <p className="font-mono text-xl font-semibold text-ink">{value}</p>
      {sub && <p className="text-[11px] text-ink-3 mt-0.5">{sub}</p>}
    </div>
  )
}

function SignalRow({ label, value }: { label: string; value: string | null }) {
  const colors: Record<string, string> = {
    UPTREND: 'text-emerald-700', DOWNTREND: 'text-red-700', FLAT: 'text-ink-3',
    BULLISH: 'text-emerald-700', OVERBOUGHT: 'text-amber-700', OVERSOLD: 'text-red-700', NEUTRAL: 'text-ink-3',
    BREAKING_OUT: 'text-emerald-700', BREAKING_DOWN: 'text-red-700', RANGE: 'text-ink-3',
    LEADING: 'text-emerald-700', LAGGING: 'text-red-700', IN_LINE: 'text-ink-3',
  }
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
      <span className="text-xs text-ink-2">{label}</span>
      <span className={`text-xs font-mono font-semibold ${value ? colors[value] || 'text-ink-3' : 'text-ink-4'}`}>
        {value || '—'}
      </span>
    </div>
  )
}

export function OverviewTab({ detail }: { detail: TickerDetail }) {
  const { market, fundamentals, technicals, scores } = detail
  const overlay = scores.technical_overlay
  const v2 = scores.v2_signal
  const history = market.price_history_30d

  const pe = fundamentals.trailing_pe && fundamentals.trailing_pe > 0 ? fundamentals.trailing_pe : null
  const growth = fundamentals.revenue_growth_yoy
  const margin = fundamentals.gross_margin
  const rsi = technicals.rsi_14

  return (
    <div className="p-6 space-y-6">
      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard label="Price" value={fmtPrice(market.current_price)} sub={`Mkt cap ${fmtLargeNumber(market.market_cap)}`} />
        <KpiCard label="Revenue Growth" value={fmtPct(growth)} sub={fundamentals.gross_margin_trend ? `Margin ${fundamentals.gross_margin_trend}` : undefined} />
        <KpiCard label="Gross Margin" value={fmtPctRaw(margin)} sub={pe != null ? `P/E ${fmtMultiple(pe)}` : 'P/E N/A'} />
        <KpiCard label="RSI-14" value={fmtRsi(rsi)} sub={technicals.momentum_signal || undefined} />
      </div>

      {/* Sparkline */}
      {history.length > 0 ? (
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-2">30-Day Price</p>
          <div className="h-28 bg-surface rounded-lg border border-border px-2 py-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <YAxis domain={['auto', 'auto']} hide />
                <Tooltip
                  formatter={(v) => [fmtPrice(v as number), 'Close']}
                  labelFormatter={(l) => l}
                  contentStyle={{ fontSize: 11, fontFamily: 'IBM Plex Mono', background: '#fff', border: '1px solid #e5e3df', borderRadius: 4 }}
                />
                <Line type="monotone" dataKey="close" stroke="#0f766e" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="h-20 bg-surface rounded-lg border border-border flex items-center justify-center">
          <p className="text-xs text-ink-4 font-mono">No price history available</p>
        </div>
      )}

      {/* Technical overlay */}
      {overlay && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3">Technical Overlay</p>
            <OverlayBadge rating={overlay.overlay_rating} />
          </div>
          <div className="bg-surface rounded-lg border border-border px-4 py-1">
            <SignalRow label="Trend (SMA50 vs SMA200)" value={technicals.trend_signal} />
            <SignalRow label="Momentum (RSI-14)" value={technicals.momentum_signal} />
            <SignalRow label="Breakout (52w range)" value={technicals.breakout_signal} />
            <SignalRow label="Relative Strength (vs SPY)" value={technicals.rs_signal} />
          </div>
        </div>
      )}

      {/* V2 Strategy signal */}
      {v2 && v2.v2_action && (
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-3">V2 Strategy</p>
          <div className="bg-surface rounded-lg border border-border px-4 py-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-ink-2">Action</span>
              <V2ActionBadge action={v2.v2_action} />
            </div>
            {detail.stock_class && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-ink-2">Class</span>
                <span className="text-xs font-mono text-ink-2">{detail.stock_class}</span>
              </div>
            )}
            {detail.macro_state && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-ink-2">Macro</span>
                <span className={`text-xs font-mono font-semibold ${detail.macro_state === 'RISK_ON' ? 'text-emerald-700' : detail.macro_state === 'RISK_OFF' ? 'text-red-700' : 'text-ink-3'}`}>
                  {detail.macro_state}
                </span>
              </div>
            )}
            {v2.v2_rationale && (
              <p className="text-[11px] text-ink-3 pt-1 border-t border-border">{v2.v2_rationale}</p>
            )}
          </div>
        </div>
      )}

      {/* Additional fundamentals */}
      <div>
        <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-3">Fundamentals</p>
        <div className="bg-surface rounded-lg border border-border px-4 py-1">
          <div className="flex items-center justify-between py-1.5 border-b border-border">
            <span className="text-xs text-ink-2">Upside to consensus</span>
            <span className={`text-xs font-mono font-semibold ${signClass(fundamentals.upside_to_consensus)}`}>
              {fmtPct(fundamentals.upside_to_consensus)}
            </span>
          </div>
          <div className="flex items-center justify-between py-1.5 border-b border-border">
            <span className="text-xs text-ink-2">Analyst target (mean)</span>
            <span className="text-xs font-mono text-ink-2">{fmtPrice(fundamentals.target_mean_price)} ({fundamentals.analyst_count ?? '?'} analysts)</span>
          </div>
          <div className="flex items-center justify-between py-1.5 border-b border-border">
            <span className="text-xs text-ink-2">Cash runway</span>
            <span className="text-xs font-mono text-ink-2">
              {fundamentals.cash_runway_months === 'profitable' ? 'Profitable' : fundamentals.cash_runway_months != null ? `${fundamentals.cash_runway_months}mo` : '—'}
            </span>
          </div>
          <div className="flex items-center justify-between py-1.5">
            <span className="text-xs text-ink-2">ARK conviction</span>
            <span className="text-xs font-mono text-ink-2">{detail.ark.conviction_level || '—'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
