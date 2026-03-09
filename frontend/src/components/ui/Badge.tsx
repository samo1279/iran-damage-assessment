import { getConfBadgeVariant } from '../../utils/colors'

const VARIANT_CLS: Record<string, string> = {
  red: 'bg-red-500/15 text-[#f85149]',
  orange: 'bg-orange-500/15 text-[#d29922]',
  blue: 'bg-blue-500/15 text-[#58a6ff]',
  purple: 'bg-purple-500/15 text-[#bc8cff]',
}

export function Badge({ value, label }: { value: number; label?: string }) {
  const v = getConfBadgeVariant(value)
  return (
    <span
      className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase shrink-0 ${VARIANT_CLS[v]}`}
    >
      {label ?? `${value}%`}
    </span>
  )
}
