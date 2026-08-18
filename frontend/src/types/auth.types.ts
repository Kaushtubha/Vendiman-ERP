/**
 * src/types/auth.types.ts — Authentication Type Definitions
 */

export type UserRole =
  | 'admin'
  | 'warehouse_manager'
  | 'inventory_manager'
  | 'procurement'
  | 'delivery_manager'
  | 'viewer'

export type UserStatus = 'active' | 'inactive' | 'suspended'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  status: UserStatus
  avatar_url?: string
  last_login_at?: string
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  user: User
}

export interface RefreshResponse {
  access_token: string
  token_type: 'bearer'
}

/** JWT payload decoded from the access token. */
export interface TokenPayload {
  sub: string         // User UUID
  email: string
  role: UserRole
  type: 'access'
  jti: string
  iat: number
  exp: number
}

/** Permission map — which roles can perform which actions. */
export type Permission =
  | 'products.read'
  | 'products.write'
  | 'products.delete'
  | 'suppliers.read'
  | 'suppliers.write'
  | 'purchase_orders.read'
  | 'purchase_orders.create'
  | 'purchase_orders.approve'
  | 'grn.read'
  | 'grn.create'
  | 'inventory.read'
  | 'inventory.adjust'
  | 'warehouses.read'
  | 'warehouses.transfer'
  | 'orders.read'
  | 'orders.create'
  | 'delivery_challans.read'
  | 'delivery_challans.create'
  | 'reports.read'
  | 'reports.export'
  | 'users.manage'

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: [
    'products.read', 'products.write', 'products.delete',
    'suppliers.read', 'suppliers.write',
    'purchase_orders.read', 'purchase_orders.create', 'purchase_orders.approve',
    'grn.read', 'grn.create',
    'inventory.read', 'inventory.adjust',
    'warehouses.read', 'warehouses.transfer',
    'orders.read', 'orders.create',
    'delivery_challans.read', 'delivery_challans.create',
    'reports.read', 'reports.export',
    'users.manage',
  ],
  warehouse_manager: [
    'products.read',
    'suppliers.read',
    'purchase_orders.read',
    'grn.read', 'grn.create',
    'inventory.read', 'inventory.adjust',
    'warehouses.read', 'warehouses.transfer',
    'delivery_challans.read', 'delivery_challans.create',
    'reports.read', 'reports.export',
  ],
  inventory_manager: [
    'products.read', 'products.write',
    'inventory.read', 'inventory.adjust',
    'warehouses.read',
    'reports.read',
  ],
  procurement: [
    'products.read', 'products.write',
    'suppliers.read', 'suppliers.write',
    'purchase_orders.read', 'purchase_orders.create',
    'grn.read',
    'inventory.read',
    'reports.read', 'reports.export',
  ],
  delivery_manager: [
    'orders.read',
    'delivery_challans.read', 'delivery_challans.create',
    'inventory.read',
    'reports.read',
  ],
  viewer: [
    'products.read',
    'suppliers.read',
    'purchase_orders.read',
    'grn.read',
    'inventory.read',
    'warehouses.read',
    'orders.read',
    'delivery_challans.read',
    'reports.read',
  ],
}
