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
      isMobile 
        ? 'w-full h-full bg-[#0d1117]' 
        : 'w-full h-full bg-black/70 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_50px_-10px_rgba(0,0,0,0.8)]'
    }`}>
      {/* Tab bar - Mobile optimized */}
      <div className={`flex shrink-0 overflow-x-auto ${isMobile ? 'bg-[#161b22] border-b-2 border-accent/20' : 'bg-white/5 border-b border-white/10'}`}>
        {TABS.map((t) => {
          const isAlarm = t.id === 'alarms'
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex-1 min-w-[70px] py-4 text-center text-[10px] md:text-sm font-black tracking-wider transition-all duration-200 ${
                activeTab === t.id
                  ? isAlarm 
                    ? 'text-red-400 border-b-3 border-red-500 bg-red-500/10'
                    : 'text-accent border-b-3 border-accent bg-accent/10'
                  : 'text-gray-500 border-b-3 border-transparent active:bg-white/10'
              }`}
            >
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Panel content - Better mobile padding */}
      <div className={`flex-1 overflow-y-auto custom-scrollbar ${isMobile ? 'p-4 pb-24' : 'p-5'}`}>
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
