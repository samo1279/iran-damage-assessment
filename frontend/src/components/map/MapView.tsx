import { useEffect, useMemo, useState, useCallback } from 'react'
import { createPortal } from 'react-dom'
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
const THREAT_CONFIG: Record<string, { color: string; pulseColor: string; radius: number; label: string; emoji: string }> = {
  'nuclear_facility': { color: '#ff4444', pulseColor: 'rgba(255,68,68,0.3)', radius: 5000, label: 'Nuclear Zone', emoji: '☢️' },
  'nuclear': { color: '#ff4444', pulseColor: 'rgba(255,68,68,0.3)', radius: 5000, label: 'Nuclear Zone', emoji: '☢️' },
  'missile': { color: '#ff6b35', pulseColor: 'rgba(255,107,53,0.3)', radius: 3000, label: 'Missile Site', emoji: '🚀' },
  'irgc': { color: '#dc2626', pulseColor: 'rgba(220,38,38,0.3)', radius: 2000, label: 'IRGC Facility', emoji: '⚔️' },
  'air_defense': { color: '#f59e0b', pulseColor: 'rgba(245,158,11,0.3)', radius: 2500, label: 'Air Defense', emoji: '🛡️' },
  'army': { color: '#ef4444', pulseColor: 'rgba(239,68,68,0.3)', radius: 1500, label: 'Military Base', emoji: '🎖️' },
  'naval': { color: '#3b82f6', pulseColor: 'rgba(59,130,246,0.3)', radius: 2000, label: 'Naval Base', emoji: '⚓' },
  'refinery': { color: '#8b5cf6', pulseColor: 'rgba(139,92,246,0.3)', radius: 1500, label: 'Energy Site', emoji: '🛢️' },
  'power_generation': { color: '#a855f7', pulseColor: 'rgba(168,85,247,0.3)', radius: 1000, label: 'Power Plant', emoji: '⚡' },
  'ammunition': { color: '#f97316', pulseColor: 'rgba(249,115,22,0.3)', radius: 1500, label: 'Ammo Depot', emoji: '💣' },
  'command_control': { color: '#dc2626', pulseColor: 'rgba(220,38,38,0.3)', radius: 1500, label: 'Command Center', emoji: '📡' },
  'weapons_research': { color: '#ef4444', pulseColor: 'rgba(239,68,68,0.3)', radius: 2000, label: 'Research Site', emoji: '🔬' },
  'population_center': { color: '#22c55e', pulseColor: 'rgba(34,197,94,0.2)', radius: 500, label: 'City', emoji: '🏙️' },
  'city': { color: '#22c55e', pulseColor: 'rgba(34,197,94,0.2)', radius: 500, label: 'City', emoji: '🏙️' },
  'confirmed_strike': { color: '#ff0000', pulseColor: 'rgba(255,0,0,0.4)', radius: 2000, label: '⚠️ CONFIRMED HIT', emoji: '💥' },
}

const VERIFICATION_COLORS = {
  confirmed: '#ff0000',
  likely: '#ff6b35',
  possible: '#3b82f6',
  unverified: '#6b7280'
}

