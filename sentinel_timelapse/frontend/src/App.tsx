import { useState, lazy, Suspense, useEffect } from 'react'
import { TopBar } from './components/layout/TopBar'
import { StatsBar } from './components/layout/StatsBar'
import { Sidebar } from './components/layout/Sidebar'
import { HelpModal } from './components/HelpModal'
import { MobileNav } from './components/layout/MobileNav'
import { EarlyWarningPanel } from './components/EarlyWarningPanel'
import { useLiveUpdates } from './api/hooks'

// Lazy load the heavy MapView component (290KB Leaflet)
const MapView = lazy(() => import('./components/map/MapView').then(m => ({ default: m.MapView })))

// Check if mobile
const isMobile = () => typeof window !== 'undefined' && window.innerWidth < 768

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
  // Delay map loading on mobile by 1 second to improve initial render
  const [mapReady, setMapReady] = useState(!isMobile())
  
  // Enable live SSE updates on desktop only
  useLiveUpdates()
  
  // Delay map load on mobile
  useEffect(() => {
    if (isMobile() && !mapReady) {
      const timer = setTimeout(() => setMapReady(true), 1000)
      return () => clearTimeout(timer)
    }
  }, [mapReady])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Early Warning System - Top Priority for Civilian Safety */}
      <EarlyWarningPanel />
      
      {/* Top Main Overlay (The 574 count and stats) */}
      <Suspense fallback={null}>
        <div className="absolute top-0 left-0 right-0 z-[2000]">
          {/* Note: MapView will render the TargetCountBadge inside itself but it is absolute positioned to the top. 
              We'll remove the standard TopBar and StatsBar from the main layout to give full map height. */}
        </div>
      </Suspense>

      <div className="flex flex-1 overflow-hidden relative">
        {/* Full-screen Map with Header Overlay */}
        <div className="absolute inset-0 z-0">
          <Suspense fallback={<MapLoader />}>
            <MapView />
          </Suspense>
        </div>

        {/* Floating Sidebar Container - RIGHT SIDE for better spacing with map legends */}
        <div className="hidden md:block absolute right-6 top-8 bottom-8 z-50 w-[420px] pointer-events-none">
          <div className="w-full h-full pointer-events-auto">
            <Sidebar />
          </div>
        </div>
      </div>

      {/* Mobile Layout Overlays */}
      <div className="flex md:hidden flex-1 flex-col overflow-hidden relative">
        <div className={`absolute inset-0 bg-bg z-20 overflow-y-auto pb-16 ${!showMap ? 'block' : 'hidden'}`}>
          <div className="p-4 border-b border-white/5 flex items-center justify-between bg-card shrink-0">
             <h1 className="text-sm font-black text-white uppercase tracking-tighter">IRI ASSESSMENT PLATFORM</h1>
             <div className="flex items-center gap-1.5 grayscale opacity-50">
               <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
               <span className="text-[10px] font-mono text-dim">LIVE</span>
             </div>
          </div>
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
