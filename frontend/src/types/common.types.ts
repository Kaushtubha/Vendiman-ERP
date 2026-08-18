/**
 * src/types/common.types.ts — Shared TypeScript Interfaces
 *
 * WHY separate types directory (not inline in components):
 *   - Types are reused across API functions, hooks, and components.
 *   - Centralizing types creates a contract between frontend and backend.
 *   - When the API schema changes, update the type here → TypeScript
 *     immediately flags all consumers that need updating.
 *   - In a larger team, types can be auto-generated from OpenAPI spec
 *     using openapi-typescript. The structure here anticipates that migration.
 */

// ── Pagination ─────────────────────────────────────────────────────────────
export interface PaginationMeta {
  page: number
  limit: number
  total: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface PaginatedResponse<T> {
  success: boolean
  message: string
  data: T[]
  meta: PaginationMeta
}

export interface SingleResponse<T> {
  success: boolean
  message: string
  data: T
  meta: null | Record<string, unknown>
}

// ── Filter & Sort ──────────────────────────────────────────────────────────
export interface PaginationParams {
  page?: number
  limit?: number
}

export interface SortParams {
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
}

export interface SearchParams {
  search?: string
}

export type ListParams = PaginationParams & SortParams & SearchParams

// ── Common Entity Fields ────────────────────────────────────────────────────
/** All entities have these audit fields from the backend. */
export interface AuditFields {
  id: string              // UUID
  created_at: string      // ISO 8601
  updated_at: string      // ISO 8601
  created_by?: string     // User ID who created
  updated_by?: string     // User ID who last updated
}

// ── Address (reused across Supplier, Warehouse, Company) ──────────────────
export interface Address {
  line1: string
  line2?: string
  city: string
  state: string
  pincode: string
  country: string
}

// ── Select Options (for dropdowns) ────────────────────────────────────────
export interface SelectOption<T = string> {
  value: T
  label: string
  disabled?: boolean
}

// ── API Error Shape ────────────────────────────────────────────────────────
export interface APIError {
  success: false
  message: string
  data: null
  meta: {
    code: string
    errors?: Array<{ field: string; message: string; type: string }>
    [key: string]: unknown
  }
}

// ── Upload Response ────────────────────────────────────────────────────────
export interface FileUploadResponse {
  url: string
  filename: string
  size_bytes: number
  content_type: string
}

// ── GST Types ──────────────────────────────────────────────────────────────
export type GSTRate = '0' | '5' | '12' | '18' | '28'

export interface GSTBreakdown {
  gst_rate: GSTRate
  taxable_amount: number
  cgst_rate: number
  cgst_amount: number
  sgst_rate: number
  sgst_amount: number
  igst_rate: number
  igst_amount: number
  total_gst: number
  total_with_gst: number
}
