import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchJSON, postJSON } from './client'
import type {
  TargetsResponse,
  FullAssessmentResponse,
  NewsResponse,
  StrikeAssessmentResponse,
} from '../types'

/** Known targets — rarely changes, long stale time */
export function useTargets() {
  return useQuery({
    queryKey: ['targets'],
    queryFn: () => fetchJSON<TargetsResponse>('/api/known-targets'),
    staleTime: 10 * 60 * 1000,
  })
}

/** Full OSINT + correlation assessment — auto-refetch every 5 min */
export function useFullAssessment() {
  return useQuery({
    queryKey: ['full-assessment'],
    queryFn: () =>
      postJSON<FullAssessmentResponse>('/api/full-assessment', {
        with_satellite: false,
      }),
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
  })
}

/** GDELT news — auto-refetch every 5 min */
export function useNews() {
  return useQuery({
    queryKey: ['news'],
    queryFn: () =>
      fetchJSON<NewsResponse>('/api/news?q=iran+military+strike+attack&limit=25'),
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
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
