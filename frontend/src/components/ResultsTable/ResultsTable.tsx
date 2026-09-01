/**
 * ResultsTable — stories 3.5.1–3.5.3, 4.1.3, 6.EXPORT.1–4.
 * UX Invariants: 2 (no empty rows), 8 (comma-formatted numbers).
 * Supports TRI mode (sorted by total_release_lbs) and Superfund mode (HRS score).
 * ADR-007: Displays chemical family expansion banner when applicable.
 * 6.EXPORT: CSV download button in results header.
 *
 * PERFORMANCE: Renders max 100 rows initially to avoid 10+ second freezes
 * when handling 22K+ facilities. Users can click "Load more" to see additional results.
 * Sorting is memoized to avoid re-sorting 22K items on every render.
 * Wrapped with React.memo to prevent re-renders during map animations.
 */
import { useState, useEffect, useMemo, useRef, memo } from 'react'
import { formatLbs } from '../../utils/formatLbs'
import type { FacilityCollection, SuperfundCollection, SearchExpansion } from '../../api/types'
import { ChemicalFamilyBanner } from '../ChemicalFamilyBanner'

/** Initial number of rows to render (performance optimization) */
const INITIAL_DISPLAY_LIMIT = 100
/** Number of additional rows to load on each "Load more" click */
const LOAD_MORE_INCREMENT = 100

// Performance debugging - set to true to enable console timing
const PERF_DEBUG = false

interface ResultsTableProps {
  mode: 'tri' | 'superfund' | 'both'
  triData: FacilityCollection | null
  superfundData: SuperfundCollection | null
  loading: boolean
  highlightedFacilityId: string | null
  onHighlight: (id: string | null) => void
  onSelect: (id: string, type: 'tri' | 'superfund') => void
  /** Search expansion info from API response (ADR-007) */
  searchExpansion?: SearchExpansion | null
  /** Callback for "Search exact term only" button (ADR-007) */
  onSearchExact?: () => void
  /** Callback for CSV export button (6.EXPORT.1–4) */
  onExport?: () => void
  /** Whether export is in progress (6.EXPORT.3) */
  exportLoading?: boolean
}

/** HRS score badge coloring (story 4.2.1): red ≥50, amber 28–50, green <28 */
function hrsColor(score: number | null): string {
  if (score === null) return '#6b7280'
  if (score >= 50) return '#ef4444'
  if (score >= 28) return '#f59e0b'
  return '#22c55e'
}

/**
 * Custom comparison function for React.memo.
 * Compares props by value rather than reference to prevent unnecessary re-renders
 * when parent components re-render with equivalent data.
 */
function arePropsEqual(prev: ResultsTableProps, next: ResultsTableProps): boolean {
  // Debug logging
  const reasons: string[] = []
  
  // Primitives - direct comparison
  if (prev.mode !== next.mode) reasons.push('mode')
  if (prev.loading !== next.loading) reasons.push('loading')
  if (prev.highlightedFacilityId !== next.highlightedFacilityId) reasons.push('highlightedFacilityId')
  
  // Collections - compare by features length and reference
  // If reference is same, definitely equal. Otherwise check length as proxy for data change.
  if (prev.triData !== next.triData) {
    const prevLen = prev.triData?.features.length ?? -1
    const nextLen = next.triData?.features.length ?? -1
    if (prevLen !== nextLen) reasons.push(`triData.length (${prevLen} → ${nextLen})`)
  }
  
  if (prev.superfundData !== next.superfundData) {
    const prevLen = prev.superfundData?.features.length ?? -1
    const nextLen = next.superfundData?.features.length ?? -1
    if (prevLen !== nextLen) reasons.push(`superfundData.length (${prevLen} → ${nextLen})`)
  }
  
  // searchExpansion - check existence and key fields
  if (prev.searchExpansion !== next.searchExpansion) {
    const prevExp = prev.searchExpansion
    const nextExp = next.searchExpansion
    if (!prevExp && nextExp) reasons.push('searchExpansion (null → value)')
    if (prevExp && !nextExp) reasons.push('searchExpansion (value → null)')
    if (prevExp && nextExp) {
      if (prevExp.expanded !== nextExp.expanded) reasons.push('searchExpansion.expanded')
      if (prevExp.family_name !== nextExp.family_name) reasons.push('searchExpansion.family_name')
    }
  }
  
  // Functions - onHighlight and onSelect need fresh refs for row interactions
  if (prev.onHighlight !== next.onHighlight) reasons.push('onHighlight')
  if (prev.onSelect !== next.onSelect) reasons.push('onSelect')
  
  // onSearchExact: log for debugging but DON'T count as reason to re-render.
  // This callback is only used for the "Search exact term only" banner action.
  // Its captured values from submission time are what we want anyway.
  // Function ref changes during flyTo animation are noise, not signal.
  if (PERF_DEBUG && prev.onSearchExact !== next.onSearchExact) {
    console.log('[ResultsTable] onSearchExact ref changed (ignored)')
  }
  
  // Export props - compare directly
  if (prev.exportLoading !== next.exportLoading) reasons.push('exportLoading')
  // onExport is a callback - don't trigger re-render on ref change
  if (PERF_DEBUG && prev.onExport !== next.onExport) {
    console.log('[ResultsTable] onExport ref changed (ignored)')
  }
  
  const areEqual = reasons.length === 0
  if (PERF_DEBUG && !areEqual) {
    console.log(`[ResultsTable] arePropsEqual=false, reasons: ${reasons.join(', ')}`)
  }
  
  return areEqual
}

