import { useState, lazy, Suspense } from 'react'
import { EarlyWarningPanel } from './components/EarlyWarningPanel'
import { UnifiedHeader } from './components/layout/UnifiedHeader'
import { Sidebar } from './components/layout/Sidebar'
import { MobileNav } from './components/layout/MobileNav'
import { HelpModal } from './components/HelpModal'
import { useLiveUpdates } from './api/hooks'
import { useAppStore } from './store/useAppStore'

// Lazy load the heavy MapView component (290KB Leaflet)
const MapView = lazy(() => import('./components/map/MapView').then(m => ({ default: m.MapView })))

// Loading placeholder for map
function MapLoader() {
  return (
    <div className="w-full h-screen bg-[#1a1a2e] flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <div className="text-white/60 text-sm font-medium">در حال بارگذاری نقشه...</div>
        <div className="text-white/40 text-xs mt-1">Loading Map...</div>
      </div>
    </div>
  )
}

export default function App() {
  const [showMap, setShowMap] = useState(true)
  const activeTab = useAppStore(s => s.activeTab)
  const setActiveTab = useAppStore(s => s.setActiveTab)
  const selectedTarget = useAppStore(s => s.selectedTarget)
  const setSelectedTarget = useAppStore(s => s.setSelectedTarget)

  // Enable live SSE updates
  useLiveUpdates()

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#1a1a2e] relative">
      {/* Early Warning System - Hidden Banner, will move to map markers */}
      {/* <EarlyWarningPanel /> */}
      
      {/* Unified Header - The ONLY permanent UI element */}
      <UnifiedHeader />
      
      {/* Full-screen Map - Always the background */}
      <Suspense fallback={<MapLoader />}>
        <MapView />
      </Suspense>

      {/* Floating Interactive Panel - Only shows when Target selected or Header Tab clicked */}
      {(selectedTarget || activeTab !== 'strikes') && (
        <div className="absolute top-20 right-4 bottom-4 z-[2000] w-[430px] transition-all animate-in slide-in-from-right duration-300">
          <div className="h-full w-full bg-[#0d1117]/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col relative">
            {/* Close button for floating panel */}
            <button 
              onClick={() => {
                setSelectedTarget(null)
                setActiveTab('strikes') // Default state
              }}
              className="absolute top-4 right-4 z-[3000] w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white text-lg transition-all active:scale-95 shadow-lg shadow-black/50 border border-white/5"
            >
              ✕
            </button>
            
            <Sidebar />
          </div>
        </div>
      )}

      {/* Mobile view handled by showMap/MobileNav but Sidebar now replaces sidebar layout */}
      {!showMap && (
        <div className="md:hidden absolute inset-0 z-[2500] bg-[#0b1020]">
           <button 
              onClick={() => setShowMap(true)}
              className="absolute top-4 right-4 z-[3000] w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white"
            >
              ✕
            </button>
            <div className="h-full overflow-y-auto pt-4">
               <Sidebar isMobile />
            </div>
        </div>
      )}

      <MobileNav
        onOpenSidebar={() => setShowMap(false)}
        showMap={showMap}
        setShowMap={setShowMap}
      />

      <HelpModal />
    </div>
  )
}
