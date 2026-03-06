import { useEffect, useRef } from 'react'
import { useTargets, useStrikeAssessment } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'
import { Spinner } from '../ui/Spinner'
import { Badge } from '../ui/Badge'
import { ProbBar } from '../ui/ProbBar'
import { getConfColor } from '../../utils/colors'

export function SatellitePanel() {
  const { data: targetData } = useTargets()
  const satTargetId = useAppStore((s) => s.satTargetId)
  const setSatTargetId = useAppStore((s) => s.setSatTargetId)
  const activeTab = useAppStore((s) => s.activeTab)
  const mutation = useStrikeAssessment()
  
  // Track if auto-fetch already happened for this target
  const lastAutoFetchId = useRef<string>('')

  const targets = targetData?.targets ?? []
  
  // Find the selected target name for display
  const selectedTarget = targets.find(t => t.id === satTargetId)

  // Auto-fetch when satTargetId is set from map click
  useEffect(() => {
    if (
      satTargetId && 
      activeTab === 'satellite' && 
      satTargetId !== lastAutoFetchId.current &&
      !mutation.isPending
    ) {
      lastAutoFetchId.current = satTargetId
      mutation.mutate(satTargetId)
    }
  }, [satTargetId, activeTab])

  function handleFetch() {
    if (!satTargetId) return
    lastAutoFetchId.current = satTargetId
    mutation.mutate(satTargetId)
  }

  const d = mutation.data

  return (
    <>
      {/* Selected Target Display */}
      {selectedTarget && (
        <div className="bg-accent/10 border border-accent rounded-md p-3 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">🎯</span>
            <div className="flex-1">
              <div className="text-sm font-bold text-accent">{selectedTarget.name}</div>
              <div className="text-[11px] text-dim">
                {selectedTarget.type.replace(/_/g, ' ')} • {selectedTarget.province}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selector */}
      <div className="bg-card border border-border rounded-md p-3 mb-2">
        <div className="text-[13px] font-bold text-white mb-2">
          🛰️ Satellite Imagery Comparison
        </div>
        <p className="text-xs text-dim mb-2">
          {satTargetId 
            ? 'Fetching satellite imagery automatically...' 
            : 'Tap a target on the map or select below to analyze satellite imagery.'}
        </p>
        <div className="flex gap-2">
          <select
            value={satTargetId}
            onChange={(e) => setSatTargetId(e.target.value)}
            className="flex-1 bg-bg border border-border text-gray-300 px-2 py-1.5 rounded text-xs"
          >
            <option value="">-- Select target --</option>
            {targets.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} ({t.province})
              </option>
            ))}
          </select>
          <button
            onClick={handleFetch}
            disabled={!satTargetId || mutation.isPending}
            className="bg-accent text-black px-3 py-1.5 rounded text-xs font-bold whitespace-nowrap disabled:opacity-50 hover:bg-accent/80 transition"
          >
            {mutation.isPending ? 'Loading...' : 'Fetch'}
          </button>
        </div>
      </div>

      {/* Loading state */}
      {mutation.isPending && (
        <div className="flex flex-col items-center py-8 text-dim">
          <Spinner />
          <span className="mt-3 text-sm">
            Downloading satellite imagery... This may take a minute.
          </span>
        </div>
      )}

      {/* Error state */}
      {mutation.isError && (
        <div className="bg-card border border-border rounded-md p-3 text-danger text-xs">
          Error: {(mutation.error as Error)?.message ?? 'Failed to fetch'}
        </div>
      )}

      {/* Results */}
      {d && d.success && (
        <div className="bg-card border border-border rounded-md p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[13px] font-bold text-white flex-1 truncate">
              {d.target_name}
            </span>
            <Badge value={Math.round((d.combined_score ?? 0) * 100)} />
          </div>

          <ProbBar
            value={Math.round((d.combined_score ?? 0) * 100)}
            color={getConfColor(Math.round((d.combined_score ?? 0) * 100))}
          />

          <div className="text-[11px] text-dim mt-1.5">
            Verdict: <strong>{d.verdict ?? 'N/A'}</strong>
          </div>
          
          {/* Cloud Coverage Warning */}
          {typeof d.cloud_coverage_percent === 'number' && d.cloud_coverage_percent > 20 && (
            <div className={`mt-2 p-2 rounded text-[11px] ${
              d.cloud_coverage_percent > 50 
                ? 'bg-yellow-500/20 border border-yellow-500/50 text-yellow-300' 
                : 'bg-blue-500/20 border border-blue-500/50 text-blue-300'
            }`}>
              <div className="flex items-center gap-1.5">
                <span>☁️</span>
                <span>
                  <strong>{d.cloud_coverage_percent.toFixed(0)}% cloud coverage</strong>
                  {d.cloud_coverage_percent > 50 
                    ? ' — Results may be less reliable due to cloud interference'
                    : ' — Some areas masked from analysis'}
                </span>
              </div>
            </div>
          )}

          {(d.verdict_reasons?.length ?? 0) > 0 && (
            <div className="text-xs text-dim mt-1.5 space-y-0.5">
              {d.verdict_reasons.map((r, i) => (
                <div key={i}>- {r}</div>
              ))}
            </div>
          )}

          {/* Before / After images */}
          {(d.before_image || d.after_image) && (
            <div className="grid grid-cols-2 gap-2 mt-3">
              {d.before_image && (
                <div className="relative rounded overflow-hidden border border-border">
                  <span className="absolute top-1 left-1 text-[10px] font-bold px-2 py-0.5 rounded bg-green-600/80 text-black z-10">
                    BEFORE
                  </span>
                  <img
                    src={`/timelapse_output/${d.before_image}`}
                    alt="Before"
                    className="w-full block"
                  />
                </div>
              )}
              {d.after_image && (
                <div className="relative rounded overflow-hidden border border-border">
                  <span className="absolute top-1 left-1 text-[10px] font-bold px-2 py-0.5 rounded bg-red-600/80 text-white z-10">
                    AFTER
                  </span>
                  <img
                    src={`/timelapse_output/${d.after_image}`}
                    alt="After"
                    className="w-full block"
                  />
                </div>
              )}
            </div>
          )}

          {/* Heatmap */}
          {d.heatmap && (
            <div className="mt-3">
              <div className="text-[11px] font-bold text-dim mb-1">
                CHANGE HEATMAP
              </div>
              <img
                src={`/timelapse_output/${d.heatmap}`}
                alt="Heatmap"
                className="w-full rounded border border-border"
              />
            </div>
          )}

          {/* Satellite stats */}
          {d.satellite_checked && (
            <div className="text-[11px] text-dim mt-2">
              Change detected: {d.satellite_change_detected ? 'Yes' : 'No'}
              {' | '}Change area: {(d.satellite_change_percent ?? 0).toFixed(1)}%
              {' | '}Events: {d.satellite_event_count ?? 0}
            </div>
          )}
        </div>
      )}
    </>
  )
}
