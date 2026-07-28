/**
 * ResultsTable — stories 3.5.1–3.5.3, 4.1.3.
 * UX Invariants: 2 (no empty rows), 8 (comma-formatted numbers).
 * Supports TRI mode (sorted by total_release_lbs) and Superfund mode (HRS score).
 */
import { formatLbs } from '../../utils/formatLbs'
import type { FacilityCollection, SuperfundCollection } from '../../api/types'

interface ResultsTableProps {
  mode: 'tri' | 'superfund'
  triData: FacilityCollection | null
  superfundData: SuperfundCollection | null
  loading: boolean
  highlightedFacilityId: string | null
  onHighlight: (id: string | null) => void
  onSelect: (id: string) => void
}

/** HRS score badge coloring (story 4.2.1): red ≥50, amber 28–50, green <28 */
function hrsColor(score: number | null): string {
  if (score === null) return '#6b7280'
  if (score >= 50) return '#ef4444'
  if (score >= 28) return '#f59e0b'
  return '#22c55e'
}

/**
 * Viewport-scoped results table.
 * UX Invariant 2: only non-empty rows rendered (no placeholders).
 */
export function ResultsTable({
  mode,
  triData,
  superfundData,
  loading,
  highlightedFacilityId,
  onHighlight,
  onSelect,
}: ResultsTableProps): JSX.Element {
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
    const sorted = [...superfundData.features].sort((a, b) => {
      const aScore = a.properties.hrs_score ?? -1
      const bScore = b.properties.hrs_score ?? -1
      return bScore - aScore
    })
    return (
      <div data-testid="results-table">
        <p className="toxmap-results-count" style={{ padding: '4px 10px', fontSize: '11px', color: '#6b7280', margin: 0, borderBottom: '1px solid #f3f4f6' }}>
          {superfundData.meta.total_count} Superfund sites found
        </p>
        <table className="toxmap-results-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'left', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>Site</th>
              <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'right', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>HRS</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((feature) => {
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
                    onSelect(props.epa_id)
                  }}
                  onMouseEnter={() => onHighlight(props.epa_id)}
                  onMouseLeave={() => onHighlight(null)}
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

  const sorted = [...triData.features].sort(
    (a, b) => (b.properties.total_release_lbs ?? 0) - (a.properties.total_release_lbs ?? 0),
  )

  return (
    <div data-testid="results-table">
      <p className="toxmap-results-count" style={{ padding: '4px 10px', fontSize: '11px', color: '#6b7280', margin: 0, borderBottom: '1px solid #f3f4f6' }}>
        {triData.meta.total_count} facilities found
      </p>
      <table className="toxmap-results-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
        <thead>
          <tr>
            <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'left', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>Facility</th>
            <th style={{ padding: '6px 10px', background: '#f9fafb', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: '#6b7280', textAlign: 'right', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>Released</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((feature) => {
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
                  onSelect(props.tri_facility_id)
                }}
                onMouseEnter={() => onHighlight(props.tri_facility_id)}
                onMouseLeave={() => onHighlight(null)}
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
    </div>
  )
}
