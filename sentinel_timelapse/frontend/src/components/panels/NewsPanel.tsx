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
    <div>
      {articles.map((a, i) => {
        const color =
          a.prob >= 60 ? '#f85149' : a.prob >= 30 ? '#d29922' : '#8b949e'
        return (
          <div key={i} className="py-2.5 px-1 border-b border-border">
            <div className="flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-semibold text-gray-300 hover:text-accent leading-snug block"
                >
                  {a.title ?? 'Untitled'}
                </a>
                <div className="text-[10px] text-dim mt-0.5">
                  {a.domain ?? ''}{' '}
                  {a.seendate ? `-- ${a.seendate.substring(0, 10)}` : ''}
                </div>
              </div>
              <span
                className="text-[11px] font-bold whitespace-nowrap shrink-0"
                style={{ color }}
              >
                {a.prob}%
              </span>
            </div>
            <ProbBar value={a.prob} color={color} />
          </div>
        )
      })}
    </div>
  )
}
