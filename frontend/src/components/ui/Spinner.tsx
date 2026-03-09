export function Spinner({ size = 32 }: { size?: number }) {
  return (
    <div
      className="border-[3px] border-border border-t-accent rounded-full animate-spin"
      style={{ width: size, height: size }}
    />
  )
}
