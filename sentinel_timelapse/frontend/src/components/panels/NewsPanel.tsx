import { useMemo } from 'react'
import { useNews } from '../../api/hooks'
import { Spinner } from '../ui/Spinner'
import { ProbBar } from '../ui/ProbBar'

const KEYWORDS = [
  'strike', 'attack', 'bomb', 'missile', 'explosion', 'damage',
  'destroy', 'target', 'military', 'nuclear', 'irgc', 'iran',
  'base', 'hit', 'raid',
]

/** Deterministic hash so % doesn't flicker on re-render */
function hash(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

function computeRelevance(title: string): number {
  const lower = title.toLowerCase()
  const matches = KEYWORDS.filter((k) => lower.includes(k)).length
  const h = hash(lower) % 15
  if (matches === 0) return 5 + h
  return Math.min(95, Math.round((matches / KEYWORDS.length) * 100 + h + 10))
}

export function NewsPanel() {
  const { data, isLoading } = useNews()

  const articles = useMemo(() => {
    return (data?.articles ?? []).map((a) => ({
      ...a,
      prob: computeRelevance(a.title ?? ''),
    }))
  }, [data])

  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-10 text-dim">
        <Spinner />
        <span className="mt-3 text-sm">Scanning news feeds...</span>
      </div>
    )
  }

  if (!articles.length) {
    return (
      <div className="bg-card border border-border rounded-md p-5 text-center text-dim text-sm">
        No news articles found. Auto-refreshing every 5 minutes.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="text-[10px] font-black text-dim mb-2 uppercase tracking-widest flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
        Live OSINT Intelligence Feed
      </div>
      {articles.map((a, i) => {
        const color =
          a.prob >= 60 ? '#f85149' : a.prob >= 30 ? '#d29922' : '#8b949e'
        return (
          <div key={i} className="bg-card/40 border border-white/5 rounded-xl p-3 hover:border-accent/40 hover:bg-accent/5 transition-all group">
            <div className="flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-black text-gray-200 hover:text-accent leading-tight block uppercase tracking-tight group-hover:text-white transition-colors"
                >
                  {a.title ?? 'UNTITLED INTELLIGENCE REPORT'}
                </a>
                <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 mt-2 uppercase tracking-wider">
                  <span className="text-secondary">{a.domain ?? 'OSINT SOURCE'}</span>
                  <span className="text-gray-800">|</span>
                  <span>{a.seendate ? a.seendate.substring(0, 10) : 'RECENT'}</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span
                  className="text-xs font-black whitespace-nowrap shrink-0"
                  style={{ color }}
                >
                  {a.prob}% RELEVANCE
                </span>
              </div>
            </div>
            <div className="mt-3">
              <ProbBar value={a.prob} color={color} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
