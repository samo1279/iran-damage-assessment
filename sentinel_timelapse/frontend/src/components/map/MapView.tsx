import { useEffect, useMemo } from 'react'
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
  const { data: targetData } = useTargets()
  const { data: assessmentData } = useFullAssessment()
  const setSatTargetId = useAppStore((s) => s.setSatTargetId)
  const setActiveTab = useAppStore((s) => s.setActiveTab)

  const targets = targetData?.targets ?? []
  const assessments = assessmentData?.assessments ?? []

  const strikeMap = useMemo(() => {
    const m = new Map<string, (typeof assessments)[0]>()
    assessments.forEach((a) => m.set(a.target_id, a))
    return m
  }, [assessments])

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
            radius={isStrike ? 8 : 5}
            pathOptions={{
              fillColor: color,
              color: '#000',
              weight: 1,
              fillOpacity: isStrike ? 0.9 : 0.6,
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
                <strong>{t.name}</strong>
                <br />
                <em>{t.type.replace(/_/g, ' ')}</em> -- {t.province}
                {isStrike && (
                  <>
                    <br />
                    <br />
                    <strong>
                      Strike confidence:{' '}
                      {Math.round((strike.combined_score ?? 0) * 100)}%
                    </strong>
                    <br />
                    Verdict: {strike.verdict ?? 'N/A'}
                    <br />
                    Sources: {strike.osint_sources ?? 0}
                  </>
                )}
                {t.description && (
                  <>
                    <br />
                    <small>{t.description}</small>
                  </>
                )}
                <br />
                <br />
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault()
                    setSatTargetId(t.id)
                    setActiveTab('satellite')
                  }}
                >
                  Fetch Satellite Imagery
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
            radius={14}
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

/* ── Main MapView ────────────────────────────────────────────────── */
export function MapView() {
  return (
    <MapContainer
      center={[32.5, 53]}
      zoom={6}
      style={{ width: '100%', height: '100%' }}
      zoomControl
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
        maxZoom={18}
      />
      <CityLabels />
      <TargetMarkers />
      <FlyToHandler />
    </MapContainer>
  )
}
