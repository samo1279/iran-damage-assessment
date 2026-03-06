import { useAppStore, type TabId } from '../../store/useAppStore'
import { StrikesPanel } from '../panels/StrikesPanel'
import { TargetsPanel } from '../panels/TargetsPanel'
import { NewsPanel } from '../panels/NewsPanel'
import { SatellitePanel } from '../panels/SatellitePanel'

const TABS: { id: TabId; label: string }[] = [
  { id: 'strikes', label: 'STRIKES' },
  { id: 'targets', label: 'TARGETS' },
  { id: 'news', label: 'NEWS' },
  { id: 'satellite', label: 'SATELLITE' },
]

interface SidebarProps {
  isMobile?: boolean
}

export function Sidebar({ isMobile = false }: SidebarProps) {
  const activeTab = useAppStore((s) => s.activeTab)
  const setActiveTab = useAppStore((s) => s.setActiveTab)

  return (
    <div className={`flex flex-col border-r border-border overflow-hidden ${
      isMobile ? 'w-full' : 'w-[420px] shrink-0'
    }`}>
      {/* Tab bar */}
      <div className="flex bg-card border-b border-border shrink-0">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 py-3 md:py-2 text-center text-sm md:text-xs font-semibold border-b-2 transition ${
              activeTab === t.id
                ? 'text-accent border-accent'
                : 'text-dim border-transparent hover:text-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Panel content */}
      <div className={`flex-1 overflow-y-auto p-2.5 ${isMobile ? 'pb-20' : ''}`}>
        {activeTab === 'strikes' && <StrikesPanel />}
        {activeTab === 'targets' && <TargetsPanel />}
        {activeTab === 'news' && <NewsPanel />}
        {activeTab === 'satellite' && <SatellitePanel />}
      </div>

      {!isMobile && (
        <div className="text-[10px] text-dim text-center py-1 px-2 border-t border-border shrink-0">
          Auto-refresh: every 5 minutes (TanStack Query)
        </div>
      )}
    </div>
  )
}
