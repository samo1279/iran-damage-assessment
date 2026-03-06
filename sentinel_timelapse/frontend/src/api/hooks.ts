import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { fetchJSON, postJSON } from './client'
import type {
  TargetsResponse,
  FullAssessmentResponse,
  NewsResponse,
  StrikeAssessmentResponse,
} from '../types'

// Detect mobile for adaptive fetching
const isMobile = () => typeof window !== 'undefined' && window.innerWidth < 768

/** SSE hook for live updates */
export function useLiveUpdates() {
  const queryClient = useQueryClient()
  
  useEffect(() => {
    let eventSource: EventSource | null = null
    
    const connect = () => {
      eventSource = new EventSource('/api/stream')
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'osint_update' && data.has_new_data) {
            // Invalidate queries to refetch fresh data
            queryClient.invalidateQueries({ queryKey: ['full-assessment'] })
            queryClient.invalidateQueries({ queryKey: ['news'] })
            queryClient.invalidateQueries({ queryKey: ['quick-stats'] })
            console.log('📡 Live update received:', data.timestamp)
          }
        } catch (e) {
          // Heartbeat or parse error - ignore
        }
      }
      
      eventSource.onerror = () => {
        eventSource?.close()
        // Reconnect after 30 seconds
        setTimeout(connect, 30000)
      }
    }
    
    // Only connect SSE on desktop (save mobile battery)
    if (!isMobile()) {
      connect()
    }
    
    return () => {
      eventSource?.close()
    }
  }, [queryClient])
}

/** Quick stats — FAST endpoint for initial page load (<100ms) */
export function useQuickStats() {
  return useQuery({
    queryKey: ['quick-stats'],
    queryFn: () => fetchJSON<{
      success: boolean
      target_count: number
      strike_count: number
      osint_articles: number
      confirmed: number
      likely: number
      categories: Record<string, number>
      provinces: string[]
      last_osint_refresh: string | null
    }>('/api/quick-stats'),
    staleTime: 1 * 60 * 1000, // 1 minute - faster refresh
    gcTime: 10 * 60 * 1000,
    refetchInterval: isMobile() ? 3 * 60 * 1000 : 60 * 1000, // 1 min desktop, 3 min mobile
  })
}

/** Known targets — rarely changes, very long stale time */
export function useTargets() {
  return useQuery({
    queryKey: ['targets'],
    queryFn: () => fetchJSON<TargetsResponse>('/api/known-targets'),
    staleTime: 10 * 60 * 1000, // 10 min - refresh more often
    gcTime: 60 * 60 * 1000,
    refetchOnMount: false,
    refetchInterval: 5 * 60 * 1000, // Check for new targets every 5 min
  })
}

/** Full OSINT + correlation assessment — LIVE refresh */
export function useFullAssessment() {
  const mobile = isMobile()
  return useQuery({
    queryKey: ['full-assessment'],
    queryFn: () =>
      postJSON<FullAssessmentResponse>('/api/full-assessment', {
        with_satellite: false,
      }),
    // Faster refresh for live data
    refetchInterval: mobile ? 3 * 60 * 1000 : 60 * 1000, // 1 min desktop, 3 min mobile
    staleTime: mobile ? 2 * 60 * 1000 : 30 * 1000, // 30s desktop, 2 min mobile
    gcTime: 30 * 60 * 1000,
    refetchOnMount: true, // Always get fresh data on mount
    refetchOnWindowFocus: true, // Refresh when user returns to tab
  })
}

/** GDELT news — LIVE refresh */
export function useNews() {
  const mobile = isMobile()
  return useQuery({
    queryKey: ['news'],
    queryFn: () =>
      fetchJSON<NewsResponse>('/api/news?q=iran+military+strike+attack&limit=25'),
    refetchInterval: mobile ? 3 * 60 * 1000 : 60 * 1000, // 1 min desktop, 3 min mobile
    staleTime: mobile ? 2 * 60 * 1000 : 30 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  })
}

/** On-demand satellite assessment for a single target */
export function useStrikeAssessment() {
  return useMutation({
    mutationFn: (targetId: string) =>
      postJSON<StrikeAssessmentResponse>('/api/assess-strike', {
        target_id: targetId,
        with_satellite: true,
      }),
  })
}
