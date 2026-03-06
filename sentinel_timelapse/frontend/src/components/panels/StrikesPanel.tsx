import { useFullAssessment } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'
import { Spinner } from '../ui/Spinner'
import { Badge } from '../ui/Badge'
import { ProbBar } from '../ui/ProbBar'
import { getConfColor } from '../../utils/colors'

export function StrikesPanel() {
  const { data, isLoading } = useFullAssessment()
  const flyTo = useAppStore((s) => s.flyTo)

  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-10 text-dim">
        <Spinner />
        <span className="mt-3 text-sm">Loading intelligence data...</span>
      </div>
    )
  }

  const assessments = data?.assessments ?? []

  if (!assessments.length) {
    return (
      <div className="bg-card border border-border rounded-md p-5 text-center text-dim text-sm">
        No strikes reported yet. Data refreshes automatically every 5 minutes.
      </div>
    )
  }

  const sorted = [...assessments].sort(
    (a, b) => (b.combined_score ?? 0) - (a.combined_score ?? 0),
  )

  return (
    <div className="space-y-2">
      {sorted.map((s) => {
        const pct = Math.round((s.combined_score ?? 0) * 100)
        const verdict = s.verdict ?? 'UNCONFIRMED'
        const reasons = (s.verdict_reasons ?? []).join(' | ')
        const sources = s.osint_sources ?? s.source_count ?? 0

        return (
          <div
            key={s.strike_id}
            onClick={() => flyTo(s.lat, s.lon)}
            className="bg-card border border-border rounded-md p-3 cursor-pointer hover:border-accent/40 transition"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[13px] font-bold text-white flex-1 truncate">
                {s.target_name ?? 'Unknown'}
              </span>
              <Badge value={pct} />
            </div>
            <ProbBar value={pct} color={getConfColor(pct)} />
            <div className="text-[11px] text-dim mt-1.5">
              <strong>{verdict}</strong> -- {sources} source(s)
            </div>
            {reasons && (
              <div className="text-xs text-dim mt-1 leading-relaxed">
                {reasons}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