const getConfig = (type: string) => THREAT_CONFIG[type] || { 
  color: '#6b7280', 
  pulseColor: 'rgba(107,114,128,0.2)', 
  radius: 500, 
  label: 'Target',
  emoji: '📍'
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

/* ── Analysis Panel (appears when clicking a target) ─────────────── */
interface AnalysisPanelProps {
  target: Target
  assessment?: Assessment
  onClose: () => void
}

function AnalysisPanel({ target, assessment, onClose }: AnalysisPanelProps) {
  const config = getConfig(target.type)
  const score = assessment?.combined_score ?? 0
  const scorePercent = Math.round(score * 100)

  return createPortal(
    <div className="fixed inset-0 z-[99999] flex items-end justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      
      {/* Panel */}
      <div className="relative w-full max-w-lg bg-[#1a1a2e] border-t-4 border-red-500 rounded-t-3xl shadow-2xl animate-slideUp max-h-[80vh] overflow-y-auto">
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-12 h-1.5 bg-white/20 rounded-full" />
        </div>

        <div className="px-5 pb-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-2xl">{config.emoji}</span>
                <span className="w-3 h-3 rounded-full animate-pulse" style={{ backgroundColor: config.color }} />
              </div>
              <h3 className="text-xl font-bold text-white">{target.name}</h3>
              <p className="text-sm text-gray-400">{target.type.replace(/_/g, ' ')} • {target.province}</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl p-1">×</button>
          </div>

          {/* Score */}
          <div className="bg-black/40 rounded-xl p-4 mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-bold text-gray-400 uppercase tracking-wider">Detection Score</span>
              <span className={`text-3xl font-black ${
                scorePercent >= 70 ? 'text-red-500' : 
                scorePercent >= 40 ? 'text-yellow-500' : 'text-green-500'
              }`}>
                {scorePercent}%
              </span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all ${
                  scorePercent >= 70 ? 'bg-red-500' : 
                  scorePercent >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${scorePercent}%` }}
              />
            </div>
          </div>

          {/* Info Grid */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-black/30 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-1">🛰️ Satellite</div>
              <div className="text-sm font-bold text-white">
                {assessment?.satellite_checked 
                  ? assessment.satellite_change_detected ? 'Changes Detected' : 'No Changes'
                  : 'Pending Analysis'}
              </div>
            </div>
            <div className="bg-black/30 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-1">📰 OSINT</div>
              <div className="text-sm font-bold text-white">
                {assessment?.osint_sources || 0} Sources
              </div>
            </div>
          </div>

          {/* Coordinates */}
          <div className="text-xs text-gray-500 text-center mb-4">
            📍 {target.lat.toFixed(4)}, {target.lon.toFixed(4)}
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="w-full bg-red-600 text-white font-bold py-3 rounded-xl hover:bg-red-500 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}

/* ── Component: target markers ───────────────────────────────────── */
function TargetMarkers({ onSelectTarget, enabledLayers }: { onSelectTarget: (t: Target, a?: Assessment) => void; enabledLayers: Set<string> }) {
  const { data: targetData, isLoading } = useTargets()
  const { data: assessmentData } = useFullAssessment()
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const allTargets = targetData?.targets ?? []
  const assessments = assessmentData?.assessments ?? []
  const mobile = isMobile()
  
  const targets = useMemo(() => {
    return allTargets.filter(t => {
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
        'refinery': 'refinery',
        'oil_field': 'oil_field',
        'power_generation': 'power_generation',
        'communications': 'communications',
        'government': 'government',
        'irgc': 'irgc',
        'population_center': 'population_center',
        'city': 'population_center',
        'confirmed_strike': 'confirmed_strike',
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

  const highThreatTypes = ['nuclear_facility', 'nuclear', 'missile', 'irgc', 'confirmed_strike', 'air_defense', 'command_control']
  const baseRadius = mobile ? 10 : 6
  const strikeRadius = mobile ? 14 : 9

  return (
    <>
      {/* Impact circles on hover */}
      {targets.filter(t => hoveredId === t.id).map((t) => {
        const config = getConfig(t.type)
        const strike = strikeMap.get(t.id)
        const isActiveStrike = strike && (strike.combined_score ?? 0) >= 0.3
          
        return (
          <Circle
            key={`impact-${t.id}`}
            center={[t.lat, t.lon]}
            radius={config.radius}
            pathOptions={{
              fillColor: isActiveStrike ? '#ff0000' : config.pulseColor,
              color: isActiveStrike ? '#ff0000' : config.color,
              weight: 2,
              fillOpacity: 0.3,
              opacity: 0.8,
              dashArray: isActiveStrike ? undefined : '5 5',
            }}
          >
            <Tooltip sticky className="impact-tooltip">
              <div className="text-xs">
                <strong>⚠️ Impact Zone</strong><br/>
                {config.label} - {(config.radius / 1000).toFixed(1)}km
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
            <Tooltip direction="top" offset={[0, -8]} className="target-label">
              <div className="flex items-center gap-1">
                {shouldPulse && <span className="live-dot"></span>}
                {t.name}
                {score > 0 && <span className="ml-1 text-red-400">({Math.round(score * 100)}%)</span>}
              </div>
            </Tooltip>
          </CircleMarker>
        )
      })}

      {/* Pulsing rings for confirmed strikes */}
      {assessments
        .filter((s) => (s.combined_score ?? 0) >= 0.5 && s.lat && s.lon)
        .map((s) => (
          <CircleMarker
            key={`ring-${s.strike_id}`}
            center={[s.lat, s.lon]}
            radius={mobile ? 20 : 14}
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

/* ── Layer Control (mahsaalert style - right sidebar) ─────────────── */
const LAYER_GROUPS = [
  {
    id: 'watchdog',
    name: 'دیدبان',
    nameEn: 'Watchdog',
    layers: [
      { id: 'confirmed_strike', name: 'حملات تایید شده', nameEn: 'Confirmed Strikes', color: '#ff0000', emoji: '💥' },
    ]
  },
  {
    id: 'high_risk',
    name: 'مناطق پرخطر',
    nameEn: 'High Risk',
    layers: [
      { id: 'nuclear_facility', name: 'برنامه هسته‌ای', nameEn: 'Nuclear', color: '#ff4444', emoji: '☢️' },
      { id: 'missile', name: 'برنامه موشکی', nameEn: 'Missiles', color: '#ff6b35', emoji: '🚀' },
      { id: 'air_defense', name: 'پدافند هوایی', nameEn: 'Air Defense', color: '#f59e0b', emoji: '🛡️' },
      { id: 'radar', name: 'رادار', nameEn: 'Radar', color: '#eab308', emoji: '📡' },
      { id: 'airbase', name: 'پایگاه هوایی', nameEn: 'Airbases', color: '#a855f7', emoji: '✈️' },
      { id: 'military', name: 'مناطق نظامی', nameEn: 'Military', color: '#ef4444', emoji: '🎖️' },
    ]
  },
  {
    id: 'infrastructure',
    name: 'زیرساخت',
    nameEn: 'Infrastructure',
    layers: [
      { id: 'refinery', name: 'پالایشگاه', nameEn: 'Refineries', color: '#8b5cf6', emoji: '🛢️' },
      { id: 'oil_field', name: 'میدان نفتی', nameEn: 'Oil Fields', color: '#7c3aed', emoji: '⛽' },
      { id: 'power_generation', name: 'نیروگاه', nameEn: 'Power Plants', color: '#a855f7', emoji: '⚡' },
      { id: 'communications', name: 'مخابرات', nameEn: 'Communications', color: '#06b6d4', emoji: '📶' },
    ]
  },
  {
    id: 'government',
    name: 'حکومتی',
    nameEn: 'Government',
    layers: [
      { id: 'government', name: 'اماکن حکومتی', nameEn: 'Government', color: '#ec4899', emoji: '🏛️' },
      { id: 'irgc', name: 'سپاه', nameEn: 'IRGC', color: '#dc2626', emoji: '⚔️' },
      { id: 'naval', name: 'نیروی دریایی', nameEn: 'Naval', color: '#3b82f6', emoji: '⚓' },
    ]
  },
  {
    id: 'cities',
    name: 'شهرها',
    nameEn: 'Cities',
    layers: [
      { id: 'population_center', name: 'مراکز جمعیتی', nameEn: 'Population', color: '#22c55e', emoji: '🏙️' },
    ]
  },
]

function LayerControlPanel({ enabledLayers, onToggleLayer, onClose }: { 
  enabledLayers: Set<string>
  onToggleLayer: (id: string) => void
  onClose: () => void
}) {
  const { data: quickStats } = useQuickStats()
  const totalTargets = quickStats?.target_count ?? 0
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ watchdog: true, high_risk: true, infrastructure: false, government: false, cities: false })

  return (
    <div className="absolute top-4 right-4 z-[1000] w-72 max-h-[calc(100vh-100px)] bg-[#1a1a2e]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/10 bg-black/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-600/30">
              <span className="text-xl">🎯</span>
            </div>
            <div>
              <div className="text-2xl font-black text-white">{totalTargets}</div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">Targets</div>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-white/10 transition">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-3 py-2 border-b border-white/5">
        <div className="relative">
          <input 
            type="text" 
            placeholder="جستجو در مکان‌ها..."
            className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-red-500/50"
          />
          <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Layer Groups */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {LAYER_GROUPS.map((group) => (
          <div key={group.id} className="rounded-xl overflow-hidden">
            <button
              onClick={() => setExpanded(p => ({ ...p, [group.id]: !p[group.id] }))}
              className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/5 transition"
            >
              <span className="text-sm font-bold text-white">{group.name}</span>
              <span className={`text-gray-500 transition-transform ${expanded[group.id] ? 'rotate-180' : ''}`}>▼</span>
            </button>

            {expanded[group.id] && (
              <div className="pb-2 space-y-0.5">
                {group.layers.map((layer) => (
                  <label
                    key={layer.id}
                    className="flex items-center gap-3 px-3 py-2 mx-1 rounded-lg hover:bg-white/5 cursor-pointer transition group"
                  >
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition ${
                      enabledLayers.has(layer.id) 
                        ? 'border-red-500 bg-red-500' 
                        : 'border-gray-600 group-hover:border-gray-400'
                    }`}>
                      {enabledLayers.has(layer.id) && (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span className="text-lg">{layer.emoji}</span>
                    <span className={`text-sm flex-1 ${enabledLayers.has(layer.id) ? 'text-white' : 'text-gray-500'}`}>
                      {layer.name}
                    </span>
                    <input
                      type="checkbox"
                      checked={enabledLayers.has(layer.id)}
                      onChange={() => onToggleLayer(layer.id)}
                      className="sr-only"
                    />
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/10 bg-black/30 text-center">
        <div className="text-xs text-gray-500">{enabledLayers.size} لایه فعال</div>
        <div className="text-[10px] text-gray-600 mt-1">@IDF @deptofwar @vahid</div>
      </div>
    </div>
  )
}

/* ── Layer Toggle Button ─────────────────────────────────────────── */
function LayerToggleBtn({ onClick, targetCount }: { onClick: () => void; targetCount: number }) {
  return (
    <button
      onClick={onClick}
      className="absolute top-4 right-4 z-[1000] bg-[#1a1a2e]/90 backdrop-blur-xl border border-white/10 rounded-2xl px-4 py-3 shadow-2xl flex items-center gap-3 hover:bg-[#1a1a2e] transition"
    >
      <div className="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-600/30">
        <span className="text-xl">🎯</span>
      </div>
      <div className="text-left">
        <div className="text-2xl font-black text-white">{targetCount}</div>
        <div className="text-[10px] text-gray-400 uppercase tracking-wider">Targets</div>
      </div>
      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
      </svg>
    </button>
  )
}

/* ── Social Links (bottom right) ─────────────────────────────────── */
function SocialLinks() {
  return (
    <div className="absolute bottom-4 right-4 z-[1000] flex gap-2">
      <a href="https://x.com/idf" target="_blank" rel="noopener noreferrer" 
         className="w-10 h-10 bg-[#1a1a2e]/90 backdrop-blur-xl border border-white/10 rounded-xl flex items-center justify-center hover:bg-white/10 transition">
        <span className="text-lg">𝕏</span>
      </a>
      <a href="https://t.me/" target="_blank" rel="noopener noreferrer"
         className="w-10 h-10 bg-[#1a1a2e]/90 backdrop-blur-xl border border-white/10 rounded-xl flex items-center justify-center hover:bg-white/10 transition">
        <span className="text-lg">📱</span>
      </a>
    </div>
  )
}

/* ── Main MapView ────────────────────────────────────────────────── */
export function MapView() {
  const [mapReady, setMapReady] = useState(false)
  const [selectedTarget, setSelectedTarget] = useState<{ target: Target; assessment?: Assessment } | null>(null)
  const [showLayerControl, setShowLayerControl] = useState(true)
  const [enabledLayers, setEnabledLayers] = useState<Set<string>>(() => new Set([
    'confirmed_strike', 'nuclear_facility', 'missile', 'air_defense', 
    'radar', 'airbase', 'military', 'naval', 'refinery', 'oil_field', 'power_generation',
    'communications', 'government', 'irgc', 'population_center'
  ]))
  
  const { data: quickStats } = useQuickStats()
  const totalTargets = quickStats?.target_count ?? 0
  const mobile = isMobile()

  useEffect(() => {
    const timer = setTimeout(() => setMapReady(true), 100)
    return () => clearTimeout(timer)
  }, [])

  const handleSelectTarget = useCallback((target: Target, assessment?: Assessment) => {
    setSelectedTarget({ target, assessment })
  }, [])

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
        zoomControl={false}
        preferCanvas={true}
        touchZoom={true}
        dragging={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OSM &copy; CARTO'
          maxZoom={18}
        />
        {mapReady && (
          <>
            <CityLabels />
            <TargetMarkers onSelectTarget={handleSelectTarget} enabledLayers={enabledLayers} />
          </>
        )}
        <FlyToHandler />
      </MapContainer>
      
      {/* Layer Control or Toggle Button */}
      {showLayerControl ? (
        <LayerControlPanel 
          enabledLayers={enabledLayers} 
          onToggleLayer={toggleLayer}
          onClose={() => setShowLayerControl(false)}
        />
      ) : (
        <LayerToggleBtn 
          onClick={() => setShowLayerControl(true)} 
          targetCount={totalTargets}
        />
      )}

      {/* Zoom Controls (custom - bottom left) */}
      <div className="absolute bottom-20 left-4 z-[1000] flex flex-col gap-1">
        <button className="w-10 h-10 bg-[#1a1a2e]/90 backdrop-blur-xl border border-white/10 rounded-xl flex items-center justify-center hover:bg-white/10 transition text-white text-xl font-bold">+</button>
        <button className="w-10 h-10 bg-[#1a1a2e]/90 backdrop-blur-xl border border-white/10 rounded-xl flex items-center justify-center hover:bg-white/10 transition text-white text-xl font-bold">−</button>
      </div>
      
      {/* Social Links */}
      <SocialLinks />

      {/* Analysis Panel */}
      {selectedTarget && (
        <AnalysisPanel 
          target={selectedTarget.target}
          assessment={selectedTarget.assessment}
          onClose={() => setSelectedTarget(null)}
        />
      )}
    </div>
  )
}
