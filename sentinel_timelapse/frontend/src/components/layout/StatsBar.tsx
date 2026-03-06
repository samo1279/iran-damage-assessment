import { useQuickStats, useFullAssessment } from '../../api/hooks'

function Stat({ value, label, loading }: { value: string | number; label: string; loading?: boolean }) {
  return (
    <div className="flex-1 bg-card py-2.5 px-3 text-center">
      <div className={`text-xl font-bold ${loading ? 'text-dim animate-pulse' : 'text-white'}`}>
        {value}
      </div>
      <div className="text-[10px] text-dim uppercase tracking-wider mt-0.5">
        {label}
      </div>
    </div>
  )
}

export function StatsBar() {
  // Use quick-stats for instant initial load
  const { data: quickStats, isLoading: quickLoading, dataUpdatedAt } = useQuickStats()
  // Full assessment loads in background (cached on backend)
  const { data: assessment, isFetching } = useFullAssessment()

  const lastScan = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : (quickStats?.last_osint_refresh ? new Date(quickStats.last_osint_refresh).toLocaleTimeString() : '--')
  
  // Use quick stats first, then full assessment when available
  const targetCount = quickStats?.target_count ?? '--'
  const articleCount = quickStats?.osint_articles ?? assessment?.osint?.articles_found ?? '--'
  const strikeCount = quickStats?.strike_count ?? assessment?.summary?.total_strikes ?? 0
  const confirmedCount = quickStats?.confirmed ?? assessment?.summary?.confirmed ?? 0
  const likelyCount = quickStats?.likely ?? assessment?.summary?.likely ?? 0

  return (
    <div className="flex gap-px bg-border shrink-0">
      <Stat value={targetCount} label="Targets in DB" loading={quickLoading} />
      <Stat value={articleCount} label="OSINT Articles" loading={isFetching} />
      <Stat value={strikeCount} label="Reported Strikes" loading={isFetching} />
      <Stat value={confirmedCount} label="Confirmed" loading={isFetching} />
      <Stat value={likelyCount} label="Likely" loading={isFetching} />
      <Stat value={isFetching ? 'Loading...' : lastScan} label="Last Scan" />
    </div>
  )
}
