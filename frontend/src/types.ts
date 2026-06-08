// All shared TypeScript interfaces for ARKWOOD FIU Dashboard

export type OverlayRating = 'STRONG_SETUP' | 'SETUP' | 'NEUTRAL' | 'AVOID' | 'EXTENDED'
export type Rating = 'STRONG BUY' | 'BUY' | 'HOLD' | 'SELL'
export type DataQuality = 'FULL' | 'PARTIAL' | 'EMPTY' | 'UNKNOWN'
export type AlertDirection = 'BELOW' | 'ABOVE'
export type V2Action = 'SELL' | 'WATCH_EXIT' | 'RISK_OFF_HOLD' | 'HOLD_EXTENDED' | 'ADD' | 'WAIT' | 'HOLD' | 'DATA_MISSING'
export type StockClass = 'COMPOUNDER' | 'CYCLICAL' | 'HIGH_VOL' | 'EMERGING' | 'UNKNOWN'
export type MacroState = 'RISK_ON' | 'RISK_OFF' | 'UNKNOWN'

export interface Holding {
  ticker: string
  short_name: string | null
  shares: number | null
  avg_cost: number | null
  current_price: number | null
  market_value: number | null
  unrealized_pnl: number | null
  unrealized_pnl_pct: number | null
  target_weight: number | null
  max_weight: number | null
  alert_below: number | null
  alert_above: number | null
  alert_triggered: boolean
  alert_direction: AlertDirection | null
  sector: string
  thesis_confidence: string | null
  last_reviewed: string | null
  overlay_rating: OverlayRating | null
  auto_total: number | null
  rating: Rating | null
  data_quality: DataQuality
  has_thesis: boolean
  stock_class: StockClass | null
  v2_action: V2Action | null
  v2_rationale: string | null
  consecutive_avoid: boolean | null
  persistence_confirmed: boolean | null
}

export interface PortfolioTotals {
  total_market_value: number
  total_unrealized_pnl: number | null
  total_unrealized_pnl_pct: number | null
  active_alerts: number
}

export interface PortfolioResponse {
  snapshot_date: string | null
  snapshot_days_old: number | null
  macro_state: MacroState | null
  holdings: Holding[]
  portfolio_totals: PortfolioTotals
}

export interface WatchlistItem {
  ticker: string
  sector: string
  why_watching: string
  target_entry: number | null
  priority: string | null
  date_added: string | null
  current_price: number | null
  overlay_rating: OverlayRating | null
  has_snapshot: boolean
  rating: Rating | null
}

export interface WatchlistResponse {
  items: WatchlistItem[]
}

export interface PricePoint {
  date: string
  close: number
}

export interface MarketData {
  current_price: number | null
  market_cap: number | null
  beta: number | null
  fifty_two_week_high: number | null
  fifty_two_week_low: number | null
  ytd_return: number | null
  sector: string | null
  industry: string | null
  price_history_30d: PricePoint[]
  data_quality: DataQuality
  missing_fields: string[]
}

export interface Fundamentals {
  trailing_pe: number | null
  forward_pe: number | null
  revenue_growth_yoy: number | null
  gross_margin: number | null
  gross_margin_trend: 'expanding' | 'flat' | 'contracting' | null
  operating_margin: number | null
  upside_to_consensus: number | null
  target_mean_price: number | null
  analyst_count: number | null
  cash_runway_months: number | 'profitable' | null
  peg_estimate: number | null
  data_quality: DataQuality
  missing_fields: string[]
}

export interface Technicals {
  sma_50: number | null
  sma_200: number | null
  rsi_14: number | null
  trend_signal: string | null
  momentum_signal: string | null
  breakout_signal: string | null
  rs_signal: string | null
  price_vs_sma50_pct: number | null
  return_1m: number | null
  return_3m: number | null
  data_quality: DataQuality
  missing_fields: string[]
}

export interface TechnicalOverlay {
  overlay_rating: OverlayRating | null
  bullish_signals: string[]
  bearish_signals: string[]
  bullish_count: number
  bearish_count: number
  overlay_notes: {
    rsi_14: number | null
    price_vs_sma50_pct: number | null
    sma_50: number | null
    sma_200: number | null
    price_vs_52w_high_pct: number | null
  }
}

export interface V2Signal {
  stock_class: StockClass | null
  macro_state: MacroState | null
  v2_action: V2Action | null
  v2_rationale: string | null
  consecutive_avoid: boolean | null
  persistence_confirmed: boolean | null
  entry_allowed: boolean | null
  exit_triggered: boolean | null
}

export interface Scores {
  auto_scores: Record<string, number>
  auto_total: number | null
  manual_total: number | null
  tvs_total: number | null
  score_status: 'AUTO_ONLY' | 'FULL_TVS'
  max_possible_auto: number
  max_possible_total: number
  manual_scores_needed: Record<string, number | null>
  notes: Record<string, string>
  v2_signal: V2Signal | null
  technical_overlay: TechnicalOverlay | null
}

export interface ChokepointAxis {
  score: number
  max_score: number
  classification: string
  scores: Record<string, number>
  labels: Record<string, string>
}

export interface ChokepointOverlay {
  ticker: string
  ai_role: string | null
  assessment_mode: string
  durability: ChokepointAxis
  entry_risk: ChokepointAxis
  risk_locations: string[]
  sizing_bias: string
  tvs_tiebreaker: string | null
  technical_timing_rule: string | null
  rationale: string | null
  last_reviewed: string | null
  data_quality: string
}

export interface ArkData {
  ark_held: boolean
  conviction_level: string
  total_etfs_held_in: number
  holdings: Array<{ etf: string; weight_pct: number; shares: number; market_value_usd: number }>
}

export interface NewsData {
  article_count: number
  recent_catalyst_score: number
  articles: Array<{ title: string; publisher: string; published_at: string | null; link: string; sentiment_hint: string }>
  data_quality: DataQuality
}

export interface HoldingInfo {
  shares: number | null
  avg_cost: number | null
  thesis_confidence: string | null
  last_reviewed: string | null
  alert_below: number | null
  alert_above: number | null
}

export interface TickerDetail {
  ticker: string
  snapshot_date: string | null
  rating: Rating | null
  data_quality: DataQuality
  chokepoint: ChokepointOverlay | null
  market: MarketData
  fundamentals: Fundamentals
  technicals: Technicals
  scores: Scores
  ark: ArkData
  news: NewsData
  holding: HoldingInfo | null
  thesis_markdown: string | null
  stock_class: StockClass | null
  macro_state: MacroState | null
  watchlist: {
    why_watching: string
    target_entry: number | null
    priority: string | null
    date_added: string | null
  } | null
}

export interface RefreshEvent {
  step: string
  status: 'running' | 'done' | 'error'
  message: string
  fatal?: boolean
}

export interface RefreshComplete {
  success: boolean
  snapshot_date: string
  duration_seconds: number
  steps_succeeded: string[]
  steps_failed: string[]
}
