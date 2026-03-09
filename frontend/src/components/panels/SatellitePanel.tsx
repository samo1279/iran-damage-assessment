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
    
    // Switch to satellite tab automatically if a point is selected
    if (satTargetId && activeTab !== 'satellite' && satTargetId !== lastAutoFetchId.current) {
       useAppStore.getState().setActiveTab('satellite')
    }
  }, [satTargetId, activeTab])

  function handleFetch() {
    if (!satTargetId) return
    lastAutoFetchId.current = satTargetId
    mutation.mutate(satTargetId)
  }

  const d = mutation.data

  return (
    <div className="space-y-4">
      {/* Selected Target Display */}
      {selectedTarget && (
        <div className="bg-accent/10 border-2 border-accent rounded-lg p-4 mb-4 shadow-lg animate-pulse-slow">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎯</span>
            <div className="flex-1">
              <div className="text-base font-black text-accent uppercase tracking-wider">{selectedTarget.name}</div>
              <div className="text-xs text-dim font-bold mt-1">
                {selectedTarget.type.replace(/_/g, ' ').toUpperCase()} • {selectedTarget.province.toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selector Container - Fixed Border and Button */}
      <div className="bg-card border-2 border-white/10 rounded-xl p-5 mb-4 shadow-xl">
        <div className="text-sm font-black text-white mb-3 uppercase tracking-[0.1em] flex items-center gap-2">
          <span className="text-accent text-lg">🛰️</span> Satellite Intelligence Analysis
        </div>
        <p className="text-xs text-dim mb-4 leading-relaxed font-medium">
          {satTargetId 
            ? 'System is automatically fetching and correlating multi-spectral imagery...' 
            : 'Select a strategic target from the map or use the dropdown below to initiate satellite verification.'}
        </p>
        
        <div className="flex flex-col gap-3">
          <select
            value={satTargetId}
            onChange={(e) => setSatTargetId(e.target.value)}
            className="w-full bg-bg border-2 border-white/10 text-gray-200 px-4 py-3 rounded-lg text-sm font-bold focus:border-accent outline-none transition-all appearance-none cursor-pointer"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center', backgroundSize: '1.2em' }}
          >
            <option value="" disabled>-- CHOOSE STRATEGIC TARGET --</option>
            {targets.map((t) => (
              <option key={t.id} value={t.id} className="bg-card py-2">
                {t.name} ({t.province})
              </option>
            ))}
          </select>
          
          <button
            onClick={handleFetch}
            disabled={!satTargetId || mutation.isPending}
            className={`w-full py-3.5 rounded-lg text-sm font-black uppercase tracking-widest transition-all shadow-lg active:scale-95 ${
              mutation.isPending 
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                : 'bg-accent text-black hover:bg-white hover:shadow-accent/40'
            }`}
          >
            {mutation.isPending ? (
              <div className="flex items-center justify-center gap-2">
                <Spinner size={16} /> <span>Running Analysis...</span>
              </div>
            ) : 'Manual Refresh Analysis'}
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
    </div>
  )
}
