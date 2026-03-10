import { useAppStore, type TabId } from '../../store/useAppStore'
import { useQuickStats, useFullAssessment } from '../../api/hooks'
import { StrikesPanel } from '../panels/StrikesPanel'
import { TargetsPanel } from '../panels/TargetsPanel'
import { NewsPanel } from '../panels/NewsPanel'
import { SatellitePanel } from '../panels/SatellitePanel'

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: 'strikes', label: 'STRIKES', icon: '💥' },
  { id: 'targets', label: 'TARGETS', icon: '🎯' },
  { id: 'news', label: 'NEWS', icon: '📰' },
  { id: 'satellite', label: 'SATELLITE', icon: '🛰️' },
]

interface SidebarProps {
  isMobile?: boolean
}

export function Sidebar({ isMobile = false }: SidebarProps) {
  const activeTab = useAppStore((s) => s.activeTab)
  const setActiveTab = useAppStore((s) => s.setActiveTab)
  
  // Live stats
  const { data: quickStats } = useQuickStats()
  const { data: assessmentData } = useFullAssessment()
  
  const totalTargets = quickStats?.target_count ?? 0
  const activeStrikes = assessmentData?.assessments?.filter(a => (a.combined_score ?? 0) >= 0.3).length ?? 0
  const categories = quickStats?.categories ?? {}
  
  const critical = (categories['nuclear_facility'] || 0) + (categories['nuclear'] || 0) + (categories['missile'] || 0)
  const high = (categories['irgc'] || 0) + (categories['air_defense'] || 0) + (categories['airbase'] || 0) + (categories['military'] || 0)
  const medium = (categories['refinery'] || 0) + (categories['power_generation'] || 0) + (categories['government'] || 0)
  const civilian = (categories['population_center'] || 0) + (categories['city'] || 0)

  return (
    <div className={`flex flex-col h-full overflow-hidden ${
      isMobile ? 'w-full h-full bg-[#0b1020]' : 'w-full h-full bg-[#0d1117]/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_60px_-15px_rgba(0,0,0,0.9)]'
    }`}>
      {/* Header with target count - mahsaalert style */}
      <div className="shrink-0 p-4 border-b border-white/10 bg-gradient-to-b from-white/5 to-transparent">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
              <span className="text-2xl">🎯</span>
            </div>
            <div>
              <div className="text-3xl font-black text-white tabular-nums tracking-tight">
                {totalTargets.toLocaleString()}
              </div>
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">TARGETS</div>
            </div>
          </div>
          {activeStrikes > 0 && (
            <div className="bg-red-600 text-white px-3 py-2 rounded-xl animate-pulse shadow-lg shadow-red-900/50">
              <div className="text-xl font-black leading-none">{activeStrikes}</div>
              <div className="text-[8px] font-bold uppercase">ACTIVE</div>
            </div>
          )}
        </div>
        
        {/* Category pills */}
        <div className="flex flex-wrap gap-2">
          <span className="px-2 py-1 rounded-lg bg-red-500/20 text-red-400 text-[10px] font-bold">
            🔴 CRITICAL ({critical})
          </span>
          <span className="px-2 py-1 rounded-lg bg-orange-500/20 text-orange-400 text-[10px] font-bold">
            🟠 HIGH ({high})
          </span>
          <span className="px-2 py-1 rounded-lg bg-yellow-500/20 text-yellow-400 text-[10px] font-bold">
            ⚡ MEDIUM ({medium})
          </span>
          <span className="px-2 py-1 rounded-lg bg-green-500/20 text-green-400 text-[10px] font-bold">
            🏙️ CIVILIAN ({civilian})
          </span>
        </div>
      </div>
      
      {/* Tab bar */}
      <div className={`flex shrink-0 ${isMobile ? 'bg-[#161b22] border-b border-white/5' : 'bg-white/5 border-b border-white/10'}`}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 py-3 text-center text-[10px] font-black tracking-wider transition-all duration-200 ${
              activeTab === t.id
                ? 'text-accent border-b-2 border-accent bg-accent/10'
                : 'text-gray-500 border-b-2 border-transparent hover:text-gray-300 hover:bg-white/5'
            }`}
          >
            <span className="mr-1">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Panel content */}
      <div className={`flex-1 overflow-y-auto p-4 custom-scrollbar ${isMobile ? 'pb-24' : ''}`}>
        {activeTab === 'strikes' && <StrikesPanel />}
        {activeTab === 'targets' && <TargetsPanel />}
        {activeTab === 'news' && <NewsPanel />}
        {activeTab === 'satellite' && <SatellitePanel />}
      </div>

      {!isMobile && (
        <div className="text-[9px] font-mono text-gray-600 text-center py-2 px-2 border-t border-white/5 shrink-0 uppercase tracking-tighter flex items-center justify-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
          System Operational • Auto-Sync: 5m
        </div>
      )}
    </div>
  )
}
