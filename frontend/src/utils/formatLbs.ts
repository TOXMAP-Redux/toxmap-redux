/**
 * Utility for formatting release quantities.
 * UX Invariant 8: all release quantities must use formatLbs — never inline toLocaleString.
 */

/**
 * Formats a number of pounds with comma separators and "lbs" suffix.
 * @example formatLbs(8205) → "8,205 lbs"
 * @example formatLbs(null) → "—"
 */
export function formatLbs(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${value.toLocaleString('en-US')} lbs`
}

/**
 * Formats a number with comma separators (no unit suffix).
 * @example formatNumber(12485) → "12,485"
 */
export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '—'
  return value.toLocaleString('en-US')
}
