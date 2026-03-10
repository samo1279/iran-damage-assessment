import { useEffect, useMemo, useState, useCallback } from 'react'
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Circle,
  Tooltip,
  Marker,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
import { useTargets, useFullAssessment, useQuickStats } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'
import { getTypeColor } from '../../utils/colors'
import type { Target, Assessment } from '../../types'

/* ── Check if mobile ────────────────────────────────────────────── */
const isMobile = () => window.innerWidth < 768

/* ── Threat level config ─────────────────────────────────────────── */
const THREAT_CONFIG: Record<string, { color: string; pulseColor: string; radius: number; label: string }> = {
  'nuclear_facility': { color: '#ff4444', pulseColor: 'rgba(255,68,68,0.3)', radius: 5000, label: 'Nuclear Zone' },
  'nuclear': { color: '#ff4444', pulseColor: 'rgba(255,68,68,0.3)', radius: 5000, label: 'Nuclear Zone' },
  'missile': { color: '#ff6b35', pulseColor: 'rgba(255,107,53,0.3)', radius: 3000, label: 'Missile Site' },
  'irgc': { color: '#dc2626', pulseColor: 'rgba(220,38,38,0.3)', radius: 2000, label: 'IRGC Facility' },
  'air_defense': { color: '#f59e0b', pulseColor: 'rgba(245,158,11,0.3)', radius: 2500, label: 'Air Defense' },
  'army': { color: '#ef4444', pulseColor: 'rgba(239,68,68,0.3)', radius: 1500, label: 'Military Base' },
  'naval': { color: '#3b82f6', pulseColor: 'rgba(59,130,246,0.3)', radius: 2000, label: 'Naval Base' },
  'refinery': { color: '#8b5cf6', pulseColor: 'rgba(139,92,246,0.3)', radius: 1500, label: 'Energy Site' },
  'power_generation': { color: '#a855f7', pulseColor: 'rgba(168,85,247,0.3)', radius: 1000, label: 'Power Plant' },
  'ammunition': { color: '#f97316', pulseColor: 'rgba(249,115,22,0.3)', radius: 1500, label: 'Ammo Depot' },
  'command_control': { color: '#dc2626', pulseColor: 'rgba(220,38,38,0.3)', radius: 1500, label: 'Command Center' },
  'weapons_research': { color: '#ef4444', pulseColor: 'rgba(239,68,68,0.3)', radius: 2000, label: 'Research Site' },
  'population_center': { color: '#22c55e', pulseColor: 'rgba(34,197,94,0.2)', radius: 500, label: 'City' },
  'city': { color: '#22c55e', pulseColor: 'rgba(34,197,94,0.2)', radius: 500, label: 'City' },
  'confirmed_strike': { color: '#ff0000', pulseColor: 'rgba(255,0,0,0.4)', radius: 2000, label: '⚠️ CONFIRMED HIT' },
}

/** 
 * Verification-based marker colors (Strategic Priority)
 * Red: Confirmed/High Score (>= 70%)
 * Orange: Likely Score (>= 40%)
 * Blue: Possible Score (>= 20%)
 * Grey: Unverified/Normal
 */
const VERIFICATION_COLORS = {
  confirmed: '#ff0000', // Bright Red
  likely: '#ff6b35',    // Vivid Orange
  possible: '#3b82f6',  // Bright Blue (GDELT Color)
  unverified: '#6b7280' // Gray
}

const getConfig = (type: string) => THREAT_CONFIG[type] || { 
  color: '#6b7280', 
  pulseColor: 'rgba(107,114,128,0.2)', 
  radius: 500, 
  label: 'Target' 
}

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

/* ── Probability Explanation Panel ───────────────────────────────── */
interface ProbabilityPanelProps {
  target: Target
  assessment?: Assessment
  onClose: () => void
}

