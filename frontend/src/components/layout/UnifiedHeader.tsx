import { useQuickStats, useFullAssessment } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'

export function UnifiedHeader() {
  const { data: stats } = useQuickStats()
  const { data: assessments } = useFullAssessment()
  const setActiveTab = useAppStore(s => s.setActiveTab)
  const setSelectedTarget = useAppStore(s => s.setSelectedTarget)

  const activeStrikes = assessments?.assessments?.filter(a => (a.combined_score ?? 0) >= 0.3).length ?? 0
  const targets = stats?.target_count ?? 0
  
  // Simulated news count for visual
  const newsCount = 24 

  const handleOpenPanel = (tab: 'targets' | 'strikes' | 'news') => {
    setActiveTab(tab)
    setSelectedTarget(null) // Close any specific target view
  }

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[3000] flex items-center gap-1 md:gap-2 p-1 bg-black/80 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
      {/* Target Count */}
      <button 
        onClick={() => handleOpenPanel('targets')}
        className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 rounded-xl transition-all"
      >
        <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-lg">🎯</div>
        <div className="text-left hidden sm:block">
          <div className="text-xs font-black text-white leading-none">{targets.toLocaleString()}</div>
          <div className="text-[8px] text-gray-500 font-bold uppercase tracking-widest">Targets</div>
        </div>
      </button>

      <div className="w-[1px] h-6 bg-white/10 mx-1"></div>

      {/* Strike Count */}
      <button 
        onClick={() => handleOpenPanel('strikes')}
        className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 rounded-xl transition-all"
      >
        <div className={`w-8 h-8 rounded-lg ${activeStrikes > 0 ? 'bg-red-500/30 text-red-500 animate-pulse' : 'bg-white/5 text-gray-500'} flex items-center justify-center text-lg`}>💥</div>
        <div className="text-left hidden sm:block">
          <div className={`text-xs font-black leading-none ${activeStrikes > 0 ? 'text-red-500' : 'text-white'}`}>{activeStrikes}</div>
          <div className="text-[8px] text-gray-500 font-bold uppercase tracking-widest">Strikes</div>
        </div>
      </button>

      <div className="w-[1px] h-6 bg-white/10 mx-1"></div>

      {/* News Count */}
      <button 
        onClick={() => handleOpenPanel('news')}
        className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 rounded-xl transition-all"
      >
        <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center text-lg">📰</div>
        <div className="text-left hidden sm:block">
          <div className="text-xs font-black text-white leading-none">{newsCount}</div>
          <div className="text-[8px] text-gray-500 font-bold uppercase tracking-widest">Intelligence</div>
        </div>
      </button>

      <div className="w-[1px] h-6 bg-white/10 mx-1"></div>

      {/* Alarm Status */}
      <div className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 rounded-xl transition-all">
        <div className="w-8 h-8 rounded-lg bg-red-600/20 flex items-center justify-center text-lg relative">
           🚨
           <span className="absolute -top-1 -right-1 flex h-3 w-3">
             <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
             <span className="relative inline-flex rounded-full h-3 w-3 bg-red-600"></span>
           </span>
        </div>
        <div className="text-left hidden sm:block">
          <div className="text-xs font-black text-red-500 leading-none uppercase">Active Alert</div>
          <div className="text-[8px] text-gray-500 font-bold uppercase tracking-widest leading-none mt-0.5">Civilian Safety</div>
        </div>
      </div>
    </div>
  )
}
