// Request timeout for mobile networks
const TIMEOUT_MS = 30000

export async function fetchJSON<T>(url: string, opts?: RequestInit): Promise<T | null> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS)
  
  try {
    const res = await fetch(url, {
      ...opts,
      signal: controller.signal,
      keepalive: true,
    })
    clearTimeout(timeoutId)
    
    if (!res.ok) {
      console.error('HTTP error:', res.status, url)
      return null
    }
    return (await res.json()) as T
  } catch (e) {
    clearTimeout(timeoutId)
    if ((e as Error).name === 'AbortError') {
      console.error('Request timeout:', url)
    } else {
      console.error('Fetch error:', url, e)
    }
    return null
  }
}

export function postJSON<T>(url: string, body: unknown): Promise<T | null> {
  return fetchJSON<T>(url, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Cache-Control': 'max-age=300', // 5 min cache hint
    },
    body: JSON.stringify(body),
  })
}
