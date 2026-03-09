import { useState } from 'react'
import { useQuickStats, useFullAssessment } from '../../api/hooks'

function Stat({ value, label, loading, color, onClick }: { 
  value: string | number; 
  label: string; 
  loading?: boolean;
  color?: string;
  onClick?: () => void;
}) {
  return (
    <div 
      className={`flex-1 bg-card py-2.5 px-3 text-center ${onClick ? 'cursor-pointer hover:bg-accent/10' : ''}`}
      onClick={onClick}
    >
      <div className={`text-xl font-bold ${loading ? 'text-dim animate-pulse' : ''}`} style={{ color: color || 'white' }}>
        {value}
      </div>
      <div className="text-[10px] text-dim uppercase tracking-wider mt-0.5">
        {label}
      </div>
    </div>
  )
}

// Category breakdown popup
function CategoryBreakdown({ categories, onClose }: { categories: Record<string, number>; onClose: () => void }) {
  const sorted = Object.entries(categories).sort((a, b) => b[1] - a[1])
  
  // Group by type
  const military = sorted.filter(([k]) => ['army', 'air_defense', 'missile', 'naval', 'irgc', 'ammunition', 'weapons_research', 'command_control'].includes(k))
  const nuclear = sorted.filter(([k]) => ['nuclear_facility', 'weapons_research'].includes(k))
  const energy = sorted.filter(([k]) => ['refinery', 'power_generation', 'gas_refinery', 'oil_field', 'oil_terminal', 'gas_field', 'gas_storage', 'pipeline', 'petrochemical', 'gas_processing'].includes(k))
  const civilian = sorted.filter(([k]) => ['population_center', 'city', 'city_capital'].includes(k))
  const infrastructure = sorted.filter(([k]) => ['critical_infrastructure', 'communications', 'transport', 'logistics'].includes(k))
  
  const Section = ({ title, items, color }: { title: string; items: [string, number][]; color: string }) => (
    items.length > 0 && (
      <div className="mb-3">
        <div className="text-xs font-bold mb-1" style={{ color }}>{title}</div>
        <div className="grid grid-cols-2 gap-1">
          {items.map(([cat, count]) => (
            <div key={cat} className="flex justify-between text-[10px]">
              <span className="text-gray-400">{cat.replace(/_/g, ' ')}</span>
              <span className="text-white font-mono">{count}</span>
            </div>
          ))}
        </div>
      </div>
    )
  )
  
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-card border border-border rounded-lg p-4 max-w-md max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-white">Target Categories</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        
        <Section title="🎯 MILITARY TARGETS" items={military} color="#ef4444" />
        <Section title="☢️ NUCLEAR FACILITIES" items={nuclear} color="#f59e0b" />
        <Section title="⚡ ENERGY INFRASTRUCTURE" items={energy} color="#8b5cf6" />
        <Section title="🏗️ CRITICAL INFRASTRUCTURE" items={infrastructure} color="#3b82f6" />
        <Section title="🏙️ POPULATION CENTERS" items={civilian} color="#22c55e" />
        
        <div className="mt-4 pt-3 border-t border-border">
          <div className="flex justify-between text-sm font-bold">
            <span className="text-gray-300">TOTAL TARGETS</span>
            <span className="text-white">{Object.values(categories).reduce((a, b) => a + b, 0)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export function StatsBar() {
  const [showCategories, setShowCategories] = useState(false)
  
  // Use quick-stats for instant initial load
  const { data: quickStats, isLoading: quickLoading, dataUpdatedAt } = useQuickStats()
  // Full assessment loads in background (cached on backend)
  const { data: assessment, isFetching } = useFullAssessment()

  const lastScan = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : (quickStats?.last_osint_refresh ? new Date(quickStats.last_osint_refresh).toLocaleTimeString() : '--')
  
  // Use quick stats first, then full assessment when available
  const targetCount = quickStats?.target_count ?? '--'
  const articleCount = quickStats?.osint_articles ?? assessment?.osint?.articles_found ?? '--'
  const strikeCount = quickStats?.strike_count ?? assessment?.summary?.total_strikes ?? 0
  const confirmedCount = quickStats?.confirmed ?? assessment?.summary?.confirmed ?? 0
  const likelyCount = quickStats?.likely ?? assessment?.summary?.likely ?? 0
  
  // Calculate category breakdowns
  const categories = quickStats?.categories ?? {}
  const militaryCount = ['army', 'air_defense', 'missile', 'naval', 'irgc', 'ammunition', 'weapons_research', 'command_control']
    .reduce((sum, k) => sum + (categories[k] || 0), 0)
  const nuclearCount = (categories['nuclear_facility'] || 0)
  const civilianCount = (categories['population_center'] || 0) + (categories['city'] || 0) + (categories['city_capital'] || 0)

  return (
    <>
      <div className="flex gap-px bg-border shrink-0">
        <Stat 
          value={targetCount} 
          label="Total Targets" 
          loading={quickLoading} 
          onClick={() => setShowCategories(true)}
        />
        <Stat value={militaryCount || '--'} label="Military" loading={quickLoading} color="#ef4444" />
        <Stat value={nuclearCount || '--'} label="Nuclear" loading={quickLoading} color="#f59e0b" />
        <Stat value={civilianCount || '--'} label="Cities" loading={quickLoading} color="#22c55e" />
        <Stat value={confirmedCount} label="Confirmed Hits" loading={isFetching} color="#dc2626" />
        <Stat value={likelyCount} label="Likely Hits" loading={isFetching} color="#eab308" />
      </div>
      
      {showCategories && quickStats?.categories && (
        <CategoryBreakdown categories={quickStats.categories} onClose={() => setShowCategories(false)} />
      )}
    </>
  )
}