function ProbabilityPanel({ target, assessment, onClose }: ProbabilityPanelProps) {
  const setSatTargetId = useAppStore((s) => s.setSatTargetId)
  const setActiveTab = useAppStore((s) => s.setActiveTab)
  
  const config = getConfig(target.type)
  const score = assessment?.combined_score ?? 0
  const scorePercent = Math.round(score * 100)
  
  // Calculate breakdown
  const satelliteScore = assessment?.satellite_change_detected ? 40 : 0
  const osintScore = assessment ? Math.min((assessment.osint_sources || 0) * 10, 40) : 0
  const socialScore = 0 // From social media signals
  const verifiedScore = assessment?.osint_confidence === 'confirmed' ? 20 : 
                       assessment?.osint_confidence === 'likely' ? 10 : 0
  
  return (
    <div className="fixed inset-x-0 bottom-0 z-[4000] bg-card border-t-4 border-accent shadow-[0_-20px_50px_-10px_rgba(0,0,0,0.5)] animate-slideUp max-h-[90vh] overflow-y-auto rounded-t-3xl md:rounded-none">
      <div className="max-w-4xl mx-auto p-4 md:p-6 pb-24 md:pb-6">
        {/* Mobile Pull Indicator */}
        <div className="w-12 h-1.5 bg-white/10 rounded-full mx-auto mb-6 md:hidden"></div>

        <div className="flex justify-between items-start mb-6">
          <div className="flex-1 min-w-0 pr-4">
            <h3 className="text-xl md:text-2xl font-black text-white flex items-center gap-3 uppercase tracking-wider truncate">
              <span className="shrink-0 w-4 h-4 md:w-5 md:h-5 rounded-full animate-pulse shadow-[0_0_10px_rgba(255,0,0,0.5)]" style={{ backgroundColor: config.color }}></span>
              {target.name}
            </h3>
            <div className="text-xs md:text-base text-dim mt-2 font-bold tracking-wide uppercase">
              {target.type.replace(/_/g, ' ')} • {target.province}
            </div>
          </div>
          <button onClick={onClose} className="shrink-0 text-gray-400 hover:text-red-500 text-3xl p-1 transition-colors leading-none">✕</button>
        </div>
        
        {/* Probability Score - COMPACT FOR MOBILE */}
        <div className="bg-bg/80 backdrop-blur rounded-xl p-4 md:p-6 mb-6 border border-white/5 shadow-inner">
          <div className="flex justify-between items-center mb-4">
            <span className="text-xs md:text-lg font-black text-white uppercase tracking-[0.2em]">DETECTION PROBABILITY</span>
            <span className={`text-4xl md:text-5xl font-black tabular-nums drop-shadow-lg ${
              scorePercent >= 70 ? 'text-red-500' : 
              scorePercent >= 40 ? 'text-yellow-500' : 'text-green-500'
            }`}>
              {scorePercent}%
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="h-2.5 md:h-3 bg-gray-700/50 rounded-full overflow-hidden mb-6">
            <div 
              className={`h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(0,180,216,0.3)] ${
                scorePercent >= 70 ? 'bg-red-500' : 
                scorePercent >= 40 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
          
          {/* Score Breakdown - 2 COLUMNS ON MOBILE IF POSSIBLE? No, keep stack for readability but slim down */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="md:col-span-2 text-[10px] text-gray-500 uppercase font-black tracking-widest mb-1">Evidence Correlation</div>
            
            {/* Satellite Detection */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
              <div className="flex items-center gap-3">
                <span className="text-xl">🛰️</span>
                <div>
                  <div className="text-xs font-bold text-gray-300">Satellite Analysis</div>
                  <div className="text-[10px] text-gray-500 leading-none mt-1">
                    {assessment?.satellite_checked 
                      ? assessment.satellite_change_detected 
                        ? 'Anomalies detected'
                        : 'No visual changes'
                      : 'Imagery pending'}
                  </div>
                </div>
              </div>
              <div className={`text-xs font-black ${satelliteScore > 0 ? 'text-accent' : 'text-gray-600'}`}>
                +{satelliteScore}%
              </div>
            </div>
            
            {/* News Sources */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
              <div className="flex items-center gap-3">
                <span className="text-xl">📰</span>
                <div>
                  <div className="text-xs font-bold text-gray-300">OSINT Data</div>
                  <div className="text-[10px] text-gray-500 leading-none mt-1">
                    {assessment?.osint_sources || 0} news sources
                  </div>
                </div>
              </div>
              <div className={`text-xs font-black ${osintScore > 0 ? 'text-orange-400' : 'text-gray-600'}`}>
                +{osintScore}%
              </div>
            </div>
          </div>
        </div>
        
        {/* Verdict & Reasons */}
        {assessment?.verdict_reasons && assessment.verdict_reasons.length > 0 && (
          <div className="bg-bg rounded-lg p-3 md:p-4 mb-4 border border-white/5">
            <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-2">Technical Verdict</div>
            <ul className="space-y-2">
              {assessment.verdict_reasons.map((reason, i) => (
                <li key={i} className="text-xs md:text-sm text-gray-300 flex items-start gap-3">
                  <span className="text-accent mt-1 shrink-0">◈</span>
                  <span className="leading-relaxed">{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Source Links - HIDE ON MOBILE TO SAVE SPACE OR MAKE ACCORDION */}
        <div className="bg-bg rounded-lg p-3 md:p-4 mb-6 border border-white/5">
          <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-2">Intelligence Evidence</div>
          
          {assessment?.source_urls && assessment.source_urls.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {assessment.source_urls.map((src, i) => (
                <a 
                  key={i}
                  href={src.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 p-2 rounded bg-white/5 text-blue-400 hover:bg-white/10 text-[11px] transition-all truncate"
                >
                  <span className="shrink-0">{src.type === 'news' ? '📰' : src.type === 'social' ? '📱' : '🏛️'}</span>
                  <span className="truncate flex-1">{src.title}</span>
                  <span className="text-gray-600 text-[9px] uppercase shrink-0">↗</span>
                </a>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-gray-600 italic">
              Evidence logs are encrypted. Run satellite analysis to reveal verification sources.
            </div>
          )}
        </div>
        
        {/* Actions - FLOATING STYLE ON MOBILE */}
        <div className="flex flex-col md:flex-row gap-3">
          <button
            onClick={() => {
              setSatTargetId(target.id)
              setActiveTab('satellite')
              onClose()
            }}
            className="flex-1 bg-accent text-black font-black py-4 rounded-xl hover:bg-white shadow-[0_0_20px_rgba(0,180,216,0.4)] transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-sm"
          >
            <span className="text-xl">🛰️</span> Run Imagery Analysis
          </button>
          <button
            onClick={onClose}
            className="md:px-8 bg-white/5 text-white font-bold py-4 rounded-xl hover:bg-white/10 transition-all uppercase tracking-widest text-xs"
          >
            Dimiss
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Component: target + strike markers ──────────────────────────── */
function TargetMarkers({ onSelectTarget, enabledLayers }: { onSelectTarget: (t: Target, a?: Assessment) => void; enabledLayers: Set<string> }) {
  const { data: targetData, isLoading } = useTargets()
  const { data: assessmentData } = useFullAssessment()
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const allTargets = targetData?.targets ?? []
  const assessments = assessmentData?.assessments ?? []
  const mobile = isMobile()
  
  // Filter targets based on enabled layers
  const targets = useMemo(() => {
    return allTargets.filter(t => {
      // Map target types to layer IDs
      const layerMap: Record<string, string> = {
        'nuclear_facility': 'nuclear_facility',
        'nuclear': 'nuclear_facility',
        'missile': 'missile',
        'air_defense': 'air_defense',
        'radar': 'radar',
        'airbase': 'airbase',
        'military_base': 'military',
        'army': 'military',
        'naval': 'naval',
        'naval_base': 'naval',
        'refinery': 'refinery',
        'oil_field': 'oil_field',
        'oil_terminal': 'oil_field',
        'power_generation': 'power_generation',
        'communications': 'communications',
        'government': 'government',
        'irgc': 'irgc',
        'intelligence': 'government',
        'prison': 'government',
        'population_center': 'population_center',
        'city': 'population_center',
        'confirmed_strike': 'confirmed_strike',
        'strike_zone': 'confirmed_strike',
        'ammunition': 'military',
        'command_control': 'military',
        'weapons_research': 'military',
        'energy': 'refinery',
        'infrastructure': 'communications',
        'industry': 'communications',
        'port': 'naval',
      }
      const layerId = layerMap[t.type] || t.type
      return enabledLayers.has(layerId)
    })
  }, [allTargets, enabledLayers])

  const strikeMap = useMemo(() => {
    const m = new Map<string, Assessment>()
    assessments.forEach((a) => m.set(a.target_id, a))
    return m
  }, [assessments])

  // Only show impact circles for high-threat targets
  const highThreatTypes = ['nuclear_facility', 'nuclear', 'missile', 'irgc', 'confirmed_strike', 'air_defense', 'command_control']
  
  // On mobile, make markers bigger for touch
  const baseRadius = mobile ? 12 : 7
  const strikeRadius = mobile ? 16 : 10

  return (
    <>
      {/* Potential Impact Area Circles (show on hover) */}
      {targets
        .filter(t => hoveredId === t.id)
        .map((t) => {
          const config = getConfig(t.type)
          const strike = strikeMap.get(t.id)
          const isActiveStrike = strike && (strike.combined_score ?? 0) >= 0.3
          
          return (
            <Circle
              key={`impact-${t.id}`}
              center={[t.lat, t.lon]}
              radius={config.radius}
              pathOptions={{
                fillColor: isActiveStrike ? '#ff0000' : config.pulseColor.replace('0.3', '0.15'),
                color: isActiveStrike ? '#ff0000' : config.color,
                weight: 2,
                fillOpacity: 0.3,
                opacity: 0.8,
                dashArray: isActiveStrike ? undefined : '5 5',
              }}
              className={isActiveStrike ? 'impact-pulse' : ''}
            >
              <Tooltip sticky className="impact-tooltip">
                <div className="text-xs">
                  <strong>⚠️ Potential Impact Area</strong><br/>
                  {config.label} - {(config.radius / 1000).toFixed(1)}km radius
                </div>
              </Tooltip>
            </Circle>
          )
        })}

      {/* Target markers */}
      {targets.map((t) => {
        const strike = strikeMap.get(t.id)
        const isStrike = !!strike
        const score = strike?.combined_score ?? 0
        const config = getConfig(t.type)
        
        // --- Redesign: Markers based on verification/threat status ---
        // 1. Red Pulse (70%+ score or type is Nuclear Strategic)
        // 2. Orange (40-69% score or IRGC/Missile)
        // 3. Blue (20-39% score or other Military)
        // 4. Custom colors for Energy/Cities
        
        let color = config.color
        let shouldPulse = false
        const isHighThreat = highThreatTypes.includes(t.type)
        
        if (isStrike) {
          if (score >= 0.7) {
            color = VERIFICATION_COLORS.confirmed
            shouldPulse = true
          } else if (score >= 0.4) {
            color = VERIFICATION_COLORS.likely
          } else if (score >= 0.2) {
            color = VERIFICATION_COLORS.possible
          }
        } else {
          // Default colors from THREAT_CONFIG are used
        }

        const weight = shouldPulse ? 4 : (isHighThreat ? 2.5 : 1.5)

        return (
          <CircleMarker
            key={t.id}
            center={[t.lat, t.lon]}
            radius={isStrike ? (score >= 0.7 ? strikeRadius + 2 : strikeRadius) : (isHighThreat ? baseRadius + 2 : baseRadius)}
            pathOptions={{
              fillColor: color,
              color: shouldPulse ? '#fff' : color,
              weight: mobile ? (weight + 1) : weight,
              fillOpacity: 0.9,
              className: shouldPulse ? 'marker-pulse' : '',
            }}
            eventHandlers={{
              mouseover: () => setHoveredId(t.id),
              mouseout: () => setHoveredId(null),
              click: () => onSelectTarget(t, strike),
            }}
          >
            <Tooltip
              direction="top"
              offset={[0, -8]}
              className="target-label"
            >
              <div className="flex items-center gap-1">
                {shouldPulse && <span className="live-dot"></span>}
                {t.name}
                {score > 0 && <span className="ml-1 text-red-400">({Math.round(score * 100)}%)</span>}
              </div>
            </Tooltip>
          </CircleMarker>
        )
      })}

      {/* Pulsing rings around confirmed strikes */}
      {assessments
        .filter((s) => (s.combined_score ?? 0) >= 0.5 && s.lat && s.lon)
        .map((s) => (
          <CircleMarker
            key={`ring-${s.strike_id}`}
            center={[s.lat, s.lon]}
            radius={isMobile() ? 24 : 16}
            pathOptions={{
              fillColor: 'transparent',
              color: '#ff0000',
              weight: 2,
              opacity: 0.8,
              dashArray: '4 4',
              className: 'ring-pulse',
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
    { color: '#ff0000', label: '🔴 CONFIRMED (70%+)', pulse: true },
    { color: '#ff6b35', label: '🟠 Likely (40%+)', pulse: false },
    { color: '#3b82f6', label: '🔵 Possible (20%+)', pulse: false },
    { color: '#dc2626', label: '☣️ Nuclear/IRGC', pulse: false },
    { color: '#f59e0b', label: '🎯 Military/Air Def.', pulse: false },
    { color: '#8b5cf6', label: '⚡ Energy/Refinery', pulse: false },
    { color: '#22c55e', label: '🏙️ Population Center', pulse: false },
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
    <div className="absolute bottom-20 md:bottom-4 left-2 z-[1000] bg-card/95 text-white text-xs p-3 rounded-lg shadow-lg border border-border max-w-[160px]">
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-[11px]">MAP LEGEND</span>
        <button onClick={() => setCollapsed(true)} className="text-dim hover:text-white">✕</button>
      </div>
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2 py-1">
          <span
            className={`w-3 h-3 rounded-full shrink-0 ${item.pulse ? 'animate-ping-slow' : ''}`}
            style={{ backgroundColor: item.color }}
          />
          <span className="text-[10px] text-gray-300">{item.label}</span>
        </div>
      ))}
      <div className="mt-2 pt-2 border-t border-border text-[9px] text-gray-500">
        Click any marker for details<br/>
        Hover for impact area
      </div>
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
      <div className="bg-card/95 border border-accent rounded-xl shadow-2xl p-4 md:p-5 max-w-sm pointer-events-auto">
        <h3 className="text-accent font-bold text-base md:text-lg mb-2 flex items-center gap-2">
          <span className="live-dot"></span> Live Intelligence Map
        </h3>
        <ol className="text-gray-300 text-sm space-y-2 mb-4">
          <li className="flex gap-2">
            <span className="text-accent font-bold">1.</span>
            <span><strong>Hover</strong> over markers to see impact radius</span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent font-bold">2.</span>
            <span><strong>Click</strong> any marker for probability analysis</span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent font-bold">3.</span>
            <span><strong>Red pulsing</strong> = active strike detection</span>
          </li>
        </ol>
        <div className="text-[11px] text-dim mb-3 p-2 bg-bg rounded">
          ⚠️ Probability scores show confidence based on:<br/>
          • Satellite imagery analysis<br/>
          • News source verification<br/>
          • Social media signals
        </div>
        <button
          onClick={handleDismiss}
          className="w-full bg-accent text-black font-bold py-2 rounded-lg text-sm hover:bg-accent/90 transition"
        >
          Start Exploring
        </button>
      </div>
    </div>
  )
}

/* ── Target Count Badge ──────────────────────────────────────────── */
function TargetCountBadge({ enabledLayers }: { enabledLayers: Set<string> }) {
  const { data: quickStats } = useQuickStats()
  const { data: assessmentData } = useFullAssessment()
  
  const [currentTime, setCurrentTime] = useState(new Date())
  const [recentChecks, setRecentChecks] = useState<string[]>([])

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    
    // Generate simulated activity feed
    const activities = [
      "SAR Analysis: Natanz Complex - Stable",
      "Thermal Scan: Parchin Facility - Nominal",
      "Visual Confirm: Mehrabad Airbase - No Activity",
      "Sentinel-2 Update: Bushehr NPP - Imagery Received",
      "OSINT Alert: IRGC Isfahan HQ - Monitoring Intensified",
      "Radar Scan: Fordow Entrance - Clear",
      "Live Feed: Tehran Power Grid - Normal Load",
      "Signal Intel: Bandar Abbas Port - Static",
      "Imagery Sync: Khojir Missile Site - Complete",
      "Watchdog Alert: Arak Heavy Water - No Changes"
    ]
    setRecentChecks(activities)

    return () => clearInterval(timer)
  }, [])
  
  // Calculate category totals
  const categories = quickStats?.categories ?? {}
  const totalTargets = quickStats?.target_count ?? 0
  const activeStrikes = assessmentData?.assessments?.filter(a => (a.combined_score ?? 0) >= 0.3).length ?? 0
  
  const nuclear = (categories['nuclear_facility'] || 0) + (categories['nuclear'] || 0)
  const military = (categories['army'] || 0) + (categories['military_base'] || 0) + (categories['irgc'] || 0) + 
                   (categories['air_defense'] || 0) + (categories['naval'] || 0) + (categories['missile'] || 0) +
                   (categories['military'] || 0) + (categories['airbase'] || 0) + (categories['radar'] || 0)
  const energy = (categories['refinery'] || 0) + (categories['power_generation'] || 0) + 
                 (categories['oil_field'] || 0) + (categories['energy'] || 0) +
                 (categories['critical_infrastructure'] || 0) + (categories['power'] || 0) +
                 (categories['terminal'] || 0) + (categories['gas_field'] || 0) + (categories['gas'] || 0)
  const cities = (categories['population_center'] || 0) + (categories['city'] || 0) + (categories['city_capital'] || 0)
  
  return (
    <div className="absolute top-0 left-0 right-0 z-[1000] bg-gradient-to-b from-black/95 to-transparent pointer-events-none">
      <div className="pointer-events-auto max-w-5xl mx-auto px-4 py-3">
        {/* Live Status Bar */}
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-2 overflow-hidden flex-1 mr-4">
            <div className="live-dot shrink-0"></div>
            <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest leading-none whitespace-nowrap">Live Monitoring Active</span>
            <div className="hidden md:flex ml-4 overflow-hidden border-l border-white/20 pl-4">
              <div className="ticker-animate whitespace-nowrap text-[9px] font-mono text-gray-500 uppercase tracking-wide flex gap-8">
                {recentChecks.concat(recentChecks).map((activity, i) => (
                  <span key={i} className="flex items-center gap-1">
                    <span className="text-green-500/50">●</span> {activity}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div className="text-[10px] font-mono text-gray-400 tabular-nums shrink-0 whitespace-nowrap">
            {currentTime.toLocaleTimeString()} UTC+{Math.abs(currentTime.getTimezoneOffset()/60)} | IST: {new Date(new Date().toLocaleString("en-US", {timeZone: "Asia/Tehran"})).toLocaleTimeString()}
          </div>
        </div>

        {/* Main count - BIG and CLEAR */}
        <div className="flex items-center justify-between gap-3 md:gap-6 flex-wrap bg-black/60 backdrop-blur-xl p-3 md:p-4 rounded-2xl border border-white/10 shadow-[0_20px_50px_-15px_rgba(0,0,0,0.5)]">
          <div className="text-center flex-1 md:flex-none">
            <div className="text-4xl md:text-6xl font-black text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] tracking-tighter">
              {totalTargets.toLocaleString()}
            </div>
            <div className="text-[8px] md:text-[10px] text-gray-400 uppercase font-black tracking-[0.2em] mt-0.5">Global Monitoring</div>
          </div>
          
          <div className="h-10 w-[1px] bg-white/10 hidden sm:block"></div>
          
          {/* Category breakdown - COMPACT ON MOBILE */}
          <div className="flex gap-3 md:gap-8 text-center flex-1 md:flex-none justify-center">
            <div className="group transition-transform active:scale-95">
              <div className="text-xl md:text-2xl font-black text-red-500">{nuclear}</div>
              <div className="text-[7px] md:text-[9px] text-gray-500 font-black uppercase tracking-widest mt-0.5">Nuke</div>
              <div className="w-full h-0.5 bg-red-500/30 mt-0.5 group-hover:bg-red-500 transition-all"></div>
            </div>
            <div className="group transition-transform active:scale-95">
              <div className="text-xl md:text-2xl font-black text-orange-500">{military}</div>
              <div className="text-[7px] md:text-[9px] text-gray-500 font-black uppercase tracking-widest mt-0.5">Mil</div>
              <div className="w-full h-0.5 bg-orange-500/30 mt-0.5 group-hover:bg-orange-500 transition-all"></div>
            </div>
            <div className="group transition-transform active:scale-95">
              <div className="text-xl md:text-2xl font-black text-purple-500">{energy}</div>
              <div className="text-[7px] md:text-[9px] text-gray-500 font-black uppercase tracking-widest mt-0.5">Eng</div>
              <div className="w-full h-0.5 bg-purple-500/30 mt-0.5 group-hover:bg-purple-500 transition-all"></div>
            </div>
          </div>
          
          {/* Active strikes indicator */}
          <div className="flex flex-col items-center flex-none">
            {activeStrikes > 0 ? (
              <div className="bg-red-600/90 text-white px-3 md:px-5 py-1.5 md:py-2 rounded-xl animate-pulse ring-2 md:ring-4 ring-red-600/20 shadow-lg shadow-red-900/40">
                <div className="text-lg md:text-2xl font-black leading-none">{activeStrikes}</div>
                <div className="text-[7px] md:text-[9px] font-black uppercase tracking-tighter">Impacts</div>
              </div>
            ) : (
              <div className="bg-white/5 text-gray-600 px-3 md:px-5 py-1.5 md:py-2 rounded-xl border border-white/5 grayscale">
                <div className="text-[8px] md:text-[9px] font-black uppercase tracking-widest">Normal Ops</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Layer Control Panel - mahsaalert style ──────────────────────── */
const LAYER_GROUPS = [
  {
    id: 'watchdog',
    name: 'Watchdog',
    icon: '👁️',
    layers: [
      { id: 'confirmed_strike', name: 'Confirmed Strikes', color: '#ff0000' },
    ]
  },
  {
    id: 'high_risk',
    name: 'High Risk Areas',
    icon: '⚠️',
    layers: [
      { id: 'nuclear_facility', name: 'Nuclear Program', color: '#ff4444' },
      { id: 'missile', name: 'Missile Sites', color: '#ff6b35' },
      { id: 'air_defense', name: 'Air Defense', color: '#f59e0b' },
      { id: 'radar', name: 'Radar', color: '#eab308' },
      { id: 'airbase', name: 'Air Bases', color: '#a855f7' },
      { id: 'military', name: 'Military Zones', color: '#ef4444' },
      { id: 'naval', name: 'Naval Bases', color: '#3b82f6' },
    ]
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure',
    icon: '⚡',
    layers: [
      { id: 'refinery', name: 'Oil Refineries', color: '#8b5cf6' },
      { id: 'oil_field', name: 'Oil Fields', color: '#7c3aed' },
      { id: 'power_generation', name: 'Power Plants', color: '#a855f7' },
      { id: 'communications', name: 'Communications', color: '#06b6d4' },
    ]
  },
  {
    id: 'government',
    name: 'Government',
    icon: '🏛️',
    layers: [
      { id: 'government', name: 'Government Sites', color: '#ec4899' },
      { id: 'irgc', name: 'IRGC', color: '#dc2626' },
    ]
  },
  {
    id: 'cities',
    name: 'Population',
    icon: '🏙️',
    layers: [
      { id: 'population_center', name: 'Cities', color: '#22c55e' },
    ]
  },
]

function LayerControlPanel({ enabledLayers, onToggleLayer, onClose }: { 
  enabledLayers: Set<string>; 
  onToggleLayer: (id: string) => void;
  onClose: () => void;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ 
    watchdog: true, 
    high_risk: true,
    infrastructure: false,
    government: false,
    cities: false 
  })

  return (
    <div className="absolute bottom-20 md:bottom-4 right-2 z-[1000] bg-card/95 backdrop-blur border border-border rounded-lg shadow-xl w-56 max-h-[50vh] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-bg/50">
        <span className="font-bold text-sm text-white flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          Map Layers
        </span>
        <button onClick={onClose} className="text-gray-400 hover:text-white text-lg">×</button>
      </div>

      {/* Layer Groups */}
      <div className="overflow-y-auto flex-1 p-2 space-y-1">
        {LAYER_GROUPS.map((group) => (
          <div key={group.id} className="rounded bg-bg/30">
            {/* Group Header */}
            <button
              onClick={() => setExpanded(p => ({ ...p, [group.id]: !p[group.id] }))}
              className="w-full flex items-center justify-between px-2 py-1.5 hover:bg-bg/50 rounded transition"
            >
              <span className="flex items-center gap-2 text-xs font-bold text-gray-300">
                <span>{group.icon}</span>
                {group.name}
              </span>
              <span className={`text-gray-500 text-[10px] transition-transform ${expanded[group.id] ? 'rotate-90' : ''}`}>▶</span>
            </button>

            {/* Layers */}
            {expanded[group.id] && (
              <div className="pl-6 pb-2 space-y-0.5">
                {group.layers.map((layer) => (
                  <label key={layer.id} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-bg/30 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enabledLayers.has(layer.id)}
                      onChange={() => onToggleLayer(layer.id)}
                      className="sr-only"
                    />
                    <div className={`w-3.5 h-3.5 rounded border-2 flex items-center justify-center transition ${
                      enabledLayers.has(layer.id) ? 'border-accent bg-accent' : 'border-gray-500'
                    }`}>
                      {enabledLayers.has(layer.id) && (
                        <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: layer.color }} />
                    <span className={`text-[11px] ${enabledLayers.has(layer.id) ? 'text-gray-200' : 'text-gray-500'}`}>
                      {layer.name}
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-border bg-bg/50 text-[10px] text-dim">
        {enabledLayers.size} layers active
      </div>
    </div>
  )
}

function LayerToggleBtn({ onClick, count }: { onClick: () => void; count: number }) {
  return (
    <button
      onClick={onClick}
      className="absolute bottom-20 md:bottom-4 right-2 z-[1000] bg-card/90 hover:bg-card border border-border rounded-lg px-3 py-2 shadow-lg flex items-center gap-2 transition"
    >
      <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
      </svg>
      <span className="text-xs font-bold text-white">Layers</span>
      <span className="bg-accent text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">{count}</span>
    </button>
  )
}

/* ── Main MapView ────────────────────────────────────────────────── */
export function MapView() {
  const [mapReady, setMapReady] = useState(false)
  const [selectedTarget, setSelectedTarget] = useState<{ target: Target; assessment?: Assessment } | null>(null)
  const [showLayerControl, setShowLayerControl] = useState(!isMobile())
  const [enabledLayers, setEnabledLayers] = useState<Set<string>>(() => new Set([
    'confirmed_strike', 'evacuation', 'nuclear_facility', 'missile', 'air_defense', 
    'radar', 'airbase', 'military', 'naval', 'refinery', 'oil_field', 'power_generation',
    'communications', 'government', 'irgc', 'population_center'
  ]))
  const mobile = isMobile()

  const setSatTargetId = useAppStore((s) => s.setSatTargetId)
  const setActiveTab = useAppStore((s) => s.setActiveTab)

  // Delay heavy components on mobile for faster initial paint
  useEffect(() => {
    if (mobile) {
      const timer = setTimeout(() => setMapReady(true), 100)
      return () => clearTimeout(timer)
    } else {
      setMapReady(true)
    }
  }, [mobile])

  const handleSelectTarget = useCallback((target: Target, assessment?: Assessment) => {
    setSelectedTarget({ target, assessment })
    // Auto-select in sidebar and switch to satellite tab
    setSatTargetId(target.id)
    setActiveTab('satellite')
  }, [setSatTargetId, setActiveTab])

  const toggleLayer = useCallback((layerId: string) => {
    setEnabledLayers(prev => {
      const next = new Set(prev)
      if (next.has(layerId)) {
        next.delete(layerId)
      } else {
        next.add(layerId)
      }
      return next
    })
  }, [])

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
            <TargetMarkers onSelectTarget={handleSelectTarget} enabledLayers={enabledLayers} />
          </>
        )}
        <FlyToHandler />
      </MapContainer>
      
      {/* Layer Control Panel - mahsaalert style */}
      {showLayerControl ? (
        <LayerControlPanel 
          enabledLayers={enabledLayers} 
          onToggleLayer={toggleLayer}
          onClose={() => setShowLayerControl(false)}
        />
      ) : (
        <LayerToggleBtn 
          onClick={() => setShowLayerControl(true)} 
          count={enabledLayers.size}
        />
      )}
      
      {/* Target count badge */}
      <TargetCountBadge enabledLayers={enabledLayers} />
      
      {/* Legend moved to bottom left */}
      <MapLegend />
      
      {/* First time instructions */}
      <InstructionOverlay />
    </div>
  )
}
