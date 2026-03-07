import { useState } from 'react'

// Layer configuration matching mahsaalert style
interface Layer {
  id: string
  name: string
  nameFa: string
  color: string
  enabled: boolean
}

interface LayerGroup {
  id: string
  name: string
  nameFa: string
  layers: Layer[]
  expanded: boolean
}

interface LayerControlProps {
  layers: LayerGroup[]
  onToggleLayer: (layerId: string) => void
  onToggleGroup: (groupId: string) => void
  onClose?: () => void
}

// Default layer groups - mahsaalert style
export const DEFAULT_LAYER_GROUPS: LayerGroup[] = [
  {
    id: 'watchdog',
    name: 'Watchdog',
    nameFa: 'دیدبان',
    expanded: true,
    layers: [
      { id: 'confirmed_strike', name: 'Confirmed Strikes', nameFa: 'حملات تایید شده', color: '#ff0000', enabled: true },
      { id: 'evacuation', name: 'Evacuation Warning', nameFa: 'هشدار تخلیه', color: '#ff6b35', enabled: true },
    ]
  },
  {
    id: 'high_risk',
    name: 'High Risk Areas',
    nameFa: 'مناطق پرخطر',
    expanded: true,
    layers: [
      { id: 'nuclear_facility', name: 'Nuclear Program', nameFa: 'برنامه هسته‌ای', color: '#ff4444', enabled: true },
      { id: 'missile', name: 'Missile Program', nameFa: 'برنامه موشکی', color: '#ff6b35', enabled: true },
      { id: 'air_defense', name: 'Air Defense', nameFa: 'پدافند هوایی', color: '#f59e0b', enabled: true },
      { id: 'radar', name: 'Radar', nameFa: 'رادار', color: '#eab308', enabled: true },
      { id: 'airbase', name: 'Air Bases / Drones', nameFa: 'پایگاه‌هوایی/پهپادی', color: '#a855f7', enabled: true },
      { id: 'military', name: 'Military Zones', nameFa: 'مناطق نظامی', color: '#ef4444', enabled: true },
      { id: 'naval', name: 'Naval Bases', nameFa: 'پایگاه‌های دریایی', color: '#3b82f6', enabled: true },
    ]
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure',
    nameFa: 'زیرساخت',
    expanded: false,
    layers: [
      { id: 'refinery', name: 'Oil Refineries', nameFa: 'پالایشگاه', color: '#8b5cf6', enabled: true },
      { id: 'oil_field', name: 'Oil Fields', nameFa: 'میدان نفتی', color: '#7c3aed', enabled: true },
      { id: 'power_generation', name: 'Power Plants', nameFa: 'نیروگاه', color: '#a855f7', enabled: true },
      { id: 'communications', name: 'Communications', nameFa: 'مخابرات', color: '#06b6d4', enabled: true },
    ]
  },
  {
    id: 'government',
    name: 'Government',
    nameFa: 'مکان‌های حکومتی',
    expanded: false,
    layers: [
      { id: 'government', name: 'Government', nameFa: 'اماکن حکومتی', color: '#ec4899', enabled: true },
      { id: 'irgc', name: 'IRGC', nameFa: 'سپاه', color: '#dc2626', enabled: true },
      { id: 'intelligence', name: 'Intelligence', nameFa: 'اطلاعات', color: '#991b1b', enabled: false },
      { id: 'prison', name: 'Prison', nameFa: 'زندان', color: '#78716c', enabled: false },
    ]
  },
  {
    id: 'cities',
    name: 'Population Centers',
    nameFa: 'مراکز جمعیتی',
    expanded: false,
    layers: [
      { id: 'population_center', name: 'Major Cities', nameFa: 'شهرها', color: '#22c55e', enabled: true },
    ]
  },
]

export function LayerControl({ layers, onToggleLayer, onToggleGroup, onClose }: LayerControlProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>(
    Object.fromEntries(layers.map(g => [g.id, g.expanded]))
  )

  const toggleExpand = (groupId: string) => {
    setExpanded(prev => ({ ...prev, [groupId]: !prev[groupId] }))
  }

  const enabledCount = layers.reduce((sum, g) => 
    sum + g.layers.filter(l => l.enabled).length, 0
  )
  const totalCount = layers.reduce((sum, g) => sum + g.layers.length, 0)

  return (
    <div className="absolute top-2 right-2 z-[1000] bg-card/95 backdrop-blur border border-border rounded-lg shadow-xl max-w-[280px] max-h-[80vh] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-bg/50">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <span className="font-bold text-sm text-white">Map Layers</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-dim">{enabledCount}/{totalCount}</span>
          {onClose && (
            <button onClick={onClose} className="text-gray-400 hover:text-white">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Scrollable content */}
      <div className="overflow-y-auto flex-1 p-2">
        {layers.map((group) => (
          <div key={group.id} className="mb-2">
            {/* Group Header */}
            <button
              onClick={() => toggleExpand(group.id)}
              className="w-full flex items-center justify-between px-2 py-1.5 rounded bg-bg/50 hover:bg-bg transition"
            >
              <div className="flex items-center gap-2">
                <svg 
                  className={`w-3 h-3 text-gray-400 transition-transform ${expanded[group.id] ? 'rotate-90' : ''}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-xs font-bold text-gray-300">{group.name}</span>
              </div>
              <span className="text-[10px] text-dim">
                {group.layers.filter(l => l.enabled).length}/{group.layers.length}
              </span>
            </button>

            {/* Layers */}
            {expanded[group.id] && (
              <div className="mt-1 ml-2 space-y-0.5">
                {group.layers.map((layer) => (
                  <label
                    key={layer.id}
                    className="flex items-center gap-2 px-2 py-1 rounded hover:bg-bg/30 cursor-pointer group"
                  >
                    <input
                      type="checkbox"
                      checked={layer.enabled}
                      onChange={() => onToggleLayer(layer.id)}
                      className="sr-only"
                    />
                    <div 
                      className={`w-3.5 h-3.5 rounded border-2 flex items-center justify-center transition ${
                        layer.enabled 
                          ? 'border-accent bg-accent' 
                          : 'border-gray-500 bg-transparent'
                      }`}
                    >
                      {layer.enabled && (
                        <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span 
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: layer.color }}
                    />
                    <span className={`text-[11px] ${layer.enabled ? 'text-gray-200' : 'text-gray-500'}`}>
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
      <div className="px-3 py-2 border-t border-border bg-bg/50">
        <div className="flex items-center justify-between text-[10px]">
          <button 
            onClick={() => layers.forEach(g => g.layers.forEach(l => onToggleLayer(l.id)))}
            className="text-gray-400 hover:text-white"
          >
            Toggle All
          </button>
          <span className="text-dim">Click markers for details</span>
        </div>
      </div>
    </div>
  )
}

// Compact toggle button when layer panel is closed
export function LayerToggleButton({ onClick, enabledCount }: { onClick: () => void; enabledCount: number }) {
  return (
    <button
      onClick={onClick}
      className="absolute top-2 right-2 z-[1000] bg-card/90 hover:bg-card border border-border rounded-lg px-3 py-2 shadow-lg flex items-center gap-2 transition"
    >
      <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
      </svg>
      <span className="text-xs font-bold text-white">Layers</span>
      <span className="bg-accent text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">
        {enabledCount}
      </span>
    </button>
  )
}
