import { useState, useMemo } from 'react'
import { useTargets } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'
import { getTypeColor } from '../../utils/colors'

// Target type descriptions - WHY it's a target
const TARGET_DESCRIPTIONS: Record<string, { icon: string; threat: string; description: string }> = {
  // Military
  'army': { icon: '🎖️', threat: 'HIGH', description: 'Ground forces base - potential staging area for military operations' },
  'air_defense': { icon: '🛡️', threat: 'HIGH', description: 'Air defense system - protects airspace, priority target in airstrikes' },
  'missile': { icon: '🚀', threat: 'CRITICAL', description: 'Ballistic missile facility - strategic weapons capability' },
  'naval': { icon: '⚓', threat: 'HIGH', description: 'Naval base - controls maritime access and operations' },
  'irgc': { icon: '⚔️', threat: 'CRITICAL', description: 'IRGC facility - Revolutionary Guard operations center' },
  'ammunition': { icon: '💣', threat: 'HIGH', description: 'Ammunition depot - weapons storage, explosive risk' },
  'weapons_research': { icon: '🔬', threat: 'CRITICAL', description: 'Weapons R&D - developing advanced military capabilities' },
  'command_control': { icon: '📡', threat: 'CRITICAL', description: 'Command center - military coordination hub' },
  
  // Nuclear
  'nuclear_facility': { icon: '☢️', threat: 'CRITICAL', description: 'Nuclear site - uranium enrichment or reactor' },
  'nuclear': { icon: '☢️', threat: 'CRITICAL', description: 'Nuclear facility - potential weapons program' },
  
  // Energy
  'refinery': { icon: '🛢️', threat: 'HIGH', description: 'Oil refinery - fuel production for military and economy' },
  'power_generation': { icon: '⚡', threat: 'MEDIUM', description: 'Power plant - electricity for military and civilians' },
  'gas_refinery': { icon: '🔥', threat: 'MEDIUM', description: 'Gas processing - energy infrastructure' },
  'oil_field': { icon: '🛢️', threat: 'MEDIUM', description: 'Oil production - economic target' },
  'oil_terminal': { icon: '🚢', threat: 'HIGH', description: 'Oil export terminal - economic chokepoint' },
  'gas_field': { icon: '💨', threat: 'MEDIUM', description: 'Natural gas production' },
  'terminal': { icon: '🚢', threat: 'HIGH', description: 'Export terminal - trade chokepoint' },
  'gas': { icon: '💨', threat: 'MEDIUM', description: 'Gas facility' },
  'power': { icon: '⚡', threat: 'MEDIUM', description: 'Power generation' },
  
  // Infrastructure
  'critical_infrastructure': { icon: '🏗️', threat: 'MEDIUM', description: 'Strategic infrastructure' },
  'communications': { icon: '📶', threat: 'MEDIUM', description: 'Communications hub - disrupts coordination' },
  'transport': { icon: '🚂', threat: 'LOW', description: 'Transport hub - logistics network' },
  'logistics': { icon: '📦', threat: 'MEDIUM', description: 'Supply chain node' },
  
  // Civilian
  'population_center': { icon: '🏙️', threat: 'CIVILIAN', description: 'City/town - civilian population' },
  'city': { icon: '🏙️', threat: 'CIVILIAN', description: 'Urban area - civilian zone' },
  'city_capital': { icon: '🏛️', threat: 'CIVILIAN', description: 'Provincial capital - administrative center' },
  
  // Other
  'government': { icon: '🏛️', threat: 'HIGH', description: 'Government building - administrative target' },
  'confirmed_strike': { icon: '💥', threat: 'HIT', description: 'Confirmed strike location' },
  'user_report': { icon: '📍', threat: 'UNVERIFIED', description: 'User-reported incident - unverified' },
}

const THREAT_COLORS: Record<string, string> = {
  'CRITICAL': '#dc2626',
  'HIGH': '#f97316',
  'MEDIUM': '#eab308',
  'LOW': '#22c55e',
  'CIVILIAN': '#3b82f6',
  'HIT': '#ef4444',
  'UNVERIFIED': '#9ca3af',
}

// Filter by threat level
type ThreatFilter = '' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'MILITARY' | 'CIVILIAN'

