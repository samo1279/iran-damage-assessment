const TYPE_COLORS: Record<string, string> = {
  nuclear_facility: '#f85149',
  missile_production: '#f0883e',
  missile_base: '#d29922',
  air_base: '#58a6ff',
  naval_base: '#58a6ff',
  military_base: '#79c0ff',
  air_defense: '#bc8cff',
  radar_site: '#bc8cff',
  command_center: '#ff7b72',
  research_center: '#d2a8ff',
  ammunition_depot: '#ffa657',
  drone_base: '#d29922',
  energy: '#3fb950',
  refinery: '#3fb950',
  government: '#ff7b72',
  port: '#39d2c0',
  underground_facility: '#8b949e',
  enrichment_plant: '#f85149',
  irgc_hq: '#ff7b72',
  s300_battery: '#bc8cff',
  bavar373_battery: '#bc8cff',
  pipeline: '#3fb950',
  uranium_mine: '#f85149',
  yellowcake_plant: '#f85149',
}

export function getTypeColor(type: string): string {
  return TYPE_COLORS[type] ?? '#58a6ff'
}

export function getConfColor(pct: number): string {
  if (pct >= 80) return '#f85149'
  if (pct >= 50) return '#d29922'
  if (pct >= 20) return '#58a6ff'
  return '#8b949e'
}

export type BadgeVariant = 'red' | 'orange' | 'blue' | 'purple'

export function getConfBadgeVariant(pct: number): BadgeVariant {
  if (pct >= 80) return 'red'
  if (pct >= 50) return 'orange'
  if (pct >= 20) return 'blue'
  return 'purple'
}
