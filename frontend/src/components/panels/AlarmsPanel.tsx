import { useQuery } from '@tanstack/react-query';
import { fetchJSON } from '../../api/client';
import { Spinner } from '../ui/Spinner';
import { useAppStore } from '../../store/useAppStore';

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

interface MapMarker {
  lat: number;
  lon: number;
  name: string;
  type: string;
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
  // NEW fields
  target_location?: { lat: number; lon: number; name: string; type: string };
  map_marker?: MapMarker;
  video_urls?: string[];
}

interface WarningsResponse {
  success: boolean;
  warnings: Warning[];
  count: number;
  last_check: string;
  refresh_interval_minutes: number;
}

export function AlarmsPanel() {
  const flyTo = useAppStore((s) => s.flyTo);
  const { data, isLoading, refetch, isFetching } = useQuery<WarningsResponse>({
    queryKey: ['early-warnings'],
    queryFn: async () => {
      const response = await fetchJSON<WarningsResponse>('/api/early-warnings');
      return response || { success: false, warnings: [], count: 0, last_check: '', refresh_interval_minutes: 20 };
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const warnings = data?.warnings || [];

  const getLevelStyles = (level: string) => {
    switch (level) {
      case 'IMMINENT':
        return { bg: 'bg-red-600/20', border: 'border-red-500', text: 'text-red-400', badge: 'bg-red-600' };
      case 'WARNING':
        return { bg: 'bg-orange-600/20', border: 'border-orange-500', text: 'text-orange-400', badge: 'bg-orange-600' };
      case 'ALERT':
        return { bg: 'bg-yellow-600/20', border: 'border-yellow-500', text: 'text-yellow-400', badge: 'bg-yellow-600' };
      case 'WATCH':
        return { bg: 'bg-blue-600/20', border: 'border-blue-500', text: 'text-blue-400', badge: 'bg-blue-600' };
      default:
        return { bg: 'bg-gray-600/20', border: 'border-gray-500', text: 'text-gray-400', badge: 'bg-gray-600' };
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'IMMINENT': return '🚨';
      case 'WARNING': return '⚠️';
      case 'ALERT': return '⚡';
      case 'WATCH': return '👁️';
      default: return '📢';
    }
  };

  // Fly to location on map
  const handleFlyToLocation = (lat: number, lon: number) => {
    flyTo(lat, lon, 14);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-10 text-dim">
        <Spinner />
        <span className="mt-3 text-sm">Checking warning sources...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-black text-dim uppercase tracking-widest flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
          Early Warning System
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="text-[10px] font-bold text-accent hover:text-white transition-colors disabled:opacity-50"
        >
          {isFetching ? '⏳ Checking...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Persian title */}
      <div className="text-center py-2 bg-white/5 rounded-lg border border-white/10">
        <div className="text-lg font-bold text-white" dir="rtl">نظام هشدار اولیه</div>
        <div className="text-[10px] text-gray-400 uppercase tracking-wider">Civilian Evacuation Alerts</div>
      </div>

      {/* No warnings state */}
      {warnings.length === 0 && (
        <div className="bg-green-900/20 border border-green-500/30 rounded-xl p-4 text-center">
          <div className="text-3xl mb-2">✅</div>
          <div className="text-green-400 font-bold">NO ACTIVE WARNINGS</div>
          <div className="text-green-400/60 font-bold mt-1" dir="rtl">هیچ هشداری فعال نیست</div>
          <div className="text-[10px] text-gray-500 mt-2">
            Last checked: {data?.last_check || 'Unknown'}
          </div>
        </div>
      )}

      {/* Warning cards */}
      {warnings.map((warning) => {
        const styles = getLevelStyles(warning.level);
        return (
          <div
            key={warning.id}
            className={`${styles.bg} border ${styles.border} rounded-xl p-4 transition-all hover:scale-[1.02]`}
          >
            {/* Level badge */}
            <div className="flex items-center justify-between mb-3">
              <span className={`${styles.badge} px-2 py-1 rounded text-xs font-black text-white flex items-center gap-1`}>
                {getLevelIcon(warning.level)} {warning.level}
              </span>
              <span className="text-[10px] text-gray-500">{warning.source_name}</span>
            </div>

            {/* Title */}
            <h3 className={`${styles.text} font-bold text-sm mb-2 leading-tight`}>
              {warning.title}
            </h3>

            {/* Messages */}
            <div className="space-y-2 mb-3">
              <div className="text-xs text-gray-300">{warning.message_en}</div>
              <div className="text-sm text-white font-bold" dir="rtl">{warning.message_fa}</div>
            </div>

            {/* Action */}
            <div className="bg-black/30 rounded-lg p-2 mb-3">
              <div className="text-[10px] text-gray-500 uppercase mb-1">Recommended Action</div>
              <div className="text-xs text-white">{warning.action}</div>
            </div>

            {/* Affected zones */}
            {warning.affected_zones.length > 0 && (
              <div className="space-y-2">
                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  🎯 Affected Areas ({warning.affected_zones.length})
                </div>
                {warning.affected_zones.map((zone) => (
                  <button
                    key={zone.zone_id}
                    onClick={() => handleFlyToLocation(zone.lat, zone.lon)}
                    className="w-full bg-black/30 rounded-lg p-2 flex justify-between items-center hover:bg-black/50 transition-colors cursor-pointer text-left"
                  >
                    <div>
                      <span className="text-xs font-bold text-white">{zone.name}</span>
                      <span className="text-xs text-gray-400 mx-2">|</span>
                      <span className="text-xs text-gray-300" dir="rtl">{zone.name_fa}</span>
                      <span className="text-[9px] text-accent ml-2">📍 View on Map</span>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] text-red-400 font-bold">
                        👥 {zone.population.toLocaleString()}
                      </div>
                      <div className="text-[9px] text-gray-500">
                        {zone.radius_km}km radius
                      </div>
                    </div>
                  </button>
                ))}

                {/* Facilities */}
                <div className="text-[10px] text-gray-500">
                  <span className="font-bold">🏭 Facilities: </span>
                  {warning.affected_zones.flatMap(z => z.facilities).slice(0, 5).join(', ')}
                  {warning.affected_zones.flatMap(z => z.facilities).length > 5 && '...'}
                </div>
              </div>
            )}

            {/* Target location - precise coordinate */}
            {warning.map_marker && (
              <button
                onClick={() => handleFlyToLocation(warning.map_marker!.lat, warning.map_marker!.lon)}
                className="w-full mt-3 bg-red-900/30 border border-red-500/50 rounded-lg p-2 flex items-center justify-between hover:bg-red-900/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎯</span>
                  <div>
                    <div className="text-xs font-bold text-red-400">{warning.map_marker.name}</div>
                    <div className="text-[9px] text-gray-400">
                      {warning.map_marker.lat.toFixed(4)}, {warning.map_marker.lon.toFixed(4)}
                    </div>
                  </div>
                </div>
                <span className="text-xs text-accent font-bold">VIEW ON MAP →</span>
              </button>
            )}

            {/* Video - if available */}
            {warning.video_urls && warning.video_urls.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  🎥 Video / Media
                </div>
                {warning.video_urls.map((videoUrl, idx) => (
                  <div key={idx}>
                    {videoUrl.includes('twitter.com') || videoUrl.includes('x.com') ? (
                      // Twitter embed
                      <a
                        href={videoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block bg-black/30 rounded-lg p-3 hover:bg-black/50 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">▶️</span>
                          <div>
                            <div className="text-xs text-white font-bold">Watch Video on 𝕏</div>
                            <div className="text-[9px] text-gray-400">Click to open in new tab</div>
                          </div>
                        </div>
                      </a>
                    ) : (
                      // Direct video
                      <video
                        src={videoUrl}
                        controls
                        className="w-full rounded-lg max-h-48 bg-black"
                        preload="metadata"
                      >
                        <source src={videoUrl} type="video/mp4" />
                      </video>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Link to source */}
            {warning.url && (
              <a
                href={warning.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block mt-3 text-center text-[10px] text-accent hover:text-white py-2 bg-white/5 rounded-lg transition-colors"
              >
                📰 View Original Report →
              </a>
            )}
          </div>
        );
      })}

      {/* Info footer - Show monitored sources */}
      <div className="pt-3 border-t border-white/10 space-y-2">
        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider text-center">
          Monitored Sources
        </div>
        <div className="grid grid-cols-3 gap-2 text-center">
          <a href="https://x.com/IDF" target="_blank" rel="noopener noreferrer" 
             className="bg-blue-900/20 border border-blue-500/30 rounded-lg py-2 px-1 hover:bg-blue-900/40 transition-colors">
            <div className="text-base">🇮🇱</div>
            <div className="text-[9px] text-blue-400 font-bold">@IDF</div>
          </a>
          <a href="https://x.com/CENTCOM" target="_blank" rel="noopener noreferrer"
             className="bg-green-900/20 border border-green-500/30 rounded-lg py-2 px-1 hover:bg-green-900/40 transition-colors">
            <div className="text-base">🇺🇸</div>
            <div className="text-[9px] text-green-400 font-bold">@CENTCOM</div>
          </a>
          <a href="https://x.com/Vahid" target="_blank" rel="noopener noreferrer"
             className="bg-purple-900/20 border border-purple-500/30 rounded-lg py-2 px-1 hover:bg-purple-900/40 transition-colors">
            <div className="text-base">🇮🇷</div>
            <div className="text-[9px] text-purple-400 font-bold">@Vahid</div>
          </a>
        </div>
        <div className="text-center text-[9px] text-gray-600">
          + Reuters, AP, GDELT | Updates every {data?.refresh_interval_minutes || 20} min
        </div>
      </div>
    </div>
  );
}
