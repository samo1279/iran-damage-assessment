import { useAppStore } from '../store/useAppStore'

export function HelpModal() {
  const helpOpen = useAppStore((s) => s.helpOpen)
  const toggleHelp = useAppStore((s) => s.toggleHelp)

  if (!helpOpen) return null

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={toggleHelp}
    >
      <div
        className="w-[720px] max-h-[85vh] rounded-xl border border-border bg-card overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-lg font-bold text-white tracking-wide">
            User Guide -- Iran OSINT Dashboard v6.0
          </h2>
          <button
            onClick={toggleHelp}
            className="text-dim hover:text-white text-xl leading-none"
          >
            x
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto max-h-[72vh] px-6 py-5 space-y-6 text-sm text-dim leading-relaxed">
          <Section title="Overview">
            <p>
              This dashboard provides near-real-time open-source intelligence
              (OSINT) monitoring of Iranian military, nuclear, and strategic
              infrastructure. It combines GDELT news analysis, Sentinel-2
              satellite imagery, and SAR change detection to identify potential
              strike activity across 175+ known targets.
            </p>
          </Section>

          <Section title="Tabs">
            <ul className="list-disc list-inside space-y-1">
              <li>
                <strong className="text-white">STRIKES</strong> -- Assessed
                targets ranked by strike probability. Click any card to fly to
                the location on the map.
              </li>
              <li>
                <strong className="text-white">TARGETS</strong> -- Full
                searchable/filterable list of all monitored sites. Filter by
                category, province, or free-text search.
              </li>
              <li>
                <strong className="text-white">NEWS</strong> -- Latest GDELT
                articles related to Iranian military activity, with relevance
                scoring.
              </li>
              <li>
                <strong className="text-white">SATELLITE</strong> -- On-demand
                satellite image fetch for any target. Shows before/after images,
                change heatmap, and damage verdict.
              </li>
            </ul>
          </Section>

          <Section title="Map Interaction">
            <ul className="list-disc list-inside space-y-1">
              <li>
                Colored dots represent target sites -- each color corresponds to
                a facility type (military base, nuclear site, air defense, etc.)
              </li>
              <li>
                Hover on a dot to see the target name.
              </li>
              <li>
                Click a dot for a popup with details and a "Fetch Satellite
                Imagery" link.
              </li>
              <li>
                Red pulsing dashed rings indicate high-confidence strike
                assessments.
              </li>
              <li>
                City name labels provide geographic orientation.
              </li>
            </ul>
          </Section>

          <Section title="Stats Bar">
            <p>
              The top stats bar shows real-time counts: total monitored targets,
              OSINT news articles found, assessed strike events, confirmed and
              likely events, and the timestamp of the last automated scan.
            </p>
          </Section>

          <Section title="Auto-Refresh">
            <p>
              The dashboard automatically polls the backend every 5 minutes for
              fresh OSINT assessments and news. You do not need to manually
              refresh. The LIVE indicator in the top bar pulses when a background
              fetch is active.
            </p>
          </Section>

          <Section title="Strike Assessment Methodology">
            <ul className="list-disc list-inside space-y-1">
              <li>
                GDELT global news is queried for keywords related to Iranian
                military infrastructure and geopolitical events.
              </li>
              <li>
                Articles are correlated against all 175+ known target
                coordinates using geographic and semantic matching.
              </li>
              <li>
                A combined score (0--100%) is computed from OSINT source count,
                keyword density, geographic proximity, and optional satellite
                change detection.
              </li>
              <li>
                Verdicts: CONFIRMED STRIKE, LIKELY STRIKE, POSSIBLE STRIKE,
                MONITORING, or NO EVIDENCE.
              </li>
            </ul>
          </Section>

          <Section title="Satellite Imagery">
            <ul className="list-disc list-inside space-y-1">
              <li>
                Uses Sentinel-2 optical imagery and Sentinel-1 SAR data where
                available.
              </li>
              <li>
                Before/After images show the site at two time points.
              </li>
              <li>
                The change heatmap highlights areas of potential structural
                change.
              </li>
              <li>
                Satellite fetch is on-demand -- select a target and click
                "Fetch" in the Satellite tab or from the map popup.
              </li>
            </ul>
          </Section>

          <Section title="Data Sources">
            <ul className="list-disc list-inside space-y-1">
              <li>GDELT Project (Global Database of Events, Language, and Tone)</li>
              <li>Copernicus Sentinel-2 multispectral imagery</li>
              <li>Copernicus Sentinel-1 SAR imagery</li>
              <li>Open-source geographic and facility databases</li>
            </ul>
          </Section>

          <Section title="Disclaimer">
            <p className="text-yellow-400/80">
              This tool is for educational and research purposes only.
              Assessments are based on publicly available open-source data and
              automated algorithms. Results should not be treated as confirmed
              intelligence and may contain false positives.
            </p>
          </Section>
        </div>
      </div>
    </div>
  )
}

/* ── little helper ─────────────────────────────────────────────── */
function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section>
      <h3 className="text-white font-semibold mb-1">{title}</h3>
      {children}
    </section>
  )
}
