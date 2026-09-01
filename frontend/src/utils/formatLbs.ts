/**
 * Utility for formatting release quantities.
 * UX Invariant 8: all release quantities must use formatLbs — never inline toLocaleString.
 */

/**
 * Formats a number of pounds with comma separators and "lbs" suffix.
 * Rounds to nearest whole number for readability.
 * @example formatLbs(8205.7) → "8,206 lbs"
 * @example formatLbs(null) → "—"
 */
export function formatLbs(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${Math.round(value).toLocaleString('en-US')} lbs`
}

/**
 * Formats a number with comma separators (no unit suffix).
 * Rounds to nearest whole number for readability.
 * @example formatNumber(12485.3) → "12,485"
 */
export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '—'
  return Math.round(value).toLocaleString('en-US')
}
