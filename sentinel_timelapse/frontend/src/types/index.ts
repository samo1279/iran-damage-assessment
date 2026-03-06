/* ── Target from /api/known-targets ──────────────────────────────── */
export interface Target {
  id: string
  name: string
  type: string
  category: string
  lat: number
  lon: number
  bbox: [number, number, number, number]
  description: string
  keywords: string[]
  province: string
}

export interface TargetsResponse {
  success: boolean
  targets: Target[]
  count: number
  categories: string[]
  provinces: string[]
}

/* ── Assessment from /api/full-assessment ────────────────────────── */
export interface Assessment {
  strike_id: string
  target_id: string
  target_name: string
  lat: number
  lon: number
  osint_confidence: string
  osint_sources: number
  satellite_checked: boolean
  satellite_change_detected: boolean
  satellite_change_percent: number
  satellite_event_count: number
  before_image: string | null
  after_image: string | null
  heatmap: string | null
  verdict: string
  verdict_reasons: string[]
  combined_score: number
  source_count?: number
}

export interface AssessmentSummary {
  total_strikes: number
  confirmed: number
  likely: number
  reported: number
  unconfirmed: number
  confirmed_targets: string[]
  likely_targets: string[]
  narrative: string
}

export interface FullAssessmentResponse {
  success: boolean
  osint: {
    articles_found: number
    articles_with_locations: number
    targets_mentioned: Record<string, unknown>
  }
  assessments: Assessment[]
  summary: AssessmentSummary
  timeline: Record<string, unknown>
}

/* ── News from /api/news ─────────────────────────────────────────── */
export interface NewsArticle {
  url: string
  title: string
  seendate: string
  domain: string
  language: string
  sourcecountry: string
}

export interface NewsResponse {
  articles: NewsArticle[]
  error?: string
}

/* ── Strike assessment from /api/assess-strike ───────────────────── */
export interface StrikeAssessmentResponse {
  success: boolean
  error?: string
  strike_id: string
  target_name: string
  osint_confidence: string
  osint_sources: number
  satellite_checked: boolean
  satellite_change_detected: boolean
  satellite_change_percent: number
  satellite_event_count: number
  before_image: string | null
  after_image: string | null
  heatmap: string | null
  cloud_mask_image?: string | null
  cloud_coverage_percent?: number
  verdict: string
  verdict_reasons: string[]
  combined_score: number
}
