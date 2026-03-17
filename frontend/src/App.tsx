import { useState, useEffect, useCallback } from 'react'
import type { PortfolioResponse, WatchlistResponse } from './types'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { DetailPanel } from './components/DetailPanel'

function App() {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null)
  const [watchlist, setWatchlist] = useState<WatchlistResponse | null>(null)
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  const fetchPortfolio = useCallback(() => {
    fetch('/api/portfolio')
      .then((r) => r.json())
      .then(setPortfolio)
      .catch(console.error)
  }, [])

  const fetchWatchlist = useCallback(() => {
    fetch('/api/watchlist')
      .then((r) => r.json())
      .then(setWatchlist)
      .catch(console.error)
  }, [])

  useEffect(() => {
    fetchPortfolio()
    fetchWatchlist()
  }, [fetchPortfolio, fetchWatchlist])

  const handleRefreshComplete = useCallback(() => {
    fetchPortfolio()
    fetchWatchlist()
  }, [fetchPortfolio, fetchWatchlist])

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-bg">
      <Header
        totals={portfolio?.portfolio_totals ?? null}
        snapshotDate={portfolio?.snapshot_date ?? null}
        snapshotDaysOld={portfolio?.snapshot_days_old ?? null}
        macroState={portfolio?.macro_state ?? null}
        onRefreshComplete={handleRefreshComplete}
      />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          holdings={portfolio?.holdings ?? []}
          watchlist={watchlist?.items ?? []}
          selected={selectedTicker}
          onSelect={setSelectedTicker}
        />
        <DetailPanel ticker={selectedTicker} />
      </div>
    </div>
  )
}

export default App
