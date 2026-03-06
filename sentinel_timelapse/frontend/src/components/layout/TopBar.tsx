import { useAppStore } from '../../store/useAppStore'
import { useFullAssessment } from '../../api/hooks'

export function TopBar() {
  const toggleHelp = useAppStore((s) => s.toggleHelp)
  const { isFetching } = useFullAssessment()

  return (
    <div className="bg-card border-b border-border px-4 py-2 flex items-center gap-3 shrink-0">
      <h1 className="text-base font-bold text-white whitespace-nowrap">
        IRAN DAMAGE ASSESSMENT PLATFORM
      </h1>
      <span className="text-[11px] bg-accent text-black px-2 py-0.5 rounded-full font-bold">
        v6.0
      </span>

      <span className="ml-auto text-xs text-dim flex items-center gap-1.5">
        <span
          className={`w-2 h-2 rounded-full ${
            isFetching ? 'bg-warning' : 'bg-success animate-pulse-live'
          }`}
        />
        {isFetching ? 'Scanning...' : 'Live -- monitoring'}
      </span>

      <button
        onClick={toggleHelp}
        className="border border-border text-accent px-3 py-1 rounded text-xs font-semibold hover:bg-accent hover:text-black transition"
      >
        ? HELP
      </button>
    </div>
  )
}