/**
 * Viewport-scoped results table.
 * UX Invariant 2: only non-empty rows rendered (no placeholders).
 * Wrapped with React.memo to prevent re-renders during map fly animations.
 */
export const ResultsTable = memo(function ResultsTable({
  mode,
  triData,
  superfundData,
  loading,
  highlightedFacilityId,
  onHighlight,
  onSelect,
  searchExpansion,
  onSearchExact,
  onExport,
  exportLoading,
}: ResultsTableProps): JSX.Element {
  // Performance logging
  // Render count tracking (enable PERF_DEBUG to log)
  const renderCount = useRef(0)
  if (PERF_DEBUG) {
    renderCount.current++
    console.log(`[ResultsTable] render #${renderCount.current}, triData=${triData?.features.length ?? 'null'}, superfundData=${superfundData?.features.length ?? 'null'}`)
  }

  // Track how many rows to display (reset when data changes)
  const [triDisplayLimit, setTriDisplayLimit] = useState(INITIAL_DISPLAY_LIMIT)
  const [superfundDisplayLimit, setSuperfundDisplayLimit] = useState(INITIAL_DISPLAY_LIMIT)

  // Reset display limits when data changes (new search)
  useEffect(() => {
    setTriDisplayLimit(INITIAL_DISPLAY_LIMIT)
  }, [triData])
  useEffect(() => {
    setSuperfundDisplayLimit(INITIAL_DISPLAY_LIMIT)
  }, [superfundData])

  // PERFORMANCE: Memoize sorting to avoid re-sorting 22K items on every render
  // (highlight changes, mouse events, etc. would otherwise trigger full re-sort)
  const sortedTri = useMemo(() => {
    if (!triData) return []
    if (PERF_DEBUG) console.time('[ResultsTable] sortedTri useMemo')
    const result = [...triData.features].sort(
      (a, b) => (b.properties.total_release_lbs ?? 0) - (a.properties.total_release_lbs ?? 0),
    )
    if (PERF_DEBUG) console.timeEnd('[ResultsTable] sortedTri useMemo')
    return result
  }, [triData])

  const sortedSuperfund = useMemo(() => {
    if (!superfundData) return []
    if (PERF_DEBUG) console.time('[ResultsTable] sortedSuperfund useMemo')
    const result = [...superfundData.features].sort((a, b) => {
      const aScore = a.properties.hrs_score ?? -1
      const bScore = b.properties.hrs_score ?? -1
      return bScore - aScore
    })
    if (PERF_DEBUG) console.timeEnd('[ResultsTable] sortedSuperfund useMemo')
    return result
  }, [superfundData])

  // ── Both mode (TRI + Superfund combined) ──────────────────────────────────
  if (mode === 'both') {
    if (loading && !triData && !superfundData) {
      return <p style={{ padding: '12px', fontSize: '13px', color: '#6b7280', margin: 0 }}>Searching…</p>
    }

    const triCount = triData?.meta.total_count ?? 0
    const superfundCount = superfundData?.meta.total_count ?? 0
    const totalCount = triCount + superfundCount

    if (totalCount === 0 && !loading) {
      return (
        <p style={{ padding: '12px', fontSize: '13px', color: '#6b7280', margin: 0 }}>
          No TRI facilities or Superfund sites found in this area.
        </p>
      )
    }

    // Use pre-sorted arrays (memoized above)
    const displayedTri = sortedTri.slice(0, triDisplayLimit)
    const hasMoreTri = sortedTri.length > triDisplayLimit
    const displayedSuperfund = sortedSuperfund.slice(0, superfundDisplayLimit)
    const hasMoreSuperfund = sortedSuperfund.length > superfundDisplayLimit

    return (
      <div data-testid="results-table" style={{ fontSize: '12px' }}>
        {/* ADR-007: Chemical family expansion banner */}
        {searchExpansion?.expanded && (
          <div style={{ padding: '8px 12px 0' }}>
            <ChemicalFamilyBanner expansion={searchExpansion} onSearchExact={onSearchExact} />
          </div>
        )}
        <div data-testid="results-summary" className="toxmap-results-count" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 10px', fontSize: '11px', color: '#6b7280', margin: 0, borderBottom: '1px solid #f3f4f6' }}>
          <span>{triCount} TRI facilities · {superfundCount} Superfund sites</span>
          {onExport && totalCount > 0 && (
            <button
              type="button"
              data-testid="export-csv-btn"
              onClick={onExport}
              disabled={exportLoading}
              aria-label="Download CSV"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                fontSize: '10px',
                fontWeight: 500,
                color: exportLoading ? '#9ca3af' : '#166534',
                background: '#f0fdf4',
                border: '1px solid #dcfce7',
                borderRadius: '4px',
                cursor: exportLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {exportLoading ? (
                <>
                  <svg width="12" height="12" viewBox="0 0 24 24" style={{ animation: 'spin 1s linear infinite' }}>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="31.4 31.4" />
                  </svg>
                  <span>Exporting…</span>
                </>
              ) : (
                <>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>CSV</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* TRI section */}
        {sortedTri.length > 0 && (
          <>
            <div style={{ padding: '6px 10px', background: '#f0fdf4', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#166534', borderBottom: '1px solid #dcfce7' }}>
              TRI Facilities ({triCount})
            </div>
            <table className="toxmap-results-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <tbody>
                {displayedTri.map((feature) => {
                  const props = feature.properties
                  const isHighlighted = props.tri_facility_id === highlightedFacilityId
                  return (
                    <tr
                      key={props.tri_facility_id}
                      data-testid="results-row"
                      style={{ borderBottom: '1px solid #f3f4f6', cursor: 'pointer', background: isHighlighted ? '#dbeafe' : 'transparent' }}
                      onMouseOver={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = '#eff6ff' }}
                      onMouseOut={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                      onClick={() => { onHighlight(props.tri_facility_id); onSelect(props.tri_facility_id, 'tri') }}
                    >
                      <td style={{ padding: '7px 10px', verticalAlign: 'top' }}>
                        <div data-testid="results-row-name" style={{ fontWeight: 600, color: '#111827', fontSize: '12px' }}>{props.name}</div>
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>{props.city}, {props.state_code}</div>
                      </td>
                      <td data-testid="results-row-release" style={{ padding: '7px 10px', textAlign: 'right', fontFamily: 'monospace', fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap', verticalAlign: 'top' }}>
                        {formatLbs(props.total_release_lbs)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {hasMoreTri && (
              <button
                type="button"
                onClick={() => setTriDisplayLimit((prev) => prev + LOAD_MORE_INCREMENT)}
                style={{ width: '100%', padding: '8px', fontSize: '12px', color: '#166534', background: '#f0fdf4', border: 'none', cursor: 'pointer', fontWeight: 500 }}
              >
                Load {Math.min(LOAD_MORE_INCREMENT, sortedTri.length - triDisplayLimit)} more ({sortedTri.length - triDisplayLimit} remaining)
              </button>
            )}
          </>
        )}

        {/* Superfund section */}
        {displayedSuperfund.length > 0 && (
          <>
            <div style={{ padding: '6px 10px', background: '#fef2f2', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#991b1b', borderBottom: '1px solid #fecaca' }}>
              Superfund Sites ({superfundCount})
            </div>
            <table className="toxmap-results-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <tbody>
                {displayedSuperfund.map((feature) => {
                  const props = feature.properties
                  const isHighlighted = props.epa_id === highlightedFacilityId
                  return (
                    <tr
                      key={props.epa_id}
                      data-testid="results-row"
                      style={{ borderBottom: '1px solid #f3f4f6', cursor: 'pointer', background: isHighlighted ? '#fee2e2' : 'transparent' }}
                      onMouseOver={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = '#fef2f2' }}
                      onMouseOut={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                      onClick={() => { onHighlight(props.epa_id); onSelect(props.epa_id, 'superfund') }}
                    >
                      <td style={{ padding: '7px 10px', verticalAlign: 'top' }}>
                        <div data-testid="results-row-name" style={{ fontWeight: 600, color: '#111827', fontSize: '12px' }}>{props.name}</div>
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>{props.city}, {props.state_code}</div>
                        <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '3px', background: '#fef2f2', color: '#ef4444', fontWeight: 600 }}>{props.status}</span>
                      </td>
                      <td data-testid="results-row-hrs" style={{ padding: '7px 10px', textAlign: 'right', fontFamily: 'monospace', fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap', verticalAlign: 'top' }}>
                        {props.hrs_score !== null ? (
                          <span style={{ color: hrsColor(props.hrs_score) }}>{props.hrs_score.toFixed(2)}</span>
                        ) : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {hasMoreSuperfund && (
              <button
                type="button"
                onClick={() => setSuperfundDisplayLimit((prev) => prev + LOAD_MORE_INCREMENT)}
                style={{ width: '100%', padding: '8px', fontSize: '12px', color: '#991b1b', background: '#fef2f2', border: 'none', cursor: 'pointer', fontWeight: 500 }}
              >
                Load {Math.min(LOAD_MORE_INCREMENT, sortedSuperfund.length - superfundDisplayLimit)} more ({sortedSuperfund.length - superfundDisplayLimit} remaining)
              </button>
            )}
          </>
        )}
      </div>
    )
  }

  // ── Superfund mode ────────────────────────────────────────────────────────
  if (mode === 'superfund') {
    if (loading && !superfundData) {
      return <p style={{ padding: '12px', fontSize: '13px', color: '#6b7280', margin: 0 }}>Searching…</p>
    }
    if (!superfundData) return <></>
    if (superfundData.features.length === 0) {
      return (
        <p style={{ padding: '12px', fontSize: '13px', color: '#6b7280', margin: 0 }}>
          No Superfund sites found in this area.
        </p>
      )
    }
    // Use pre-sorted array (memoized above)
    const displayed = sortedSuperfund.slice(0, superfundDisplayLimit)
    const hasMore = sortedSuperfund.length > superfundDisplayLimit
    return (
      <div data-testid="results-table">
        <div data-testid="results-summary" className="toxmap-results-count" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 10px', fontSize: '11px', color: '#6b7280', margin: 0, borderBottom: '1px solid #f3f4f6' }}>
          <span>{superfundData.meta.total_count} Superfund sites</span>
        </div>
        <table className="toxmap-results-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'left', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>Site</th>
              <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'right', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>HRS</th>
            </tr>
          </thead>
          <tbody>
            {displayed.map((feature) => {
              const props = feature.properties
              const isHighlighted = props.epa_id === highlightedFacilityId
              return (
                <tr
                  key={props.epa_id}
                  data-testid="results-row"
                  style={{ borderBottom: '1px solid #f3f4f6', cursor: 'pointer', background: isHighlighted ? '#fee2e2' : 'transparent' }}
                  onMouseOver={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = '#fef2f2' }}
                  onMouseOut={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                  onClick={() => {
                    onHighlight(props.epa_id)
                    onSelect(props.epa_id, 'superfund')
                  }}
                >
                  <td style={{ padding: '7px 10px', verticalAlign: 'top' }}>
                    <div data-testid="results-row-name" className="toxmap-facility-name" style={{ fontWeight: 600, color: '#111827', fontSize: '12px' }}>
                      {props.name}
                    </div>
                    <div style={{ fontSize: '11px', color: '#6b7280' }}>
                      {props.city}, {props.state_code}
                    </div>
                    <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '3px', background: '#fef2f2', color: '#ef4444', fontWeight: 600 }}>
                      {props.status}
                    </span>
                  </td>
                  <td
                    data-testid="results-row-hrs"
                    style={{ padding: '7px 10px', textAlign: 'right', fontFamily: 'monospace', fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap', verticalAlign: 'top' }}
                  >
                    {props.hrs_score !== null ? (
                      <span style={{ color: hrsColor(props.hrs_score) }}>{props.hrs_score.toFixed(2)}</span>
                    ) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {hasMore && (
          <button
            type="button"
            onClick={() => setSuperfundDisplayLimit((prev) => prev + LOAD_MORE_INCREMENT)}
            style={{ width: '100%', padding: '8px', fontSize: '12px', color: '#991b1b', background: '#fef2f2', border: 'none', cursor: 'pointer', fontWeight: 500 }}
          >
            Load {Math.min(LOAD_MORE_INCREMENT, sortedSuperfund.length - superfundDisplayLimit)} more ({sortedSuperfund.length - superfundDisplayLimit} remaining)
          </button>
        )}
      </div>
    )
  }

  // ── TRI mode (default) ────────────────────────────────────────────────────
  if (loading && !triData) {
    return <p style={{ padding: '12px', fontSize: '13px', color: '#6b7280', margin: 0 }}>Searching…</p>
  }
  if (!triData) return <></>
  if (triData.features.length === 0) {
    return (
      <p style={{ padding: '12px', fontSize: '13px', color: '#6b7280', margin: 0 }}>
        No facilities found in this area for the selected filters.
      </p>
    )
  }

  // Use pre-sorted array (memoized above)
  const displayed = sortedTri.slice(0, triDisplayLimit)
  const hasMore = sortedTri.length > triDisplayLimit

  return (
    <div data-testid="results-table">
      <div data-testid="results-summary" className="toxmap-results-count" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 10px', fontSize: '11px', color: '#6b7280', margin: 0, borderBottom: '1px solid #f3f4f6' }}>
        <span>{triData.meta.total_count} TRI facilities</span>
        {onExport && triData.features.length > 0 && (
          <button
            type="button"
            data-testid="export-csv-btn"
            onClick={onExport}
            disabled={exportLoading}
            aria-label="Download CSV"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              fontSize: '10px',
              fontWeight: 500,
              color: exportLoading ? '#9ca3af' : '#166534',
              background: '#f0fdf4',
              border: '1px solid #dcfce7',
              borderRadius: '4px',
              cursor: exportLoading ? 'not-allowed' : 'pointer',
            }}
          >
            {exportLoading ? (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" style={{ animation: 'spin 1s linear infinite' }}>
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="31.4 31.4" />
                </svg>
                <span>Exporting…</span>
              </>
            ) : (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                <span>CSV</span>
              </>
            )}
          </button>
        )}
      </div>
      <table className="toxmap-results-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
        <thead>
          <tr>
            <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'left', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>Facility</th>
            <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'right', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>Released</th>
          </tr>
        </thead>
        <tbody>
          {displayed.map((feature) => {
            const props = feature.properties
            const isHighlighted = props.tri_facility_id === highlightedFacilityId
            return (
              <tr
                key={props.tri_facility_id}
                data-testid="results-row"
                style={{ borderBottom: '1px solid #f3f4f6', cursor: 'pointer', background: isHighlighted ? '#dbeafe' : 'transparent' }}
                onMouseOver={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = '#eff6ff' }}
                onMouseOut={(e) => { if (!isHighlighted) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                onClick={() => {
                  onHighlight(props.tri_facility_id)
                  onSelect(props.tri_facility_id, 'tri')
                }}
              >
                <td style={{ padding: '7px 10px', verticalAlign: 'top' }}>
                  <div data-testid="results-row-name" className="toxmap-facility-name" style={{ fontWeight: 600, color: '#111827', fontSize: '12px' }}>
                    {props.name}
                  </div>
                  <div className="toxmap-facility-sub" style={{ fontSize: '11px', color: '#6b7280' }}>
                    {props.city}, {props.state_code}
                  </div>
                  {props.chemical_name && (
                    <div style={{ fontSize: '11px', color: '#9ca3af' }}>{props.chemical_name}</div>
                  )}
                </td>
                <td
                  data-testid="results-row-release"
                  className="toxmap-release-amount"
                  style={{ padding: '7px 10px', textAlign: 'right', fontFamily: 'monospace', fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap', verticalAlign: 'top' }}
                >
                  {formatLbs(props.total_release_lbs)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {hasMore && (
        <button
          type="button"
          onClick={() => setTriDisplayLimit((prev) => prev + LOAD_MORE_INCREMENT)}
          style={{ width: '100%', padding: '8px', fontSize: '12px', color: '#166534', background: '#f0fdf4', border: 'none', cursor: 'pointer', fontWeight: 500 }}
        >
          Load {Math.min(LOAD_MORE_INCREMENT, sortedTri.length - triDisplayLimit)} more ({sortedTri.length - triDisplayLimit} remaining)
        </button>
      )}
    </div>
  )
}, arePropsEqual)
