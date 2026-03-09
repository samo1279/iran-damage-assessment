import { useAppStore, type TabId } from '../../store/useAppStore'
import { useQuery } from '@tanstack/react-query'
import { fetchJSON } from '../../api/client'

interface MobileNavProps {
  onOpenSidebar: () => void
  showMap: boolean
  setShowMap: (show: boolean) => void
}

interface WarningsResponse {
  count: number;
}

const TABS: { id: TabId; label: string; emoji: string }[] = [
  { id: 'strikes', label: 'Strikes', emoji: '💥' },
  { id: 'targets', label: 'List', emoji: '🎯' },
  { id: 'news', label: 'News', emoji: '📰' },
  { id: 'alarms', label: 'Alert', emoji: '🚨' },
]

export function MobileNav({ onOpenSidebar, showMap, setShowMap }: MobileNavProps) {
  const activeTab = useAppStore((s) => s.activeTab)
  const setActiveTab = useAppStore((s) => s.setActiveTab)
  
  // Get warning count for badge
  const { data: warningData } = useQuery<WarningsResponse>({
    queryKey: ['early-warnings'],
    queryFn: async () => {
      const response = await fetchJSON<WarningsResponse>('/api/early-warnings');
      return response || { count: 0 };
    },
    staleTime: 60000,
  });
  const warningCount = warningData?.count || 0;

  const handleTabClick = (tabId: TabId) => {
    setActiveTab(tabId)
    setShowMap(false)
    onOpenSidebar()
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#0d1117] border-t-2 border-accent/30 z-[3000] md:hidden shadow-[0_-4px_20px_rgba(0,0,0,0.5)]">
      <div className="flex justify-around items-center py-2 px-2 safe-area-pb">
        {/* Map toggle button */}
        <button
          onClick={() => setShowMap(true)}
          className={`flex flex-col items-center justify-center min-w-[60px] py-2 px-2 rounded-xl transition-all ${
            showMap 
              ? 'text-accent bg-accent/20 border border-accent/50' 
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <span className="text-2xl">🗺️</span>
          <span className="text-[9px] font-black uppercase mt-1">Map</span>
        </button>

        {/* Tab buttons */}
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id && !showMap
          const isAlarms = tab.id === 'alarms'
          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`relative flex flex-col items-center justify-center min-w-[60px] py-2 px-2 rounded-xl transition-all ${
                isActive 
                  ? isAlarms 
                    ? 'text-red-400 bg-red-500/20 border border-red-500/50' 
                    : 'text-accent bg-accent/20 border border-accent/50'
                  : isAlarms && warningCount > 0
                    ? 'text-red-400'
                    : 'text-gray-400 hover:text-white'
              }`}
            >
              <span className="text-2xl">{tab.emoji}</span>
              <span className="text-[9px] font-black uppercase mt-1">{tab.label}</span>
              {/* Warning badge */}
              {isAlarms && warningCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[8px] font-black w-5 h-5 rounded-full flex items-center justify-center animate-pulse">
                  {warningCount}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
