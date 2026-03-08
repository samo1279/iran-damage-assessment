import { useAppStore, type TabId } from '../../store/useAppStore'
import { StrikesPanel } from '../panels/StrikesPanel'
import { TargetsPanel } from '../panels/TargetsPanel'
import { NewsPanel } from '../panels/NewsPanel'
import { AlarmsPanel } from '../panels/AlarmsPanel'
import { SatellitePanel } from '../panels/SatellitePanel'

const TABS: { id: TabId; label: string }[] = [
  { id: 'strikes', label: 'STRIKES' },
  { id: 'targets', label: 'TARGETS' },
  { id: 'news', label: 'NEWS' },
  { id: 'alarms', label: '🚨 ALARMS' },
  { id: 'satellite', label: 'SAT' },
]

interface SidebarProps {
  isMobile?: boolean
}

export function Sidebar({ isMobile = false }: SidebarProps) {
  const activeTab = useAppStore((s) => s.activeTab)
  const setActiveTab = useAppStore((s) => s.setActiveTab)

  return (
    <div className={`flex flex-col h-full overflow-hidden ${
      isMobile ? 'w-full h-full bg-bg' : 'w-full h-full bg-black/70 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_50px_-10px_rgba(0,0,0,0.8)]'
    }`}>
      {/* Tab bar - LARGER TEXT & BOLDER DISPLAY */}
      <div className={`flex shrink-0 ${isMobile ? 'bg-card border-b border-border' : 'bg-white/5 border-b border-white/10'}`}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 py-5 md:py-4 text-center text-[11px] md:text-sm font-black tracking-[0.1em] transition-all duration-300 ${
              activeTab === t.id
                ? 'text-accent border-b-2 border-accent bg-accent/10 shadow-[inset_0_-10px_20px_-10px_rgba(0,180,216,0.2)]'
                : 'text-gray-500 border-b-2 border-transparent hover:text-gray-300 hover:bg-white/5'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Panel content - MORE PADDING */}
      <div className={`flex-1 overflow-y-auto p-5 custom-scrollbar ${isMobile ? 'pb-20' : ''}`}>
        {activeTab === 'strikes' && <StrikesPanel />}
        {activeTab === 'targets' && <TargetsPanel />}
        {activeTab === 'news' && <NewsPanel />}
        {activeTab === 'alarms' && <AlarmsPanel />}
        {activeTab === 'satellite' && <SatellitePanel />}
      </div>

      {!isMobile && (
        <div className="text-[9px] font-mono text-gray-600 text-center py-2 px-2 border-t border-white/5 shrink-0 uppercase tracking-tighter">
          System Status: <span className="text-green-500/50">Operational</span> // Auto-Sync: 5m
        </div>
      )}
    </div>
  )
}
