/**
 * src/stores/ui.store.ts — UI Global State
 *
 * Manages global UI state: sidebar collapsed, dark mode, active toast notifications.
 *
 * WHY separate UI store (not in auth store):
 *   Single Responsibility Principle. UI preferences are unrelated to auth state.
 *   Changing dark mode should not affect auth subscriptions.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { STORAGE_KEYS } from '@/lib/constants'

type Theme = 'dark' | 'light' | 'system'

interface UIState {
  theme: Theme
  sidebarCollapsed: boolean
  breadcrumbs: Array<{ label: string; href?: string }>

  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setBreadcrumbs: (crumbs: Array<{ label: string; href?: string }>) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      sidebarCollapsed: false,
      breadcrumbs: [],

      setTheme: (theme) => {
        set({ theme })
        // Apply theme to DOM immediately
        const root = document.documentElement
        if (theme === 'dark') {
          root.classList.add('dark')
        } else if (theme === 'light') {
          root.classList.remove('dark')
        } else {
          // System preference
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          root.classList.toggle('dark', prefersDark)
        }
      },

      toggleTheme: () => {
        const current = get().theme
        const next = current === 'dark' ? 'light' : 'dark'
        get().setTheme(next)
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
      },

      setSidebarCollapsed: (collapsed) => {
        set({ sidebarCollapsed: collapsed })
      },

      setBreadcrumbs: (breadcrumbs) => {
        set({ breadcrumbs })
      },
    }),
    {
      name: STORAGE_KEYS.THEME,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
)
