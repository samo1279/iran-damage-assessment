import { getConfColor } from '../../utils/colors'

export function ProbBar({ value, color }: { value: number; color?: string }) {
  const bg = color ?? getConfColor(value)
  return (
    <div className="h-1 bg-border rounded-full mt-1.5 overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-300"
        style={{ width: `${value}%`, background: bg }}
      />
    </div>
  )
}
