/**
 * src/lib/constants.ts — Application-wide Constants
 */

export const APP_NAME = 'Mini Blinkit ERP'
export const APP_VERSION = '1.0.0'

/** API base URL — Vite dev proxy handles /api → localhost:8000 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/** Default pagination */
export const DEFAULT_PAGE_SIZE = 25
export const MAX_PAGE_SIZE = 200

/** Local storage keys */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'erp_access_token',
  REFRESH_TOKEN: 'erp_refresh_token',
  USER: 'erp_user',
  THEME: 'erp_theme',
  SIDEBAR_COLLAPSED: 'erp_sidebar_collapsed',
} as const

/** Stock reservation timeout (milliseconds) — matches backend setting */
export const STOCK_RESERVATION_TIMEOUT_MS = 60_000

/** Indian GST slabs */
export const GST_RATES = [
  { value: '0', label: '0%' },
  { value: '5', label: '5%' },
  { value: '12', label: '12%' },
  { value: '18', label: '18%' },
  { value: '28', label: '28%' },
] as const

/** User roles with display labels */
export const USER_ROLES = {
  admin: 'Admin',
  warehouse_manager: 'Warehouse Manager',
  inventory_manager: 'Inventory Manager',
  procurement: 'Procurement',
  delivery_manager: 'Delivery Manager',
  viewer: 'Viewer',
} as const

/** Purchase Order status config */
export const PO_STATUS_CONFIG = {
  draft: { label: 'Draft', variant: 'secondary' as const },
  pending_approval: { label: 'Pending Approval', variant: 'warning' as const },
  approved: { label: 'Approved', variant: 'success' as const },
  rejected: { label: 'Rejected', variant: 'danger' as const },
  partially_received: { label: 'Partially Received', variant: 'info' as const },
  fully_received: { label: 'Fully Received', variant: 'success' as const },
  cancelled: { label: 'Cancelled', variant: 'secondary' as const },
} as const

/** GRN status config */
export const GRN_STATUS_CONFIG = {
  draft: { label: 'Draft', variant: 'secondary' as const },
  in_progress: { label: 'In Progress', variant: 'info' as const },
  completed: { label: 'Completed', variant: 'success' as const },
  discrepancy: { label: 'Discrepancy', variant: 'warning' as const },
} as const

/** Query stale times — controls React Query refetch frequency */
export const STALE_TIMES = {
  /** Real-time data: inventory counts, order status */
  REALTIME: 30_000,      // 30 seconds
  /** Frequently changing: orders, GRN lists */
  SHORT: 2 * 60_000,     // 2 minutes
  /** Moderately changing: PO lists, supplier lists */
  MEDIUM: 5 * 60_000,    // 5 minutes
  /** Reference data: categories, warehouses, products */
  LONG: 30 * 60_000,     // 30 minutes
} as const
