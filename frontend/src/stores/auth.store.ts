/**
 * src/stores/auth.store.ts — Authentication Global State
 *
 * PATTERN: Zustand store with persist middleware for cross-tab token sharing.
 *
 * WHY Zustand (not Redux, React Context):
 *   - Redux: Excellent for complex state machines, but auth state is simple.
 *     Redux adds 4x the boilerplate (actions, reducers, selectors) for no benefit.
 *   - React Context: Every context update re-renders ALL consumers.
 *     With auth state in context, adding a user avatar update re-renders
 *     the entire component tree. Zustand re-renders only subscribed components.
 *   - Zustand: Minimal API, selector-based subscriptions, built-in persist.
 *     `useAuthStore(state => state.user)` only re-renders when user changes.
 *
 * SECURITY:
 *   - Access token stored in memory (store state) — disappears on page refresh.
 *   - User object persisted to sessionStorage (cleared when tab closes).
 *   - Refresh token is an HttpOnly cookie — invisible to JavaScript (XSS-safe).
 *   - WHY NOT localStorage: localStorage persists across sessions and is
 *     accessible to any JavaScript on the page. If an XSS attack occurs,
 *     localStorage tokens are immediately exfiltrated.
 *
 * TOKEN PERSISTENCE:
 *   On page refresh, the access token is gone (memory only).
 *   The Axios interceptor detects the 401 and uses the refresh token cookie
 *   to get a new access token silently. The user sees no interruption.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { type User, type Permission, ROLE_PERMISSIONS } from '@/types/auth.types'
import { STORAGE_KEYS } from '@/lib/constants'

interface AuthState {
  /** JWT access token — in memory only (no persistence) */
  accessToken: string | null
  /** Current user — persisted to sessionStorage */
  user: User | null
  /** True when auth state is being rehydrated from storage */
  isLoading: boolean

  // Actions
  setAuth: (token: string, user: User) => void
  setAccessToken: (token: string) => void
  logout: () => void
  hasPermission: (permission: Permission) => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      user: null,
      isLoading: false,

      setAuth: (token, user) => {
        set({ accessToken: token, user })
      },

      setAccessToken: (token) => {
        set({ accessToken: token })
      },

      logout: () => {
        set({ accessToken: null, user: null })
      },

      /**
       * Check if the current user has a specific permission.
       *
       * WHY client-side permission check:
       *   Used for UI gating (show/hide buttons, routes). It is NOT a
       *   security boundary — the backend enforces all permissions.
       *   Client-side permission checks are UX improvements only.
       */
      hasPermission: (permission: Permission) => {
        const user = get().user
        if (!user) return false
        const rolePermissions = ROLE_PERMISSIONS[user.role] ?? []
        return rolePermissions.includes(permission)
      },
    }),
    {
      name: STORAGE_KEYS.USER,
      storage: createJSONStorage(() => sessionStorage), // Tab-scoped
      // Only persist user (not access token — memory only)
      partialize: (state) => ({ user: state.user }),
    }
  )
)
