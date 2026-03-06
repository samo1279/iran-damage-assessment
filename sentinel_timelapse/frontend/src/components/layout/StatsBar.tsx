import { useTargets, useFullAssessment } from '../../api/hooks'

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="flex-1 bg-card py-2.5 px-3 text-center">
      <div className="text-xl font-bold text-white">{value}</div>
      <div className="text-[10px] text-dim uppercase tracking-wider mt-0.5">
        {label}
      </div>
    </div>
  )
}

export function StatsBar() {
  const { data: targets } = useTargets()
  const { data: assessment, dataUpdatedAt } = useFullAssessment()

  const lastScan = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : '--'

  return (
    <div className="flex gap-px bg-border shrink-0">
      <Stat value={targets?.count ?? '--'} label="Targets in DB" />
      <Stat
        value={assessment?.osint?.articles_found ?? '--'}
        label="OSINT Articles"
      />
      <Stat
        value={assessment?.summary?.total_strikes ?? '--'}
        label="Reported Strikes"
      />
      <Stat value={assessment?.summary?.confirmed ?? '--'} label="Confirmed" />
      <Stat value={assessment?.summary?.likely ?? '--'} label="Likely" />
      <Stat value={lastScan} label="Last Scan" />
    </div>
  )
}
