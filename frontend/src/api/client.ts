/**
 * src/api/client.ts — Axios HTTP Client
 *
 * PATTERN: Axios instance with interceptors for auth, error handling,
 * and request/response transformation.
 *
 * WHY Axios (not fetch):
 *   - Request/response interceptors: Centralized auth header injection and
 *     token refresh — without duplicating in every API call.
 *   - Automatic JSON parsing: `response.data` is already parsed.
 *   - Request cancellation: via AbortController (same as fetch, but ergonomic).
 *   - Error handling: Axios throws on 4xx/5xx; fetch doesn't.
 *   - WHY NOT fetch: Implementing interceptors with fetch requires a custom
 *     wrapper of similar complexity to Axios anyway.
 *
 * TOKEN REFRESH FLOW:
 *   Access token (60min) expires → 401 received → interceptor automatically
 *   calls /auth/refresh → gets new access token → retries original request.
 *   The user never sees an error or needs to re-login.
 *
 *   WHY queue pending requests during refresh:
 *   If 5 API calls fire simultaneously when the token expires, without a
 *   queue they all try to refresh simultaneously → 5 concurrent refresh
 *   requests → race condition → 4 of them fail with "refresh token already
 *   used" (if single-use) or create 5 valid sessions.
 *   The queue holds all requests until one refresh completes, then retries all.
 *
 * SECURITY:
 *   - Tokens stored in memory (authStore Zustand) by default.
 *   - Access token persisted to sessionStorage (tab-scoped).
 *   - Refresh token is HttpOnly cookie set by the server (XSS-safe).
 *   - Never store tokens in localStorage (accessible to XSS injected scripts).
 */

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios'
import { useAuthStore } from '@/stores/auth.store'
import { STORAGE_KEYS } from '@/lib/constants'

// ── API Client Instance ────────────────────────────────────────────────────
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30_000,               // 30 seconds — reasonable for reports/exports
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  withCredentials: true,         // Send HttpOnly cookies (refresh token)
})

// ── Request Interceptor ────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request ID for correlation (matches backend RequestIdMiddleware)
    config.headers['X-Request-ID'] = crypto.randomUUID()

    return config
  },
  (error) => Promise.reject(error)
)

// ── Token Refresh Queue ────────────────────────────────────────────────────
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else if (token) {
      resolve(token)
    }
  })
  failedQueue = []
}

// ── Response Interceptor ───────────────────────────────────────────────────
apiClient.interceptors.response.use(
  // Success: return response as-is
  (response: AxiosResponse) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Handle 401 — token expired → attempt refresh
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      if (isRefreshing) {
        // Another refresh is in progress — queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Attempt token refresh — refresh token sent as HttpOnly cookie
        const response = await apiClient.post<{
          data: { access_token: string }
        }>('/auth/refresh')

        const newToken = response.data.data.access_token
        useAuthStore.getState().setAccessToken(newToken)

        processQueue(null, newToken)

        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        // Refresh failed — force logout
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Re-throw for React Query to handle
    return Promise.reject(error)
  }
)

// ── Typed Response Helper ──────────────────────────────────────────────────
/**
 * Standard API response envelope shape from the backend.
 */
export interface APIResponse<T = unknown> {
  success: boolean
  message: string
  data: T
  meta: PaginationMeta | Record<string, unknown> | null
}

export interface PaginationMeta {
  page: number
  limit: number
  total: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface PaginatedData<T> {
  items: T[]
  meta: PaginationMeta
}

/**
 * Extract typed data from the API response envelope.
 *
 * Usage:
 *   const products = await apiClient.get<APIResponse<Product[]>>('/products')
 *   const data = extractData(products) // typed as Product[]
 */
export function extractData<T>(response: AxiosResponse<APIResponse<T>>): T {
  return response.data.data
}

export default apiClient
