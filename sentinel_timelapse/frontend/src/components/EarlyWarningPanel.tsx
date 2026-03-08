import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { fetchJSON } from '../api/client';
import { useAppStore } from '../store/useAppStore';

interface EvacuationZone {
  zone_id: string;
  name: string;
  name_fa: string;
  lat: number;
  lon: number;
  radius_km: number;
  population: number;
  facilities: string[];
}

interface Warning {
  id: string;
  source_id: string;
  source_name: string;
  title: string;
  url: string;
  published: string;
  detected_at: string;
  level: 'IMMINENT' | 'WARNING' | 'ALERT' | 'WATCH';
  level_num: number;
  color: string;
  message_en: string;
  message_fa: string;
  action: string;
  affected_zones: EvacuationZone[];
  matched_keywords: string[];
  expires_at: string;
}

interface WarningsResponse {
  success: boolean;
  warnings: Warning[];
  count: number;
  last_check: string;
  refresh_interval_minutes: number;
}

export function EarlyWarningPanel() {
  const [isDismissed, setIsDismissed] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const setActiveTab = useAppStore((s) => s.setActiveTab);

  // Fetch warnings every 60 seconds
  const { data, isLoading } = useQuery<WarningsResponse>({
    queryKey: ['early-warnings'],
    queryFn: async () => {
      const response = await fetchJSON<WarningsResponse>('/api/early-warnings');
      return response || { success: false, warnings: [], count: 0, last_check: '', refresh_interval_minutes: 20 };
    },
    refetchInterval: 60000, // Check every minute
    staleTime: 30000,
  });

  const warnings = data?.warnings || [];
  const criticalWarnings = warnings.filter(w => w.level === 'IMMINENT' || w.level === 'WARNING');

  // Play alert sound for critical warnings
  useEffect(() => {
    if (criticalWarnings.length > 0 && audioEnabled) {
      // Reset dismissed state when new critical warnings arrive
      setIsDismissed(false);
      try {
        // Use Web Audio API for alert
        const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = 800;
        osc.connect(ctx.destination);
        osc.start();
        setTimeout(() => osc.stop(), 200);
      } catch (e) {
        console.log('Audio alert not available');
      }
    }
  }, [criticalWarnings.length, audioEnabled]);

  // Handle going to alarms tab
  const goToAlarmsTab = () => {
    setActiveTab('alarms');
    setIsDismissed(true);
  };

  if (isLoading) return null;
  if (warnings.length === 0) return null;
  if (isDismissed) {
    // Show minimized bar when dismissed - mobile friendly
    return (
      <button
        onClick={() => setIsDismissed(false)}
        className="fixed top-0 left-0 right-0 z-50 bg-red-900/95 text-white text-center py-3 md:py-2 text-xs md:text-sm font-bold active:bg-red-800 transition-colors border-b-2 border-red-500"
      >
        <span className="animate-pulse">🚨</span> {warnings.length} Warning{warnings.length > 1 ? 's' : ''} {criticalWarnings.length > 0 && <span className="bg-red-600 px-2 py-0.5 rounded text-[10px] ml-2">CRITICAL</span>}
      </button>
    );
  }

  const getLevelStyles = (level: string) => {
    switch (level) {
      case 'IMMINENT':
        return 'bg-red-600 text-white animate-pulse border-red-400';
      case 'WARNING':
        return 'bg-orange-500 text-white border-orange-400';
      case 'ALERT':
        return 'bg-yellow-500 text-black border-yellow-400';
      case 'WATCH':
        return 'bg-blue-500 text-white border-blue-400';
      default:
        return 'bg-gray-500 text-white border-gray-400';
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Critical Warning Banner - Mobile optimized */}
      {criticalWarnings.length > 0 && (
        <div className={`${getLevelStyles(criticalWarnings[0].level)} p-2 md:p-3 shadow-lg border-b-2 border-white/20`}>
          <div className="flex items-start md:items-center justify-between gap-2">
            <div className="flex items-start md:items-center gap-2 flex-1 min-w-0">
              <span className="text-xl md:text-2xl shrink-0">⚠️</span>
              <div className="text-left flex-1 min-w-0">
                <div className="text-xs md:text-lg font-bold truncate">{criticalWarnings[0].message_en}</div>
                <div className="text-sm md:text-xl font-bold truncate" dir="rtl">{criticalWarnings[0].message_fa}</div>
              </div>
            </div>
            <div className="flex items-center gap-1 md:gap-2 shrink-0">
              <button
                onClick={() => setAudioEnabled(!audioEnabled)}
                className="p-2 md:p-2 bg-black/20 rounded-lg active:bg-black/40 text-base md:text-sm min-w-[40px]"
                title={audioEnabled ? 'Mute alerts' : 'Enable alerts'}
              >
                {audioEnabled ? '🔊' : '🔇'}
              </button>
              <button
                onClick={goToAlarmsTab}
                className="px-2 md:px-3 py-2 bg-black/30 rounded-lg active:bg-black/50 text-xs md:text-sm font-bold whitespace-nowrap"
              >
                <span className="hidden md:inline">📋 View All</span>
                <span className="md:hidden">📋</span>
              </button>
              <button
                onClick={() => setIsDismissed(true)}
                className="px-2 md:px-3 py-2 bg-black/30 rounded-lg active:bg-black/50 text-xs md:text-sm font-bold"
              >
                ✕
              </button>
            </div>
          </div>
          {/* Affected zones quick summary - scrollable on mobile */}
          {criticalWarnings[0].affected_zones.length > 0 && (
            <div className="mt-2 flex gap-2 overflow-x-auto pb-1 -mx-2 px-2">
              {criticalWarnings[0].affected_zones.map(zone => (
                <span key={zone.zone_id} className="bg-black/30 px-2 py-1 rounded-lg text-[10px] md:text-xs font-bold whitespace-nowrap shrink-0">
                  📍 {zone.name} ({zone.name_fa})
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Non-critical warnings summary */}
      {criticalWarnings.length === 0 && warnings.length > 0 && (
        <div className="bg-yellow-600 text-black p-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span className="font-bold">{warnings.length} Active Warning{warnings.length > 1 ? 's' : ''}</span>
            <span className="text-sm">- Monitoring CENTCOM/IDF</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={goToAlarmsTab}
              className="px-3 py-1 bg-black/20 rounded hover:bg-black/30 text-sm font-bold"
            >
              📋 View All
            </button>
            <button
              onClick={() => setIsDismissed(true)}
              className="px-3 py-1 bg-black/20 rounded hover:bg-black/30 text-sm"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default EarlyWarningPanel;
