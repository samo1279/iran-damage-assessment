import { useState } from 'react'
import { TopBar } from './components/layout/TopBar'
import { StatsBar } from './components/layout/StatsBar'
import { Sidebar } from './components/layout/Sidebar'
import { MapView } from './components/map/MapView'
import { HelpModal } from './components/HelpModal'
import { MobileNav } from './components/layout/MobileNav'

export default function App() {
  const [showMap, setShowMap] = useState(true) // On mobile: show map or sidebar
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex flex-col h-screen">
      <TopBar />
      <StatsBar />
      
      {/* Desktop Layout */}
      <div className="hidden md:flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex-1 relative">
          <MapView />
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="flex md:hidden flex-1 flex-col overflow-hidden relative">
        {/* Map View */}
        <div className={`absolute inset-0 ${showMap ? 'block' : 'hidden'}`}>
          <MapView />
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
