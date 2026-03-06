import { useEffect, useMemo, useState } from 'react'
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
  Popup,
  Marker,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
import { useTargets, useFullAssessment } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'
import { getTypeColor } from '../../utils/colors'

/* ── Check if mobile ────────────────────────────────────────────── */
const isMobile = () => window.innerWidth < 768

/* ── City labels for orientation ─────────────────────────────────── */
const CITY_LABELS = [
  { name: 'Tehran', lat: 35.6892, lon: 51.389 },
  { name: 'Isfahan', lat: 32.6546, lon: 51.668 },
  { name: 'Shiraz', lat: 29.5918, lon: 52.5837 },
  { name: 'Tabriz', lat: 38.08, lon: 46.2919 },
  { name: 'Mashhad', lat: 36.2972, lon: 59.6067 },
  { name: 'Ahvaz', lat: 31.3183, lon: 48.6706 },
  { name: 'Kermanshah', lat: 34.3142, lon: 47.065 },
  { name: 'Bandar Abbas', lat: 27.1865, lon: 56.2808 },
  { name: 'Bushehr', lat: 28.9234, lon: 50.8203 },
  { name: 'Qom', lat: 34.6401, lon: 50.8764 },
  { name: 'Arak', lat: 34.0917, lon: 49.6892 },
  { name: 'Hamadan', lat: 34.799, lon: 48.515 },
  { name: 'Kerman', lat: 30.2839, lon: 57.0834 },
  { name: 'Yazd', lat: 31.8974, lon: 54.3569 },
  { name: 'Semnan', lat: 35.5729, lon: 53.397 },
  { name: 'Rasht', lat: 37.2808, lon: 49.5832 },
  { name: 'Sanandaj', lat: 35.3219, lon: 46.9862 },
  { name: 'Zahedan', lat: 29.4963, lon: 60.8629 },
  { name: 'Chabahar', lat: 25.2919, lon: 60.643 },
  { name: 'Dezful', lat: 32.3838, lon: 48.4011 },
  { name: 'Karaj', lat: 35.84, lon: 50.9391 },
  { name: 'Urmia', lat: 37.5527, lon: 45.0761 },
  { name: 'Natanz', lat: 33.5131, lon: 51.9164 },
  { name: 'Fordow', lat: 34.7081, lon: 51.0263 },
  { name: 'Parchin', lat: 35.52, lon: 51.77 },
]

/* ── Component: react to store flyTo requests ────────────────────── */
function FlyToHandler() {
  const map = useMap()
  const mapFocus = useAppStore((s) => s.mapFocus)

  useEffect(() => {
    if (mapFocus) {
      map.flyTo([mapFocus.lat, mapFocus.lon], mapFocus.zoom, { duration: 1 })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapFocus?.ts])

  return null
}

/* ── Component: static city name labels ──────────────────────────── */
function CityLabels() {
  return (
    <>
      {CITY_LABELS.map((c) => (
        <Marker
          key={c.name}
          position={[c.lat, c.lon]}
          icon={L.divIcon({
            className: 'city-label',
            html: c.name,
            iconSize: [0, 0],
            iconAnchor: [-8, 8],
          })}
          interactive={false}
        />
      ))}
    </>
  )
}

/* ── Component: target + strike markers ──────────────────────────── */
function TargetMarkers() {
  const { data: targetData, isLoading } = useTargets()
  const { data: assessmentData } = useFullAssessment()
  const setSatTargetId = useAppStore((s) => s.setSatTargetId)
  const setActiveTab = useAppStore((s) => s.setActiveTab)

  const targets = targetData?.targets ?? []
  const assessments = assessmentData?.assessments ?? []
  const mobile = isMobile()

  const strikeMap = useMemo(() => {
    const m = new Map<string, (typeof assessments)[0]>()
    assessments.forEach((a) => m.set(a.target_id, a))
    return m
  }, [assessments])

  // On mobile, make markers bigger for touch
  const baseRadius = mobile ? 10 : 5
  const strikeRadius = mobile ? 14 : 8

  return (
    <>
      {targets.map((t) => {
        const strike = strikeMap.get(t.id)
        const isStrike = !!strike
        const color = isStrike
          ? (strike.combined_score ?? 0) >= 0.5
            ? '#f85149'
            : '#d29922'
          : getTypeColor(t.type)

        return (
          <CircleMarker
            key={t.id}
            center={[t.lat, t.lon]}
            radius={isStrike ? strikeRadius : baseRadius}
            pathOptions={{
              fillColor: color,
              color: '#fff',
              weight: mobile ? 2 : 1,
              fillOpacity: isStrike ? 0.9 : 0.75,
            }}
          >
            <Tooltip
              direction="top"
              offset={[0, -8]}
              className="target-label"
            >
              {t.name}
            </Tooltip>
            <Popup>
              <div style={{ minWidth: 200, fontFamily: 'sans-serif' }}>
                <div style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '6px' }}>
                  {t.name}
                </div>
                <div style={{ color: '#8b949e', fontSize: '12px', marginBottom: '8px' }}>
                  {t.type.replace(/_/g, ' ').toUpperCase()} • {t.province}
                </div>
                
                {isStrike && (
                  <div style={{ 
                    background: 'rgba(248,81,73,0.15)', 
                    padding: '8px', 
                    borderRadius: '6px',
                    marginBottom: '10px',
                    borderLeft: '3px solid #f85149'
                  }}>
                    <div style={{ color: '#f85149', fontWeight: 'bold', fontSize: '13px' }}>
                      ⚠️ Strike Detected: {Math.round((strike.combined_score ?? 0) * 100)}% confidence
                    </div>
                    <div style={{ color: '#d4d4d4', fontSize: '11px', marginTop: '4px' }}>
                      {strike.verdict ?? 'Under review'} • {strike.osint_sources ?? 0} sources
                    </div>
                  </div>
                )}
                
                {t.description && (
                  <div style={{ color: '#9e9e9e', fontSize: '11px', marginBottom: '8px' }}>
                    {t.description}
                  </div>
                )}
                
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault()
                    setSatTargetId(t.id)
                    setActiveTab('satellite')
                  }}
                  style={{ display: 'block' }}
                >
                  🛰️ View Satellite Imagery
                </a>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}

      {/* Pulsing dashed rings around high-confidence strikes */}
      {assessments
        .filter((s) => (s.combined_score ?? 0) >= 0.5 && s.lat && s.lon)
        .map((s) => (
          <CircleMarker
            key={`ring-${s.strike_id}`}
            center={[s.lat, s.lon]}
            radius={isMobile() ? 20 : 14}
            pathOptions={{
              fillColor: 'transparent',
              color: '#f85149',
              weight: 2,
              opacity: 0.6,
              dashArray: '4 4',
            }}
            interactive={false}
          />
        ))}
    </>
  )
}

