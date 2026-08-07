/**
 * FacilitySearchInput — ADR-010 facility search autocomplete.
 * Allows searching facilities by TRI ID or name.
 * Results show match_type badge and relevance score.
 */
import { useState } from 'react'
import { useFacilitySearch } from '../../hooks/useFacilitySearch'
import type { FacilitySearchResult } from '../../api/types'

interface FacilitySearchInputProps {
  /** 2-letter state filter (matches SearchPanel's state filter) */
  state?: string
  /** Called when user selects a facility from dropdown */
  onSelect: (facility: FacilitySearchResult) => void
}

/**
 * Facility search input with autocomplete dropdown.
 * Shows ranked results with ID or name match badges.
 */
export function FacilitySearchInput({
  state,
  onSelect,
}: FacilitySearchInputProps): JSX.Element {
  const [query, setQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)

  const { results, loading, error } = useFacilitySearch(query, state)

  const handleSelect = (facility: FacilitySearchResult) => {
    setQuery('')
    setShowDropdown(false)
    onSelect(facility)
  }

  return (
    <div className="toxmap-facility-search" style={{ position: 'relative' }}>
      <label
        htmlFor="facility-search-input"
        style={{
          display: 'block',
          fontSize: '11px',
          fontWeight: 500,
          color: '#6b7280',
          marginBottom: '3px',
        }}
      >
        Site (TRI ID, EPA ID or Name)
      </label>
      <input
        id="facility-search-input"
        data-testid="facility-search-input"
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setShowDropdown(true)
        }}
        onFocus={() => setShowDropdown(true)}
        onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
        placeholder="e.g. 89319BHPCP, WAD009248671, or Hanford"
        autoComplete="off"
        style={{
          width: '100%',
          padding: '8px 10px',
          fontSize: '13px',
          border: '1px solid #d1d5db',
          borderRadius: '4px',
          outline: 'none',
          fontFamily: 'inherit',
        }}
      />

      {/* Autocomplete dropdown */}
      {showDropdown && query.length >= 2 && (
        <ul
          data-testid="facility-search-dropdown"
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: '100%',
            zIndex: 50,
            maxHeight: '240px',
            overflowY: 'auto',
            background: '#fff',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
            marginTop: '2px',
            padding: 0,
            listStyle: 'none',
          }}
        >
          {loading && (
            <li
              style={{
                padding: '10px 12px',
                fontSize: '12px',
                color: '#9ca3af',
              }}
            >
              Searching…
            </li>
          )}

          {!loading && error && (
            <li
              style={{
                padding: '10px 12px',
                fontSize: '12px',
                color: '#dc2626',
              }}
            >
              Search failed
            </li>
          )}

          {!loading && !error && results.length === 0 && (
            <li
              style={{
                padding: '10px 12px',
                fontSize: '12px',
                color: '#9ca3af',
              }}
            >
              No sites found
            </li>
          )}

          {results.map((site) => (
            <li
              key={`${site.site_type}-${site.site_id}`}
              data-testid="facility-search-option"
              onMouseDown={() => handleSelect(site)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid #f3f4f6',
              }}
              onMouseOver={(e) => {
                ;(e.currentTarget as HTMLElement).style.background = '#eff6ff'
              }}
              onMouseOut={(e) => {
                ;(e.currentTarget as HTMLElement).style.background = ''
              }}
            >
              {/* Site name and badges */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  marginBottom: '2px',
                  flexWrap: 'wrap',
                }}
              >
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: 500,
                    color: '#111827',
                  }}
                >
                  {site.name}
                </span>
                {/* Site type badge (TRI vs Superfund) */}
                <span
                  data-testid="site-type-badge"
                  style={{
                    fontSize: '9px',
                    fontWeight: 600,
                    padding: '1px 5px',
                    borderRadius: '3px',
                    textTransform: 'uppercase',
                    ...(site.site_type === 'tri'
                      ? { background: '#e0e7ff', color: '#4338ca' }
                      : { background: '#fef3c7', color: '#92400e' }),
                  }}
                >
                  {site.site_type === 'tri' ? 'TRI' : 'Superfund'}
                </span>
                {/* Match type badge */}
                <span
                  data-testid="facility-match-badge"
                  style={{
                    fontSize: '9px',
                    fontWeight: 600,
                    padding: '1px 5px',
                    borderRadius: '3px',
                    textTransform: 'uppercase',
                    ...(site.match_type === 'id'
                      ? { background: '#dbeafe', color: '#1e40af' }
                      : { background: '#dcfce7', color: '#166534' }),
                  }}
                >
                  {site.match_type === 'id' ? 'ID Match' : 'Name Match'}
                </span>
              </div>
              {/* Site ID and location */}
              <div
                style={{
                  fontSize: '11px',
                  color: '#6b7280',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontFamily: 'monospace', fontSize: '10px' }}>
                  {site.site_id}
                </span>
                <span>
                  {site.city}
                  {site.city && site.state_code ? ', ' : ''}
                  {site.state_code}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
