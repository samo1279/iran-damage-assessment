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
    <div className="flex flex-col h-screen h-[100dvh] overflow-hidden bg-[#0d1117]">
      {/* Early Warning System - Top Priority for Civilian Safety */}
      <EarlyWarningPanel />
      
      {/* MAIN CONTENT - Full screen map with overlays */}
      <div className="flex-1 relative overflow-hidden">
        {/* Full-screen Map - fills entire viewport */}
        <div className="absolute inset-0">
          <Suspense fallback={<MapLoader />}>
            <MapView />
          </Suspense>
        </div>

        {/* Desktop: Floating Sidebar on right */}
        <div className="hidden md:block absolute right-6 top-8 bottom-8 z-50 w-[420px] pointer-events-none">
          <div className="w-full h-full pointer-events-auto">
            <Sidebar />
          </div>
        </div>

        {/* Mobile: Full-screen panel overlay (slides over map) */}
        <div 
          className={`md:hidden absolute inset-0 z-40 bg-[#0d1117] transition-transform duration-300 ${
            showMap ? 'translate-x-full' : 'translate-x-0'
          }`}
        >
          {/* Mobile Header */}
          <div className="sticky top-0 z-10 px-4 py-3 border-b-2 border-accent/20 flex items-center justify-between bg-[#161b22] shadow-lg">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
                <span className="text-lg">🇮🇷</span>
              </div>
              <div>
                <h1 className="text-sm font-black text-white uppercase tracking-tight">IRI Assessment</h1>
                <div className="text-[9px] text-gray-500 uppercase">Real-Time Intelligence</div>
              </div>
            </div>
            <button 
              onClick={() => setShowMap(true)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-accent/20 border border-accent/30 active:bg-accent/30"
            >
              <span>🗺️</span>
              <span className="text-[10px] font-bold text-accent">MAP</span>
            </button>
          </div>
          {/* Scrollable content area */}
          <div className="h-[calc(100%-60px)] overflow-y-auto pb-24">
            <Sidebar isMobile />
          </div>
        </div>
      </div>

      {/* Mobile Bottom Navigation - always visible */}
      <MobileNav 
        onOpenSidebar={() => setSidebarOpen(true)}
        showMap={showMap}
        setShowMap={setShowMap}
      />
      
      <HelpModal />
    </div>
  )
}
