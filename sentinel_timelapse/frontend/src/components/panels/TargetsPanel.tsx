import { useState, useMemo } from 'react'
import { useTargets } from '../../api/hooks'
import { useAppStore } from '../../store/useAppStore'
import { getTypeColor } from '../../utils/colors'

export function TargetsPanel() {
  const { data } = useTargets()
  const flyTo = useAppStore((s) => s.flyTo)

  const [category, setCategory] = useState('')
  const [province, setProvince] = useState('')
  const [search, setSearch] = useState('')

  const targets = data?.targets ?? []
  const categories = data?.categories ?? []
  const provinces = data?.provinces ?? []

  const filtered = useMemo(() => {
    let list = targets
    if (category) list = list.filter((t) => t.category === category)
    if (province) list = list.filter((t) => t.province === province)
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          t.type.toLowerCase().includes(q) ||
          (t.description ?? '').toLowerCase().includes(q),
      )
    }
    return list
  }, [targets, category, province, search])

  return (
    <>
      {/* Filters */}
      <div className="flex gap-1.5 flex-wrap mb-2">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="bg-bg border border-border text-gray-300 px-2 py-1 rounded text-[11px]"
        >
          <option value="">All Categories ({categories.length})</option>
          {[...categories].sort().map((c) => (
            <option key={c} value={c}>
              {c.replace(/_/g, ' ')}
            </option>
          ))}
        </select>

        <select
          value={province}
          onChange={(e) => setProvince(e.target.value)}
          className="bg-bg border border-border text-gray-300 px-2 py-1 rounded text-[11px]"
        >
          <option value="">All Provinces ({provinces.length})</option>
          {[...provinces].sort().map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search targets..."
          className="flex-1 min-w-[100px] bg-bg border border-border text-gray-300 px-2 py-1 rounded text-[11px]"
        />
      </div>

      <div className="text-[11px] text-dim mb-2">
        Showing {filtered.length} of {targets.length} targets
      </div>

      <div>
        {filtered.map((t) => (
          <div
            key={t.id}
            onClick={() => flyTo(t.lat, t.lon)}
            className="flex items-center gap-2 py-2 px-2 border-b border-border cursor-pointer hover:bg-accent/5 transition"
          >
            <div
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ background: getTypeColor(t.type) }}
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-gray-300 truncate">
                {t.name}
              </div>
              <div className="text-[10px] text-dim">
                {t.type.replace(/_/g, ' ')} -- {t.province}
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
