import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import 'leaflet/dist/leaflet.css'
import './index.css'

// Lazy load the main app for faster initial paint
const App = React.lazy(() => import('./App'))

// Aggressive caching for mobile
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      staleTime: 5 * 60 * 1000, // 5 minutes default
      gcTime: 30 * 60 * 1000, // 30 minutes cache
      networkMode: 'offlineFirst', // Use cache first on mobile
    },
  },
})

// Loading spinner for initial load
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen bg-[#0d1117]">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <div className="text-gray-400 text-sm">Loading Intel Platform...</div>
    </div>
  </div>
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<LoadingFallback />}>
        <App />
      </Suspense>
    </QueryClientProvider>
  </React.StrictMode>,
)
