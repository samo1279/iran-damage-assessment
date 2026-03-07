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

/** SSE hook for live updates - DISABLED to reduce server load */
export function useLiveUpdates() {
  // SSE disabled - causes too many connections on Railway free tier
  // Data refreshes every 5-10 minutes instead
  return
}

/** Quick stats — FAST endpoint for initial page load (<100ms) */
export function useQuickStats() {
  const mobile = isMobile()
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
    staleTime: mobile ? 5 * 60 * 1000 : 2 * 60 * 1000, // 5 min mobile, 2 min desktop
    gcTime: 30 * 60 * 1000,
    refetchInterval: mobile ? 10 * 60 * 1000 : 3 * 60 * 1000, // 10 min mobile, 3 min desktop
    refetchOnMount: false, // Don't refetch if cached
    retry: 2, // Retry twice on failure
  })
}

/** Known targets — rarely changes, very long stale time */
export function useTargets() {
  const mobile = isMobile()
  return useQuery({
    queryKey: ['targets'],
    queryFn: () => fetchJSON<TargetsResponse>('/api/known-targets'),
    staleTime: mobile ? 30 * 60 * 1000 : 15 * 60 * 1000, // 30 min mobile, 15 min desktop
    gcTime: 60 * 60 * 1000,
    refetchOnMount: false,
    refetchOnWindowFocus: false, // Don't refetch targets on focus
    refetchInterval: mobile ? false : 15 * 60 * 1000, // No auto-refresh on mobile
    retry: 2,
  })
}

/** Full OSINT + correlation assessment — Cached on server */
export function useFullAssessment() {
  const mobile = isMobile()
  return useQuery({
    queryKey: ['full-assessment'],
    queryFn: () => fetchJSON<FullAssessmentResponse>('/api/full-assessment'),
    // Much slower refresh to reduce server load
    refetchInterval: mobile ? false : 5 * 60 * 1000, // 5 min desktop, disabled on mobile
    staleTime: mobile ? 10 * 60 * 1000 : 3 * 60 * 1000, // 10 min mobile, 3 min desktop
    gcTime: 30 * 60 * 1000,
    refetchOnMount: false, // Use cache if available
    refetchOnWindowFocus: false, // Don't refetch on every tab switch
    retry: 2,
  })
}

/** GDELT news — LIVE refresh */
export function useNews() {
  const mobile = isMobile()
  return useQuery({
    queryKey: ['news'],
    queryFn: () =>
      fetchJSON<NewsResponse>('/api/news?q=iran+military+strike+attack&limit=25'),
    refetchInterval: mobile ? false : 5 * 60 * 1000, // 5 min desktop, disabled on mobile
    staleTime: mobile ? 10 * 60 * 1000 : 3 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

/** On-demand satellite assessment for a single target with Polling support */
export function useStrikeAssessment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (targetId: string) => {
      // 1. Start the task
      const startRes = await postJSON<{ status: string, task_id?: string } & StrikeAssessmentResponse>(
        '/api/assess-strike', 
        { target_id: targetId, with_satellite: true }
      )
      
      if (!startRes) throw new Error('Failed to connect to server')
      
      // If already done (served from cache), return immediately
      if (startRes.status === 'completed' || startRes.success) {
        return startRes as StrikeAssessmentResponse
      }
      
      const taskId = startRes.task_id
      if (!taskId) throw new Error('No task ID returned')
      
      // 2. Poll until complete (longer timeout for satellite processing)
      let attempts = 0
      const maxAttempts = 120 // 6 minutes total: 2s * 120
      
      while (attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 2000)) // Wait 2s (faster polling)
        const pollRes = await fetchJSON<{ status: string; progress?: number } & StrikeAssessmentResponse>(
          `/api/task-status/${taskId}`
        )
        
        if (pollRes?.status === 'completed' || pollRes?.success) {
          return pollRes as StrikeAssessmentResponse
        }
        
        if (pollRes?.status === 'error') {
          throw new Error(pollRes.error || 'Analysis failed on server')
        }
        
        // Log progress for debugging
        if (pollRes?.progress) {
          console.log(`[Analysis] Progress: ${pollRes.progress}%`)
        }
        
        attempts++
      }
      
      throw new Error('Analysis timed out after 6 minutes - satellite imagery may be unavailable')
    },
    onSuccess: () => {
      // Refresh related data if needed
      queryClient.invalidateQueries({ queryKey: ['quick-stats'] })
    }
  })
}