/* ── Map Legend Component ────────────────────────────────────────── */
function MapLegend() {
  const [collapsed, setCollapsed] = useState(isMobile())
  
  const items = [
    { color: '#f85149', label: 'Confirmed Strike' },
    { color: '#d29922', label: 'Possible Strike' },
    { color: '#58a6ff', label: 'Nuclear Site' },
    { color: '#f97583', label: 'Military Base' },
    { color: '#a371f7', label: 'Air Defense' },
    { color: '#7ee787', label: 'Energy/Oil' },
  ]

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="absolute bottom-20 md:bottom-4 left-2 z-[1000] bg-card/90 text-white text-xs px-2 py-1 rounded shadow-lg border border-border"
      >
        📍 Legend
      </button>
    )
  }

  return (
    <div className="absolute bottom-20 md:bottom-4 left-2 z-[1000] bg-card/95 text-white text-xs p-2 rounded-lg shadow-lg border border-border max-w-[140px]">
      <div className="flex justify-between items-center mb-1.5">
        <span className="font-bold text-[10px]">MAP LEGEND</span>
        <button onClick={() => setCollapsed(true)} className="text-dim hover:text-white">✕</button>
      </div>
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5 py-0.5">
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-[10px] text-gray-300">{item.label}</span>
        </div>
      ))}
    </div>
  )
}

/* ── Instruction Overlay (shown on first visit) ──────────────────── */
function InstructionOverlay() {
  const [dismissed, setDismissed] = useState(() => {
    return sessionStorage.getItem('map-instructions-seen') === 'true'
  })

  const handleDismiss = () => {
    sessionStorage.setItem('map-instructions-seen', 'true')
    setDismissed(true)
  }

  if (dismissed) return null

  return (
    <div className="absolute inset-0 z-[999] flex items-center justify-center p-4 pointer-events-none">
      <div className="bg-card/95 border border-accent rounded-xl shadow-2xl p-4 md:p-5 max-w-xs pointer-events-auto">
        <h3 className="text-accent font-bold text-base md:text-lg mb-2 flex items-center gap-2">
          👆 How to Use
        </h3>
        <ol className="text-gray-300 text-sm space-y-2 mb-4">
          <li className="flex gap-2">
            <span className="text-accent font-bold">1.</span>
            <span><strong>Tap/click</strong> any colored marker on the map</span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent font-bold">2.</span>
            <span>A popup shows target info</span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent font-bold">3.</span>
            <span>Click <strong>"Fetch Satellite Imagery"</strong> to analyze</span>
          </li>
        </ol>
        <div className="text-[11px] text-dim mb-3">
          🔴 Red = Strike detected &nbsp; 🟡 Yellow = Possible &nbsp; 🔵 Blue = Target
        </div>
        <button
          onClick={handleDismiss}
          className="w-full bg-accent text-black font-bold py-2 rounded-lg text-sm hover:bg-accent/90 transition"
        >
          Got it!
        </button>
      </div>
    </div>
  )
}

/* ── Target Count Badge ──────────────────────────────────────────── */
function TargetCountBadge() {
  const { data, isLoading } = useTargets()
  const count = data?.count ?? 0
  
  return (
    <div className="absolute top-2 left-2 z-[1000] bg-card/90 text-white text-xs px-2.5 py-1.5 rounded-lg shadow border border-border">
      <span className="text-accent font-bold">{isLoading ? '...' : count}</span>
      <span className="text-dim ml-1">targets loaded</span>
    </div>
  )
}

/* ── Main MapView ────────────────────────────────────────────────── */
export function MapView() {
  const [mapReady, setMapReady] = useState(false)
  const mobile = isMobile()

  // Delay heavy components on mobile for faster initial paint
  useEffect(() => {
    if (mobile) {
      const timer = setTimeout(() => setMapReady(true), 100)
      return () => clearTimeout(timer)
    } else {
      setMapReady(true)
    }
  }, [mobile])

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={[32.5, 53]}
        zoom={mobile ? 5 : 6}
        style={{ width: '100%', height: '100%' }}
        zoomControl={!mobile}
        preferCanvas={true}
        touchZoom={true}
        dragging={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OSM &copy; CARTO'
          maxZoom={18}
          keepBuffer={mobile ? 2 : 4}
          updateWhenZooming={false}
          updateWhenIdle={true}
        />
        {/* Render markers only after map is ready */}
        {mapReady && (
          <>
            <CityLabels />
            <TargetMarkers />
          </>
        )}
        <FlyToHandler />
      </MapContainer>
      
      {/* Overlays outside the MapContainer */}
      <TargetCountBadge />
      <MapLegend />
      <InstructionOverlay />
    </div>
  )
}