export function TargetsPanel() {
  const { data } = useTargets()
  const flyTo = useAppStore((s) => s.flyTo)

  const [category, setCategory] = useState('')
  const [province, setProvince] = useState('')
  const [search, setSearch] = useState('')
  const [threatFilter, setThreatFilter] = useState<ThreatFilter>('')

  const targets = data?.targets ?? []
  const categories = data?.categories ?? []
  const provinces = data?.provinces ?? []

  const filtered = useMemo(() => {
    let list = targets
    if (category) list = list.filter((t) => t.category === category)
    if (province) list = list.filter((t) => t.province === province)
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          t.type.toLowerCase().includes(q) ||
          (t.description ?? '').toLowerCase().includes(q),
      )
    }
    if (threatFilter) {
      list = list.filter((t) => {
        const info = TARGET_DESCRIPTIONS[t.type] || TARGET_DESCRIPTIONS[t.category]
        const threat = info?.threat || 'LOW'
        if (threatFilter === 'MILITARY') {
          return ['CRITICAL', 'HIGH'].includes(threat)
        }
        if (threatFilter === 'CIVILIAN') {
          return threat === 'CIVILIAN'
        }
        return threat === threatFilter
      })
    }
    return list
  }, [targets, category, province, search, threatFilter])

  // Count by threat level
  const threatCounts = useMemo(() => {
    const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, CIVILIAN: 0 }
    targets.forEach((t) => {
      const info = TARGET_DESCRIPTIONS[t.type] || TARGET_DESCRIPTIONS[t.category]
      const threat = info?.threat || 'LOW'
      if (counts[threat] !== undefined) counts[threat]++
    })
    return counts
  }, [targets])

  return (
    <>
      {/* Threat Level Summary */}
      <div className="flex gap-1 mb-3 flex-wrap">
        <button
          onClick={() => setThreatFilter(threatFilter === 'CRITICAL' ? '' : 'CRITICAL')}
          className={`px-2 py-1 rounded text-[10px] font-bold border ${threatFilter === 'CRITICAL' ? 'bg-red-600 border-red-500' : 'bg-card border-border hover:bg-red-900/30'}`}
        >
          ☢️ CRITICAL ({threatCounts.CRITICAL})
        </button>
        <button
          onClick={() => setThreatFilter(threatFilter === 'HIGH' ? '' : 'HIGH')}
          className={`px-2 py-1 rounded text-[10px] font-bold border ${threatFilter === 'HIGH' ? 'bg-orange-600 border-orange-500' : 'bg-card border-border hover:bg-orange-900/30'}`}
        >
          🎯 HIGH ({threatCounts.HIGH})
        </button>
        <button
          onClick={() => setThreatFilter(threatFilter === 'MEDIUM' ? '' : 'MEDIUM')}
          className={`px-2 py-1 rounded text-[10px] font-bold border ${threatFilter === 'MEDIUM' ? 'bg-yellow-600 border-yellow-500' : 'bg-card border-border hover:bg-yellow-900/30'}`}
        >
          ⚡ MEDIUM ({threatCounts.MEDIUM})
        </button>
        <button
          onClick={() => setThreatFilter(threatFilter === 'CIVILIAN' ? '' : 'CIVILIAN')}
          className={`px-2 py-1 rounded text-[10px] font-bold border ${threatFilter === 'CIVILIAN' ? 'bg-blue-600 border-blue-500' : 'bg-card border-border hover:bg-blue-900/30'}`}
        >
          🏙️ CIVILIAN ({threatCounts.CIVILIAN})
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-1.5 flex-wrap mb-2">
        <div className="flex flex-col gap-2">
          <div className="grid grid-cols-2 gap-2">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="bg-bg border-2 border-white/10 text-gray-200 px-3 py-2 rounded-lg text-[11px] font-bold focus:border-accent outline-none"
            >
              <option value="">ALL CATEGORIES ({targets.length})</option>
              {[...categories].sort().map((c) => (
                <option key={c} value={c}>
                  {c.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>

            <select
              value={province}
              onChange={(e) => setProvince(e.target.value)}
              className="bg-bg border-2 border-white/10 text-gray-200 px-3 py-2 rounded-lg text-[11px] font-bold focus:border-accent outline-none"
            >
              <option value="">ALL PROVINCES</option>
              {[...provinces].sort().map((p) => (
                <option key={p} value={p}>
                  {p.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="SEARCH STRATEGIC TARGETS..."
            className="w-full bg-bg border-2 border-white/10 text-gray-200 px-4 py-2.5 rounded-lg text-xs font-bold focus:border-accent outline-none placeholder:text-gray-600"
          />
        </div>
      </div>

      <div className="text-[10px] font-black text-dim mb-3 uppercase tracking-widest flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
        Displaying {filtered.length} IDENTIFIED TARGETS
      </div>

      <div className="space-y-2">
        {filtered.map((t) => {
          const info = TARGET_DESCRIPTIONS[t.type] || TARGET_DESCRIPTIONS[t.category] || { icon: '📍', threat: 'LOW', description: t.description || 'Location' }
          const threatColor = THREAT_COLORS[info.threat] || THREAT_COLORS.LOW
          
          return (
            <div
              key={t.id}
              onClick={() => flyTo(t.lat, t.lon)}
              className="bg-card/40 border border-white/5 rounded-xl p-3 cursor-pointer hover:border-accent/40 hover:bg-accent/5 transition-all group"
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl group-hover:scale-110 transition-transform">{info.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-black text-gray-100 truncate uppercase tracking-tight">
                    {t.name}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mt-1">
                    <span 
                      className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-tighter"
                      style={{ backgroundColor: `${threatColor}30`, color: threatColor }}
                    >
                      {info.threat}
                    </span>
                    <span className="text-[10px] text-gray-400 font-bold uppercase">{t.type.replace(/_/g, ' ')}</span>
                    <span className="text-gray-700">•</span>
                    <span className="text-[10px] text-gray-500 font-bold uppercase">{t.province}</span>
                  </div>
                </div>
              </div>
              <div className="mt-2 text-[11px] text-gray-500 font-medium leading-tight pl-9 border-t border-white/5 pt-2 italic">
                {info.description}
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
