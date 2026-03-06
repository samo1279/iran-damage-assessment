import { useAppStore, type TabId } from '../../store/useAppStore'

interface MobileNavProps {
  onOpenSidebar: () => void
  showMap: boolean
  setShowMap: (show: boolean) => void
}

const TABS: { id: TabId; label: string; emoji: string }[] = [
  { id: 'strikes', label: 'Strikes', emoji: '💥' },
  { id: 'targets', label: 'Targets', emoji: '🎯' },
  { id: 'news', label: 'News', emoji: '📰' },
  { id: 'satellite', label: 'Satellite', emoji: '🛰️' },
]

export function MobileNav({ onOpenSidebar, showMap, setShowMap }: MobileNavProps) {
  const activeTab = useAppStore((s) => s.activeTab)
  const setActiveTab = useAppStore((s) => s.setActiveTab)

  const handleTabClick = (tabId: TabId) => {
    setActiveTab(tabId)
    setShowMap(false)
    onOpenSidebar()
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border z-[1000] md:hidden">
      <div className="flex justify-around items-center py-2 px-1 safe-area-pb">
        {/* Map toggle button */}
        <button
          onClick={() => setShowMap(true)}
          className={`flex flex-col items-center justify-center py-1 px-2 rounded transition ${
            showMap ? 'text-accent' : 'text-dim hover:text-gray-300'
          }`}
        >
          <span className="text-lg mb-0.5">🗺️</span>
          <span className="text-[10px] font-medium">Map</span>
        </button>

        {/* Tab buttons */}
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id && !showMap
          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`flex flex-col items-center justify-center py-1 px-2 rounded transition ${
                isActive ? 'text-accent' : 'text-dim hover:text-gray-300'
              }`}
            >
              <span className="text-lg mb-0.5">{tab.emoji}</span>
              <span className="text-[10px] font-medium">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
