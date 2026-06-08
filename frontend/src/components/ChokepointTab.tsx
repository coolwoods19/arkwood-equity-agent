import type { ChokepointOverlay } from '../types'

function AxisCard({
  title,
  axis,
}: {
  title: string
  axis: ChokepointOverlay['durability']
}) {
  const pct = axis.max_score > 0 ? Math.max(0, Math.min(1, axis.score / axis.max_score)) * 100 : 0
  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3">{title}</p>
          <p className="text-xs text-ink-2 mt-1">{axis.classification}</p>
        </div>
        <p className="font-mono text-2xl font-semibold text-ink">
          {axis.score}<span className="text-sm font-normal text-ink-3">/{axis.max_score}</span>
        </p>
      </div>
      <div className="h-2 bg-border rounded-full overflow-hidden mb-3">
        <div className="h-full rounded-full bg-teal-500" style={{ width: `${pct}%` }} />
      </div>
      <div className="space-y-2">
        {Object.entries(axis.scores).map(([key, score]) => (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-ink-2 flex-1">{axis.labels[key] || key}</span>
            <span className="font-mono text-xs text-ink-2 w-8 text-right">{score}/10</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ChokepointTab({
  ticker,
  chokepoint,
}: {
  ticker: string
  chokepoint: ChokepointOverlay | null
}) {
  if (!chokepoint) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-dashed border-border bg-surface p-8 text-center">
          <p className="text-sm text-ink-2 font-serif mb-2">No AI chokepoint profile for {ticker}</p>
          <p className="text-xs text-ink-3">
            Create <code className="font-mono bg-border px-1.5 py-0.5 rounded">data/chokepoints/{ticker}.json</code> from the template to add the two-axis overlay.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="bg-surface rounded-lg border border-border p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-1">AI Chokepoint Overlay</p>
            <h2 className="font-serif text-xl text-ink">{chokepoint.ai_role || chokepoint.ticker}</h2>
            <p className="text-xs text-ink-3 mt-1">{chokepoint.assessment_mode}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-1">Sizing Bias</p>
            <p className="text-sm font-mono font-semibold text-ink">{chokepoint.sizing_bias}</p>
          </div>
        </div>
        {chokepoint.rationale && (
          <p className="text-sm text-ink-2 leading-relaxed mt-4 border-t border-border pt-3">{chokepoint.rationale}</p>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <AxisCard title="Chokepoint Durability" axis={chokepoint.durability} />
        <AxisCard title="Entry / Risk Quality" axis={chokepoint.entry_risk} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-surface rounded-lg border border-border p-4">
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-3">Risk Location</p>
          <div className="flex flex-wrap gap-2">
            {chokepoint.risk_locations.length > 0 ? (
              chokepoint.risk_locations.map((risk) => (
                <span key={risk} className="text-[10px] font-mono border border-border rounded px-2 py-1 text-ink-2 bg-bg">
                  {risk}
                </span>
              ))
            ) : (
              <span className="text-xs text-ink-4">No explicit risk locations set</span>
            )}
          </div>
        </div>

        <div className="bg-surface rounded-lg border border-border p-4 space-y-3">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-1">TVS Tie-Breaker</p>
            <p className="text-xs text-ink-2 leading-relaxed">{chokepoint.tvs_tiebreaker || 'No rule set'}</p>
          </div>
          <div className="border-t border-border pt-3">
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-3 mb-1">Technical Timing Rule</p>
            <p className="text-xs text-ink-2 leading-relaxed">{chokepoint.technical_timing_rule || 'No rule set'}</p>
          </div>
        </div>
      </div>

      <p className="text-[10px] font-mono text-ink-4">
        Last reviewed: {chokepoint.last_reviewed || 'unknown'} · Source: {chokepoint.data_quality}
      </p>
    </div>
  )
}
