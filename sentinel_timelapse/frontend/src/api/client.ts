export async function fetchJSON<T>(url: string, opts?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(url, opts)
    return (await res.json()) as T
  } catch (e) {
    console.error('Fetch error:', url, e)
    return null
  }
}

export function postJSON<T>(url: string, body: unknown): Promise<T | null> {
  return fetchJSON<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
