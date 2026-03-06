import { useState, lazy, Suspense } from 'react'
import { TopBar } from './components/layout/TopBar'
import { StatsBar } from './components/layout/StatsBar'
import { Sidebar } from './components/layout/Sidebar'
import { HelpModal } from './components/HelpModal'
import { MobileNav } from './components/layout/MobileNav'
import { useLiveUpdates } from './api/hooks'

// Lazy load the heavy MapView component (290KB Leaflet)
const MapView = lazy(() => import('./components/map/MapView').then(m => ({ default: m.MapView })))

// Loading placeholder for map
function MapLoader() {
  return (
    <div className="w-full h-full bg-dark flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full mx-auto mb-2"></div>
        <div className="text-dim text-sm">Loading map...</div>
      </div>
    </div>
  )
}

export default function App() {
  const [showMap, setShowMap] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  // Enable live SSE updates (auto-refresh when new data arrives)
  useLiveUpdates()

  return (
    <div className="flex flex-col h-screen">
      <TopBar />
      <StatsBar />
      
      {/* Desktop Layout */}
      <div className="hidden md:flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex-1 relative">
          <Suspense fallback={<MapLoader />}>
            <MapView />
          </Suspense>
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="flex md:hidden flex-1 flex-col overflow-hidden relative">
        {/* Map View */}
        <div className={`absolute inset-0 ${showMap ? 'block' : 'hidden'}`}>
          <Suspense fallback={<MapLoader />}>
            <MapView />
          </Suspense>
        </div>
        
        {/* Panel View - slides over map */}
        <div className={`absolute inset-0 bg-bg overflow-y-auto pb-16 ${!showMap ? 'block' : 'hidden'}`}>
          <Sidebar isMobile />
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileNav 
        onOpenSidebar={() => setSidebarOpen(true)}
        showMap={showMap}
        setShowMap={setShowMap}
      />
      
      <HelpModal />
    </div>
  )
}
