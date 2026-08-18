import React, { Suspense } from 'react'
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import { ProtectedRoute, PublicOnlyRoute } from './ProtectedRoute'

// ── Lazy-loaded page modules ──────────────────────────────────────────────
// Auth
const LoginPage = React.lazy(() => import('@/pages/auth/LoginPage'))
const UnauthorizedPage = React.lazy(() => import('@/pages/error/UnauthorizedPage'))
const NotFoundPage = React.lazy(() => import('@/pages/error/NotFoundPage'))

// Layout & Dashboard
const AppLayout = React.lazy(() => import('@/components/layout/AppLayout'))
const DashboardPage = React.lazy(() => import('@/pages/dashboard/DashboardPage'))

// Operations Modules
const ProductsPage = React.lazy(() => import('@/pages/products/ProductsPage'))
const SuppliersPage = React.lazy(() => import('@/pages/suppliers/SuppliersPage'))
const PurchaseOrdersPage = React.lazy(() => import('@/pages/purchase-orders/PurchaseOrdersPage'))
const GRNPage = React.lazy(() => import('@/pages/grn/GRNPage'))
const InventoryPage = React.lazy(() => import('@/pages/inventory/InventoryPage'))
const ProfitabilityPage = React.lazy(() => import('@/pages/profitability/ProfitabilityPage'))
const AlertsPage = React.lazy(() => import('@/pages/alerts/AlertsPage'))
const BulkUploadPage = React.lazy(() => import('@/pages/upload/BulkUploadPage'))

function PageLoader() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <p className="text-xs text-muted-foreground font-medium">Loading Vendiman...</p>
      </div>
    </div>
  )
}

const router = createBrowserRouter([
  // ── Public Routes ──
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        path: '/login',
        element: (
          <Suspense fallback={<PageLoader />}>
            <LoginPage />
          </Suspense>
        ),
      },
    ],
  },

  // ── Protected Operations Routes ──
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: (
          <Suspense fallback={<PageLoader />}>
            <AppLayout />
          </Suspense>
        ),
        children: [
          {
            path: '/dashboard',
            element: (
              <Suspense fallback={<PageLoader />}>
                <DashboardPage />
              </Suspense>
            ),
          },
          {
            path: '/products',
            element: (
              <Suspense fallback={<PageLoader />}>
                <ProductsPage />
              </Suspense>
            ),
          },
          {
            path: '/suppliers',
            element: (
              <Suspense fallback={<PageLoader />}>
                <SuppliersPage />
              </Suspense>
            ),
          },
          {
            path: '/purchase-orders',
            element: (
              <Suspense fallback={<PageLoader />}>
                <PurchaseOrdersPage />
              </Suspense>
            ),
          },
          {
            path: '/grn',
            element: (
              <Suspense fallback={<PageLoader />}>
                <GRNPage />
              </Suspense>
            ),
          },
          {
            path: '/inventory',
            element: (
              <Suspense fallback={<PageLoader />}>
                <InventoryPage />
              </Suspense>
            ),
          },
          {
            path: '/profitability',
            element: (
              <Suspense fallback={<PageLoader />}>
                <ProfitabilityPage />
              </Suspense>
            ),
          },
          {
            path: '/alerts',
            element: (
              <Suspense fallback={<PageLoader />}>
                <AlertsPage />
              </Suspense>
            ),
          },
          {
            path: '/upload',
            element: (
              <Suspense fallback={<PageLoader />}>
                <BulkUploadPage />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },

  // ── Error & Fallbacks ──
  {
    path: '/unauthorized',
    element: (
      <Suspense fallback={<PageLoader />}>
        <UnauthorizedPage />
      </Suspense>
    ),
  },
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '*',
    element: (
      <Suspense fallback={<PageLoader />}>
        <NotFoundPage />
      </Suspense>
    ),
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
