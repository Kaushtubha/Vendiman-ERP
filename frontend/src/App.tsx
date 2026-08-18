/**
 * src/App.tsx — Root Application Component
 *
 * PATTERN: Provider composition at the root level.
 *
 * WHY all providers at root:
 *   React Query, router, and toast providers must wrap the entire component
 *   tree. Placing them at root ensures no provider boundary issues when
 *   components deep in the tree consume them.
 *
 * PROVIDER ORDER MATTERS:
 *   QueryClientProvider → must wrap everything (hooks used everywhere)
 *   Toaster → must render at root level (portals render outside component tree)
 *   AppRouter → the actual application
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from '@/components/ui/toaster'
import { AppRouter } from '@/router'
import { useUIStore } from '@/stores/ui.store'
import { useEffect } from 'react'

// ── React Query Client Configuration ──────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /**
       * WHY staleTime > 0: With staleTime=0 (default), React Query
       * refetches every time a component mounts. For ERP data that changes
       * infrequently (product list, supplier list), this creates unnecessary
       * API load. Each query sets its own staleTime based on data volatility.
       */
      staleTime: 2 * 60_000,           // 2 minutes default
      gcTime: 10 * 60_000,             // Cache for 10 minutes (previously cacheTime)
      retry: 1,                         // Retry once on network error
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
      refetchOnWindowFocus: false,      // Don't refetch when tab regains focus
      refetchOnMount: true,
    },
    mutations: {
      retry: 0,                         // Never retry mutations (idempotency concerns)
    },
  },
})

// ── App Component ──────────────────────────────────────────────────────────
export default function App() {
  const { theme } = useUIStore()

  // Apply theme on mount and when it changes
  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else if (theme === 'light') {
      root.classList.remove('dark')
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      root.classList.toggle('dark', prefersDark)
    }
  }, [theme])

  return (
    <QueryClientProvider client={queryClient}>
      <AppRouter />
      <Toaster />
      {import.meta.env.DEV && (
        <ReactQueryDevtools
          initialIsOpen={false}
          buttonPosition="bottom-right"
        />
      )}
    </QueryClientProvider>
  )
}
