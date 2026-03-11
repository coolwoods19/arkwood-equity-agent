import type { Scores } from '../types'
import { OverlayBadge } from './OverlayBadge'

const SCORE_LABELS: Record<string, string> = {
  revenue_growth_over_20pct: 'Revenue Growth >20% YoY',
  expanding_gross_margins: 'Expanding Gross Margins',
  peg_score: '5-Year Forward PEG',
  cash_runway_score: 'Cash Runway >24mo / Profitable',
  upside_to_consensus_score: 'Upside to Consensus >15%',
  ark_conviction_score: 'ARK Conviction',
  news_catalyst_score: 'Recent Catalyst / News',
}

const MANUAL_LABELS: Record<string, string> = {
  tech_moat: 'Clear Tech Moat / Niche Leader',
  s_curve_adoption: 'Steep S-Curve Adoption',
  wrights_law: "Wright's Law / Learning Curve",
  tech_convergence: 'Tech Convergence (multi-platform)',
  disruption_driver: 'Disruption Driver (vs Leverager)',
  below_5yr_peer_avg: 'Below 5yr / Peer Avg Multiples',
}

function ScoreBar({ score, max }: { score: number; max: number }) {
  const pct = max > 0 ? Math.max(0, Math.min(1, score / max)) * 100 : 0
  const color = score >= max * 0.8 ? 'bg-emerald-500' : score > 0 ? 'bg-teal-400' : 'bg-red-300'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs text-ink-2 w-8 text-right">{score > 0 ? `+${score}` : score}</span>
    </div>
  )
}

export function ScoresTab({ scores }: { scores: Scores }) {
  const { auto_scores, auto_total, max_possible_auto, max_possible_total, manual_scores_needed, notes, technical_overlay } = scores

  const scorePct = max_possible_total > 0 ? ((auto_total ?? 0) / max_possible_total) * 100 : 0

  return (
    <div className="p-6 space-y-6">
      {/* Score summary */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <div className="flex items-end justify-between mb-3">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3">TVS Auto Score</p>
            <p className="font-mono text-3xl font-semibold text-ink">{auto_total ?? '—'}<span className="text-base font-normal text-ink-3">/{max_possible_total}</span></p>
          </div>
          <p className="text-xs text-ink-3 font-mono">Auto-scored: {auto_total}/{max_possible_auto}</p>
        </div>
        <div className="h-2 bg-border rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${scorePct >= 80 ? 'bg-emerald-500' : scorePct >= 60 ? 'bg-teal-400' : scorePct >= 40 ? 'bg-amber-400' : 'bg-red-400'}`}
            style={{ width: `${scorePct}%` }}
          />
        </div>
      </div>

      {/* Auto scores */}
      <div>
        <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-3">Auto-Scored Criteria</p>
        <div className="bg-surface rounded-lg border border-border divide-y divide-border">
          {Object.entries(auto_scores).map(([key, score]) => (
            <div key={key} className="px-4 py-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-ink-2">{SCORE_LABELS[key] || key}</span>
              </div>
              <ScoreBar score={score} max={10} />
              {notes[key] && <p className="text-[10px] text-ink-3 mt-1 font-mono">{notes[key]}</p>}
            </div>
          ))}
        </div>
      </div>

      {/* Manual scores */}
      <div>
        <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-3">Analyst-Scored Criteria <span className="text-ink-4">(pending)</span></p>
        <div className="bg-surface rounded-lg border border-border divide-y divide-border">
          {Object.entries(manual_scores_needed).map(([key, val]) => (
            <div key={key} className="px-4 py-3 flex items-center justify-between">
              <span className="text-xs text-ink-2">{MANUAL_LABELS[key] || key}</span>
              {val != null ? (
                <span className="font-mono text-xs text-emerald-700">+{val}</span>
              ) : (
                <span
                  className="inline-block border border-border text-[10px] font-mono text-ink-4 px-1.5 py-0.5 rounded"
                  title="Pending analyst review"
                >
                  ?
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Technical overlay */}
      {technical_overlay && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3">Technical Overlay</p>
            <OverlayBadge rating={technical_overlay.overlay_rating} />
          </div>
          <div className="bg-surface rounded-lg border border-border px-4 py-2 text-xs text-ink-2 font-mono space-y-1">
            <div className="flex justify-between"><span className="text-ink-3">Bullish signals</span><span className="text-emerald-700">{technical_overlay.bullish_signals.join(', ') || 'none'}</span></div>
            <div className="flex justify-between"><span className="text-ink-3">Bearish signals</span><span className="text-red-700">{technical_overlay.bearish_signals.join(', ') || 'none'}</span></div>
            <div className="flex justify-between"><span className="text-ink-3">RSI-14</span><span>{technical_overlay.overlay_notes.rsi_14?.toFixed(1) ?? '—'}</span></div>
            <div className="flex justify-between"><span className="text-ink-3">Price vs SMA50</span><span>{technical_overlay.overlay_notes.price_vs_sma50_pct != null ? `${(technical_overlay.overlay_notes.price_vs_sma50_pct * 100).toFixed(1)}%` : '—'}</span></div>
          </div>
        </div>
      )}
    </div>
  )
}
