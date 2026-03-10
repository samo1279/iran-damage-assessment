import { create } from 'zustand'

export type TabId = 'strikes' | 'targets' | 'news' | 'satellite'

interface TargetDetails {
  id: string
  name: string
  type: string
  lat: number
  lon: number
}

interface MapFocus {
  lat: number
  lon: number
  zoom: number
  /** bumped to force flyTo even if coords are the same */
  ts: number
}

interface AppState {
  activeTab: TabId
  setActiveTab: (tab: TabId) => void

  selectedTarget: TargetDetails | null
  setSelectedTarget: (target: TargetDetails | null) => void

  helpOpen: boolean
  toggleHelp: () => void

  mapFocus: MapFocus | null
  flyTo: (lat: number, lon: number, zoom?: number) => void

  satTargetId: string
  setSatTargetId: (id: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  activeTab: 'strikes',
  setActiveTab: (tab) => set({ activeTab: tab }),

  selectedTarget: null,
  setSelectedTarget: (target) => set({ selectedTarget: target }),

  helpOpen: false,
  toggleHelp: () => set((s) => ({ helpOpen: !s.helpOpen })),

  mapFocus: null,
  flyTo: (lat, lon, zoom = 12) =>
    set({ mapFocus: { lat, lon, zoom, ts: Date.now() } }),

  satTargetId: '',
  setSatTargetId: (id) => set({ satTargetId: id }),
}))
