/**
 * src/router/ProtectedRoute.tsx — Authentication & Authorization Guard
 *
 * PATTERN: Route guard component — wraps protected routes with auth check.
 *
 * WHY component-level protection (not router-level middleware):
 *   React Router v6 doesn't have middleware. Guards as wrapper components
 *   are the idiomatic React Router approach. They allow fine-grained control:
 *   some routes require specific roles, others just need authentication.
 *
 * BEHAVIOR:
 *   - Not authenticated → redirect to /login (with `from` state for redirect back)
 *   - Authenticated but wrong role → redirect to /unauthorized
 *   - Authenticated & authorized → render children
 *
 * IMPORTANT: This is a UX guard, not a security boundary.
 *   The backend enforces all permissions on every API call.
 *   Client-side route protection is purely for user experience —
 *   preventing a viewer from seeing the "Create PO" form is UX,
 *   not security. The API will reject the POST anyway.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth.store'
import type { Permission } from '@/types/auth.types'

interface ProtectedRouteProps {
  /**
   * Required permission to access this route.
   * If not specified, only authentication is required.
   */
  requiredPermission?: Permission
  /** Redirect to this path if unauthorized. Defaults to /unauthorized */
  unauthorizedRedirect?: string
}

export function ProtectedRoute({
  requiredPermission,
  unauthorizedRedirect = '/unauthorized',
}: ProtectedRouteProps) {
  const location = useLocation()
  const { user, hasPermission } = useAuthStore()

  // Not authenticated → redirect to login, preserve intended destination
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Has permission requirement → check it
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to={unauthorizedRedirect} replace />
  }

  // All checks pass → render the route
  return <Outlet />
}

/**
 * Public route guard — redirects authenticated users away from login page.
 * Prevents showing login page to already-logged-in users.
 */
export function PublicOnlyRoute() {
  const { user } = useAuthStore()

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
