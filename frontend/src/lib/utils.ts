/**
 * src/lib/utils.ts — Shared Utility Functions
 *
 * WHY centralized utils (not inline in components):
 *   - cn() is used in every Shadcn UI component — it must be importable
 *     from a stable path (@/lib/utils)
 *   - Formatting functions (currency, dates, numbers) are business logic.
 *     Centralizing ensures: ₹1,23,456.78 format is consistent across all
 *     modules (Inventory value, PO amount, dashboard KPIs).
 *
 * DESIGN: This module is intentionally kept small.
 *   Domain-specific logic belongs in service-specific hooks/utils.
 *   This file contains only universal, module-agnostic utilities.
 */

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind CSS classes with conflict resolution.
 *
 * WHY twMerge: Tailwind generates atomic classes. When two conflicting
 * classes are applied (e.g., `p-4` and `p-2`), the last one in CSS wins —
 * but CSS order is unpredictable. twMerge resolves conflicts by
 * understanding Tailwind's class semantics.
 *
 * Example: cn('p-4', 'p-2') → 'p-2' (not 'p-4 p-2')
 *
 * WHY clsx: Handles conditional class application cleanly:
 *   cn('base', { 'text-red-500': hasError, 'text-green-500': isValid })
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ── Currency Formatting ────────────────────────────────────────────────────
/**
 * Format a number as Indian Rupees with Indian number system (lakhs, crores).
 *
 * WHY Indian locale (not standard):
 *   Indian number system groups as 12,34,567 (not 1,234,567).
 *   Incorrect formatting in a ₹100 crore inventory report is a serious error.
 *
 * Examples:
 *   formatCurrency(1234567.89) → "₹12,34,567.89"
 *   formatCurrency(0)           → "₹0.00"
 */
export function formatCurrency(
  amount: number,
  options: { decimals?: number; compact?: boolean } = {}
): string {
  const { decimals = 2, compact = false } = options

  if (compact && amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)} Cr`
  }
  if (compact && amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)} L`
  }

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount)
}

/**
 * Format a number with Indian number system commas.
 *
 * Examples:
 *   formatNumber(1234567) → "12,34,567"
 *   formatNumber(0)       → "0"
 */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-IN').format(value)
}

// ── Date Formatting ────────────────────────────────────────────────────────
/**
 * Format a date string to DD MMM YYYY format.
 *
 * WHY DD MMM YYYY (not ISO, not MM/DD/YYYY):
 *   - "27 Jan 2025" is unambiguous — Jan vs Jan, not 01/27 vs 27/01
 *   - Used on PO PDFs, GRN forms, delivery challans — professional look
 *
 * Examples:
 *   formatDate("2025-01-27T10:30:00Z") → "27 Jan 2025"
 *   formatDate(null) → "—"
 */
export function formatDate(
  date: string | Date | null | undefined,
  format: 'short' | 'long' | 'datetime' = 'short'
): string {
  if (!date) return '—'

  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return '—'

  if (format === 'datetime') {
    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: 'Asia/Kolkata',
    })
  }

  if (format === 'long') {
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      timeZone: 'Asia/Kolkata',
    })
  }

  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'Asia/Kolkata',
  })
}

/**
 * Return a relative time string.
 *
 * Examples:
 *   timeAgo("2025-01-27T09:00:00Z") → "3 hours ago"
 */
export function timeAgo(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(d)
}

// ── String Utilities ───────────────────────────────────────────────────────
/** Truncate a string to a max length with ellipsis. */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - 3) + '...'
}

/** Convert snake_case or SCREAMING_SNAKE to Title Case for display. */
export function humanize(str: string): string {
  return str
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

// ── Stock Utilities ────────────────────────────────────────────────────────
/**
 * Return stock level status for color-coding.
 *
 * Used in inventory tables and dashboard alerts.
 * Thresholds are configurable — could come from product settings in the future.
 */
export type StockLevel = 'ok' | 'low' | 'critical' | 'out'

export function getStockLevel(quantity: number, reorderPoint: number = 10): StockLevel {
  if (quantity === 0) return 'out'
  if (quantity <= reorderPoint * 0.3) return 'critical'
  if (quantity <= reorderPoint) return 'low'
  return 'ok'
}

export const STOCK_LEVEL_CONFIG: Record<StockLevel, { label: string; className: string }> = {
  ok: { label: 'In Stock', className: 'text-success bg-success-muted' },
  low: { label: 'Low Stock', className: 'text-warning bg-warning-muted' },
  critical: { label: 'Critical', className: 'text-danger bg-danger-muted' },
  out: { label: 'Out of Stock', className: 'text-danger bg-danger-muted' },
}

// ── Validation Utilities ───────────────────────────────────────────────────
/** Check if a string is a valid GSTIN (Indian GST number). */
export function isValidGSTIN(gstin: string): boolean {
  const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/
  return gstinRegex.test(gstin)
}

/** Check if a string is a valid Indian mobile number. */
export function isValidMobile(mobile: string): boolean {
  return /^[6-9]\d{9}$/.test(mobile.replace(/\s|-/g, ''))
}
