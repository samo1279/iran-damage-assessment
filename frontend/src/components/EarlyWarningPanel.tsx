import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { fetchJSON } from '../api/client';

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
  const [isExpanded, setIsExpanded] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);

  // Fetch warnings every 60 seconds
  const { data, isLoading, refetch } = useQuery<WarningsResponse>({
    queryKey: ['early-warnings'],
    queryFn: async () => {
      const response = await fetchJSON<WarningsResponse>('/api/early-warnings');
      return response || { success: false, warnings: [], count: 0, last_check: '', refresh_interval_minutes: 5 };
    },
    refetchInterval: 60000, // Check every minute
    staleTime: 30000,
  });

  const warnings = data?.warnings || [];
  const criticalWarnings = warnings.filter(w => w.level === 'IMMINENT' || w.level === 'WARNING');

  // Play alert sound for critical warnings
  useEffect(() => {
    if (criticalWarnings.length > 0 && audioEnabled) {
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

  if (isLoading) return null;
  if (warnings.length === 0) return null;

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
      {/* Critical Warning Banner */}
      {criticalWarnings.length > 0 && (
        <div className={`${getLevelStyles(criticalWarnings[0].level)} p-3 text-center font-bold shadow-lg`}>
          <div className="flex items-center justify-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div className="text-left">
              <div className="text-lg">{criticalWarnings[0].message_en}</div>
              <div className="text-xl font-bold" dir="rtl">{criticalWarnings[0].message_fa}</div>
            </div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="ml-4 px-3 py-1 bg-black/30 rounded hover:bg-black/50"
            >
              {isExpanded ? 'Hide Details' : 'Show Details'}
            </button>
          </div>
        </div>
      )}

      {/* Expanded Warning Details */}
      {isExpanded && warnings.length > 0 && (
        <div className="bg-gray-900/95 backdrop-blur border-b border-gray-700 max-h-[50vh] overflow-y-auto">
          <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                🚨 EARLY WARNING SYSTEM - نظام هشدار اولیه
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setAudioEnabled(!audioEnabled)}
                  className={`px-3 py-1 rounded text-sm ${audioEnabled ? 'bg-green-600' : 'bg-gray-600'}`}
                >
                  {audioEnabled ? '🔊 Sound ON' : '🔇 Sound OFF'}
                </button>
                <button
                  onClick={() => refetch()}
                  className="px-3 py-1 bg-blue-600 rounded text-sm hover:bg-blue-700"
                >
                  🔄 Refresh
                </button>
              </div>
            </div>

            <div className="grid gap-4">
              {warnings.map((warning) => (
                <div
                  key={warning.id}
                  className={`${getLevelStyles(warning.level)} rounded-lg p-4 border-2`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-black/30 rounded text-sm font-bold">
                          {warning.level}
                        </span>
                        <span className="text-sm opacity-80">
                          Source: {warning.source_name}
                        </span>
                      </div>
                      <h3 className="font-bold text-lg mb-2">{warning.title}</h3>
                      <p className="text-sm mb-3">{warning.action}</p>

                      {/* Affected Zones */}
                      <div className="bg-black/20 rounded p-3">
                        <h4 className="font-bold mb-2">
                          🎯 AFFECTED AREAS - مناطق تحت تأثیر
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {warning.affected_zones.map((zone) => (
                            <div
                              key={zone.zone_id}
                              className="bg-black/30 rounded p-2 flex justify-between items-center"
                            >
                              <div>
                                <span className="font-bold">{zone.name}</span>
                                <span className="mx-2" dir="rtl">({zone.name_fa})</span>
                              </div>
                              <div className="text-right text-sm">
                                <div>👥 {zone.population.toLocaleString()} people</div>
                                <div>📍 {zone.radius_km} km radius</div>
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {/* Facilities in danger */}
                        {warning.affected_zones.length > 0 && (
                          <div className="mt-2 text-sm">
                            <span className="font-bold">🏭 Facilities: </span>
                            {warning.affected_zones
                              .flatMap(z => z.facilities)
                              .join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Action Button */}
                  {warning.url && (
                    <a
                      href={warning.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mt-3 px-4 py-2 bg-black/30 rounded hover:bg-black/50 text-sm"
                    >
                      📰 Read Full Report →
                    </a>
                  )}
                </div>
              ))}
            </div>

            {/* Last Update Info */}
            <div className="mt-4 text-center text-gray-400 text-sm">
              Last checked: {data?.last_check || 'Unknown'} | 
              Updates every {data?.refresh_interval_minutes || 20} minutes
            </div>
          </div>
        </div>
      )}

      {/* Collapse button when not expanded but have warnings */}
      {!isExpanded && warnings.length > 0 && !criticalWarnings.length && (
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full bg-yellow-600 text-center py-2 text-sm font-bold hover:bg-yellow-500"
        >
          ⚠️ {warnings.length} Active Warning(s) - Click to expand
        </button>
      )}
    </div>
  );
}

export default EarlyWarningPanel;
