/**
 * ChemicalFamilyBanner — ADR-007: Disclosure for chemical family expansion.
 *
 * Displays when a search is expanded to include related chemicals
 * (e.g., "Lead" expands to include "Lead Compounds" and "Lead and Lead Compounds").
 */
import type { SearchExpansion } from '../api/types'

interface ChemicalFamilyBannerProps {
  expansion: SearchExpansion
  /** Callback when user clicks "Search exact term only" */
  onSearchExact?: () => void
}

/**
 * Informational banner showing which chemicals are included in the search.
 * Provides transparency about the expanded search per right-to-know principles.
 */
export function ChemicalFamilyBanner({
  expansion,
  onSearchExact,
}: ChemicalFamilyBannerProps): JSX.Element | null {
  if (!expansion.expanded) return null

  // Format the list of chemicals for display
  const chemicalList = expansion.searched_chemicals
    .map((c) => `"${c}"`)
    .join(', ')

  return (
    <div
      data-testid="chemical-family-banner"
      style={{
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '6px',
        padding: '10px 12px',
        margin: '8px 0',
        fontSize: '12px',
        lineHeight: 1.5,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <span style={{ fontSize: '14px' }}>ℹ️</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, color: '#1e40af', marginBottom: '4px' }}>
            Combined results for {expansion.family_name} family
          </div>
          <div style={{ color: '#1e3a8a', marginBottom: '6px' }}>
            Showing releases reported as {chemicalList} per EPA TRI reporting categories.
          </div>
          {expansion.description && (
            <div style={{ color: '#3b82f6', fontSize: '11px', marginBottom: '6px' }}>
              {expansion.description}
            </div>
          )}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            {expansion.nlm_url && (
              <a
                href={expansion.nlm_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: '#2563eb',
                  textDecoration: 'none',
                  fontSize: '11px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '3px',
                }}
              >
                Learn more (NLM) ↗
              </a>
            )}
            {onSearchExact && (
              <button
                onClick={onSearchExact}
                style={{
                  background: 'transparent',
                  border: '1px solid #93c5fd',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  color: '#1d4ed8',
                  cursor: 'pointer',
                  fontSize: '11px',
                }}
              >
                Search exact term only
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
