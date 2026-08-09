/**
 * FacilityDrawer — story 3.4.3, 3.4.4, 3.4.5.
 * Shows full facility detail with 3-tab Recharts: top chemicals, release by medium, release trend.
 * Trend tab displays up to 15 years, clamped to 1987 (first TRI reporting year) to avoid misleading zeros.
 * UX Invariants: 8 (comma numbers), T-08 (ATSDR link opens new tab, preserves map state).
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from 'recharts'
import { useFacilityDetail } from '../../hooks/useFacilityDetail'
import { useFacilityReleases } from '../../hooks/useFacilityReleases'
import { searchChemicals } from '../../api/chemicals'
import { exportSingleFacilityCsv } from '../../api/export'
import { formatLbs, formatNumber } from '../../utils/formatLbs'
import type { Chemical } from '../../api/types'

type Tab = 'chemicals' | 'medium' | 'trend'

interface FacilityDrawerProps {
  facilityId: string
  onClose: () => void
  /** Selected year from search filter. If empty/null, defaults to current year. */
  selectedYear?: string | null
  /** Current drawer width in pixels (controlled by parent) */
  width?: number
  /** Callback when user drags to resize drawer */
  onWidthChange?: (width: number) => void
}

/** Fixed right-side drawer showing full facility detail with Recharts tabs. */
export function FacilityDrawer({ facilityId, onClose, selectedYear, width = 420, onWidthChange }: FacilityDrawerProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('chemicals')
  
  // Parse selectedYear for API calls (null = all years)
  const yearFilter = selectedYear && /^\d{4}$/.test(selectedYear) ? parseInt(selectedYear, 10) : null
  
  // Fetch facility detail with year filter
  const { detail, loading: detailLoading } = useFacilityDetail(facilityId, yearFilter)
  
  // Fetch releases for trend chart — if year filter is set, end at that year; otherwise use current year
  const trendEndYear = yearFilter ?? new Date().getFullYear()
  // TRI reporting began in 1987 — clamp start year to avoid showing misleading zeros for years that didn't exist
  const TRI_FIRST_YEAR = 1987
  const trendStartYear = Math.max(TRI_FIRST_YEAR, trendEndYear - 14)
  const trendYearsAvailable = trendEndYear - trendStartYear + 1
  const { releases, loading: releasesLoading } = useFacilityReleases(facilityId, trendStartYear, trendEndYear)

  // Export state (story 6.EXPORT.5–6)
  const [exportLoading, setExportLoading] = useState(false)
  
  const handleExport = useCallback(async () => {
    if (!facilityId) return
    setExportLoading(true)
    try {
      await exportSingleFacilityCsv(facilityId)
    } catch (err) {
      console.error('Export failed:', err)
      window.alert('Export failed. Please try again.')
    } finally {
      setExportLoading(false)
    }
  }, [facilityId])

  // Ref for direct DOM manipulation during resize (avoids React re-render lag)
  const drawerRef = useRef<HTMLDivElement>(null)
  const [isResizing, setIsResizing] = useState(false)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsResizing(true)

    const startX = e.clientX
    const startWidth = width
    const drawer = drawerRef.current

    // Disable text selection and transitions during drag
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
    if (drawer) {
      drawer.style.transition = 'none'
    }

    const handleMouseMove = (moveEvent: MouseEvent) => {
      moveEvent.preventDefault()
      moveEvent.stopPropagation()
      // Dragging left (negative delta) should increase width for right-side drawer
      const delta = startX - moveEvent.clientX
      const newWidth = Math.min(800, Math.max(320, startWidth + delta))
      // Direct DOM update for smooth dragging (no React state during drag)
      if (drawer) {
        drawer.style.width = `${newWidth}px`
      }
    }

    const handleMouseUp = (upEvent: MouseEvent) => {
      upEvent.preventDefault()
      upEvent.stopPropagation()

      // Restore normal behavior
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
      if (drawer) {
        drawer.style.transition = ''
      }

      // Commit final width to React state
      if (drawer && onWidthChange) {
        const finalWidth = parseInt(drawer.style.width, 10)
        if (!isNaN(finalWidth)) {
          onWidthChange(finalWidth)
        }
      }

      setIsResizing(false)
      document.removeEventListener('mousemove', handleMouseMove, true)
      document.removeEventListener('mouseup', handleMouseUp, true)
    }

    // Use capture phase to intercept events before map receives them
    document.addEventListener('mousemove', handleMouseMove, true)
    document.addEventListener('mouseup', handleMouseUp, true)
  }, [width, onWidthChange])

  // Look up per-chemical URLs for all top chemicals.
  // The FacilityDetail schema only returns chemical_name + release amount; URLs
  // live in the chemicals table and are fetched via searchChemicals.
  const [chemicalData, setChemicalData] = useState<Map<string, Chemical>>(new Map())
  useEffect(() => {
    const names = detail?.top_chemicals?.map((c) => c.chemical_name) ?? []
    if (names.length === 0) return
    setChemicalData(new Map())
    // Fetch each chemical's data in parallel
    Promise.all(
      names.map((name) =>
        searchChemicals(name).then((results) => {
          const match = results.find((r) => r.name.toUpperCase() === name.toUpperCase())
          return match ? [name.toUpperCase(), match] as const : null
        }).catch(() => null)
      )
    ).then((results) => {
      const map = new Map<string, Chemical>()
      for (const r of results) {
        if (r) map.set(r[0], r[1])
      }
      setChemicalData(map)
    })
  }, [detail])

  // Medium breakdown: filtered to selected year if set, otherwise all years from trend range
  // This ensures "By Medium" shows data consistent with "Top Chemicals" tab
  const filteredReleases = yearFilter 
    ? releases.filter((r) => r.reporting_year === yearFilter)
    : releases
  
  const mediumData = filteredReleases.length > 0
    ? [
        { medium: 'Air', lbs: filteredReleases.reduce((sum, r) => sum + (r.air_release_lbs ?? 0), 0) },
        { medium: 'Water', lbs: filteredReleases.reduce((sum, r) => sum + (r.water_release_lbs ?? 0), 0) },
        { medium: 'Land', lbs: filteredReleases.reduce((sum, r) => sum + (r.land_release_lbs ?? 0), 0) },
        { medium: 'Underground', lbs: filteredReleases.reduce((sum, r) => sum + (r.underground_release_lbs ?? 0), 0) },
        { medium: 'Off-site', lbs: filteredReleases.reduce((sum, r) => sum + (r.off_site_lbs ?? 0), 0) },
      ].filter((d) => d.lbs > 0)
    : []

  // Sum of medium breakdowns for discrepancy calculation (EPA data quality issue)
  const mediumSum = mediumData.reduce((sum, d) => sum + d.lbs, 0)

  // Release trend data — aggregate all chemicals per year, fill missing years with zeros
  // Uses trendStartYear and trendEndYear computed above based on selectedYear filter

  // Per-year discrepancy data structure for trend chart (Option A: per-year discrepancy in Trend tab)
  // Note: null values indicate "no report filed" — semantically different from 0 ("reported zero releases")
  interface YearData {
    year: number
    lbs: number | null       // EPA-reported total (Field 65 + Field 88); null = no data
    mediumSum: number | null // Sum of air + water + land + underground + off-site; null = no data
    discrepancy: number      // mediumSum - epaTotal (positive = mediums exceed EPA total); 0 if no data
    discrepancyPct: number   // Absolute discrepancy as percentage of EPA total; 0 if no data
    hasData: boolean         // True if this year has actual reported data
  }

  const trendData = (() => {
    // Aggregate all chemicals per year with both EPA total and medium breakdown
    const dataByYear = new Map<number, { epaTotal: number; mediumSum: number }>()
    for (const r of releases) {
      const current = dataByYear.get(r.reporting_year) ?? { epaTotal: 0, mediumSum: 0 }
      // EPA total = Field 65 (on-site total from EPA) + Field 88 (off-site)
      const epaTotal = (r.total_release_lbs ?? 0) + (r.off_site_lbs ?? 0)
      // Medium sum = individual medium breakdowns (air, water, land, underground are on-site; off-site separate)
      const mediumSum = (r.air_release_lbs ?? 0) + (r.water_release_lbs ?? 0) + 
                        (r.land_release_lbs ?? 0) + (r.underground_release_lbs ?? 0) + 
                        (r.off_site_lbs ?? 0)
      dataByYear.set(r.reporting_year, {
        epaTotal: current.epaTotal + epaTotal,
        mediumSum: current.mediumSum + mediumSum,
      })
    }

    // Generate full year range ending at selected year (or current year), clamped to 1987
    // Missing years use null (not 0) — semantically different: null = "no report", 0 = "reported zero"
    const fullRange: YearData[] = []
    for (let y = trendStartYear; y <= trendEndYear; y++) {
      const yearData = dataByYear.get(y)
      const hasData = yearData !== undefined
      if (hasData) {
        const epaTotal = yearData.epaTotal
        const mediumSum = yearData.mediumSum
        const discrepancy = mediumSum - epaTotal
        const discrepancyPct = epaTotal > 0 ? (Math.abs(discrepancy) / epaTotal) * 100 : 0
        fullRange.push({ year: y, lbs: epaTotal, mediumSum, discrepancy, discrepancyPct, hasData: true })
      } else {
        // No data for this year — use null to create gap in line chart
        fullRange.push({ year: y, lbs: null, mediumSum: null, discrepancy: 0, discrepancyPct: 0, hasData: false })
      }
    }
    return fullRange
  })()

  // Count years with actual data vs gaps
  const yearsWithData = trendData.filter(d => d.hasData).length
  const yearsWithGaps = trendData.length - yearsWithData

  // Check if ANY year has a significant discrepancy (≥5%) - used to warn even when aggregate is minimal
  const hasYearWithHighDiscrepancy = trendData.some(d => d.hasData && d.discrepancyPct >= 5 && (d.lbs ?? 0) > 0)

  return (
    <div
      ref={drawerRef}
      data-testid="facility-detail-panel"
      className="toxmap-drawer"
      style={{
        position: 'absolute',
        right: 0,
        top: 0,
        height: '100%',
        width: `${width}px`,
        maxWidth: '90vw',
        zIndex: 40,
        background: '#fff',
        borderLeft: '1px solid #e5e7eb',
        boxShadow: '-4px 0 16px rgba(0,0,0,0.1)',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'system-ui, sans-serif',
        transition: isResizing ? 'none' : 'width 250ms ease',
      }}
    >
      {/* Header */}
      <div className="toxmap-drawer-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '14px 16px', borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
        <div style={{ flex: 1, paddingRight: '8px' }}>
          {detailLoading ? (
            <div style={{ height: '18px', width: '180px', background: '#e5e7eb', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
          ) : (
            <>
              <p className="toxmap-drawer-title" style={{ fontSize: '14px', fontWeight: 700, color: '#111827', lineHeight: 1.3, margin: 0 }}>
                {detail?.name ?? facilityId}
              </p>
              {detail && (
                <>
                  <p style={{ margin: '4px 0 0', fontSize: '11px', color: '#6b7280', fontFamily: 'monospace' }}>
                    TRI ID:{' '}
                    <a
                      href={`https://enviro.epa.gov/facts/tri/ef-facilities/#/Facility/${detail.tri_facility_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#2563eb', textDecoration: 'none' }}
                      data-testid="facility-tri-id-link"
                    >
                      {detail.tri_facility_id}
                    </a>
                  </p>
                  <p className="toxmap-drawer-subtitle" style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px', margin: '2px 0 0' }}>
                    {detail.address}, {detail.city}, {detail.state_code}
                  </p>
                </>
              )}
            </>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flexShrink: 0 }}>
          <button
            data-testid="facility-export-btn"
            type="button"
            onClick={handleExport}
            disabled={exportLoading || !detail}
            className="toxmap-drawer-export"
            style={{
              background: exportLoading ? '#e5e7eb' : '#f0fdf4',
              border: '1px solid #dcfce7',
              borderRadius: '4px',
              cursor: exportLoading || !detail ? 'not-allowed' : 'pointer',
              fontSize: '11px',
              color: exportLoading ? '#9ca3af' : '#166534',
              padding: '4px 8px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 500,
            }}
            aria-label="Export facility data"
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
                <span>Export</span>
              </>
            )}
          </button>
          <button
            data-testid="popup-close-bottom"
            type="button"
            onClick={onClose}
            className="toxmap-drawer-close"
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', color: '#9ca3af', padding: 0, lineHeight: 1 }}
            aria-label="Close facility detail"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Note about chemical links */}
      {chemicalData.size > 0 && (
        <div className="toxmap-drawer-links" style={{ padding: '6px 16px', borderBottom: '1px solid #f3f4f6', flexShrink: 0 }}>
          <p style={{ margin: 0, fontSize: '10px', color: '#6b7280' }}>
            Chemical names link to PubChem. ToxFAQs™ links (if available) provide ATSDR health info.
          </p>
        </div>
      )}

      {/* Tab bar */}
      <div className="toxmap-drawer-tab-bar" style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
        {([
          { id: 'chemicals', testid: 'facility-chart-tab-1', label: 'Top Chemicals' },
          { id: 'medium', testid: 'facility-chart-tab-2', label: 'By Medium' },
          { id: 'trend', testid: 'facility-chart-tab-3', label: 'Release Trend' },
        ] as { id: Tab; testid: string; label: string }[]).map(({ id, testid, label }) => (
          <button
            key={id}
            data-testid={testid}
            type="button"
            onClick={() => setActiveTab(id)}
            className={`toxmap-drawer-tab${activeTab === id ? ' active' : ''}`}
            style={{ flex: 1, padding: '8px 4px', fontSize: '11px', fontWeight: 500, background: 'none', border: 'none', borderBottom: activeTab === id ? '2px solid #2563eb' : '2px solid transparent', cursor: 'pointer', color: activeTab === id ? '#1d4ed8' : '#6b7280', fontFamily: 'inherit' }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Chart content */}
      <div className="toxmap-drawer-body" style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {(detailLoading || releasesLoading) && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontSize: '13px', color: '#9ca3af' }}>
            Loading…
          </div>
        )}

        {/* Tab 1: Top chemicals — matches Fig 11 (2006): shows "Release Amount (lbs.)" with year context */}
        {!detailLoading && activeTab === 'chemicals' && detail && (
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              Emissions estimates {yearFilter ? `(${yearFilter})` : '(all years)'}
            </h3>
            {detail.top_chemicals.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No chemical data available.</p>
            ) : (
              (() => {
                // 7.BUG.29: Use API-provided total (all chemicals, all years) for TOTAL row
                const facilityTotal = detail.total_release_lbs ?? 0
                // Sum of top 5 chemicals displayed
                const sumTop5 = detail.top_chemicals.reduce((sum, c) => sum + (c.total_release_lbs ?? 0), 0)
                // "Other chemicals" = facility total minus top 5
                const otherChemicals = Math.max(0, facilityTotal - sumTop5)
                // Use facility total for percentage calculations (per Fig 11)
                const percentBase = facilityTotal > 0 ? facilityTotal : sumTop5
                return (
                  <>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart
                        data={detail.top_chemicals.map((c) => ({
                          name: c.chemical_name.length > 14 ? c.chemical_name.slice(0, 14) + '…' : c.chemical_name,
                          lbs: c.total_release_lbs,
                        }))}
                        layout="vertical"
                      >
                        <XAxis type="number" tick={{ fontSize: 10 }} />
                        <YAxis dataKey="name" type="category" width={110} tick={{ fontSize: 10 }} />
                        <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)) + ' lbs', 'Released']} />
                        <Bar dataKey="lbs" fill="#3b82f6" />
                      </BarChart>
                    </ResponsiveContainer>
                    <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse', marginTop: '12px' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                          <th style={{ padding: '6px 0', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: '#374151' }}>
                            Chemical
                          </th>
                          <th data-testid="top-chemicals-amount-header" style={{ padding: '6px 0', textAlign: 'right', fontSize: '11px', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>
                            Release Amount<br /><span style={{ fontWeight: 400 }}>(lbs./{yearFilter ?? 'all years'})</span>
                          </th>
                          <th style={{ padding: '6px 0', textAlign: 'right', fontSize: '11px', fontWeight: 600, color: '#374151', width: '50px' }}>
                            %
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.top_chemicals.map((c, idx) => {
                          const chem = chemicalData.get(c.chemical_name.toUpperCase())
                          const pct = percentBase > 0 ? ((c.total_release_lbs ?? 0) / percentBase) * 100 : 0
                          return (
                            <tr key={c.chemical_name} style={{ borderBottom: '1px solid #f3f4f6' }}>
                              <td style={{ padding: '4px 0' }}>
                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', flexWrap: 'wrap' }}>
                                  {/* Numbered rank per Fig 11 */}
                                  <span style={{ color: '#6b7280', fontWeight: 700, minWidth: '16px' }}>{idx + 1})</span>
                                  {/* Chemical name — link to PubChem if available */}
                                  {chem?.pubchem_url ? (
                                    <a
                                      data-testid="facility-chemical-pubchem"
                                      href={chem.pubchem_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                                    >
                                      {c.chemical_name}
                                    </a>
                                  ) : (
                                    <span style={{ color: '#374151', fontWeight: 500 }}>{c.chemical_name}</span>
                                  )}
                                  {/* ToxFAQs™ link if available */}
                                  {chem?.atsdr_url && (
                                    <a
                                      data-testid="facility-chemical-toxfaqs"
                                      href={chem.atsdr_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{ fontSize: '10px', color: '#059669', textDecoration: 'none' }}
                                    >
                                      ToxFAQs™
                                    </a>
                                  )}
                                </div>
                              </td>
                              <td
                                data-testid="facility-release-amount"
                                style={{ padding: '4px 0', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700 }}
                              >
                                {formatLbs(c.total_release_lbs)}
                              </td>
                              <td style={{ padding: '4px 0', textAlign: 'right', fontFamily: 'monospace', color: '#6b7280' }}>
                                {pct.toFixed(1)}%
                              </td>
                            </tr>
                          )
                        })}
                        {/* "Other chemicals" row per Fig 11 — shown if there are chemicals beyond top 5 */}
                        {otherChemicals > 0 && (
                          <tr style={{ borderBottom: '1px solid #f3f4f6' }}>
                            <td style={{ padding: '4px 0' }}>
                              <span style={{ color: '#6b7280', fontStyle: 'italic' }}>Other chemicals</span>
                            </td>
                            <td style={{ padding: '4px 0', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700 }}>
                              {formatLbs(otherChemicals)}
                            </td>
                            <td style={{ padding: '4px 0', textAlign: 'right', fontFamily: 'monospace', color: '#6b7280' }}>
                              {percentBase > 0 ? ((otherChemicals / percentBase) * 100).toFixed(1) : 0}%
                            </td>
                          </tr>
                        )}
                      </tbody>
                      {/* TOTAL row per Fig 11 — uses facility total, not just sum of top 5 */}
                      <tfoot>
                        <tr style={{ borderTop: '2px solid #e5e7eb', background: '#f9fafb' }}>
                          <td style={{ padding: '6px 0', fontWeight: 700, color: '#111827' }}>
                            TOTAL
                          </td>
                          <td
                            data-testid="facility-release-total"
                            style={{ padding: '6px 0', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, color: '#111827' }}
                          >
                            {formatLbs(facilityTotal)}
                          </td>
                          <td style={{ padding: '6px 0', textAlign: 'right', fontFamily: 'monospace', color: '#6b7280' }}>
                            {/* Percentages may not sum to 100 due to rounding */}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                    <p style={{ marginTop: '8px', fontSize: '10px', color: '#9ca3af', fontStyle: 'italic' }}>
                      *Percents may not add to 100 because of rounding.
                    </p>
                  </>
                )
              })()
            )}
          </div>
        )}

        {/* Tab 2: Release by medium */}
        {!releasesLoading && activeTab === 'medium' && (
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              Release by medium (lbs./{yearFilter ?? 'all years'})
            </h3>
            {mediumData.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No medium breakdown available.</p>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={mediumData}>
                    <XAxis dataKey="medium" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)) + ' lbs', 'Released']} />
                    <Bar dataKey="lbs" fill="#f97316" />
                  </BarChart>
                </ResponsiveContainer>
                {/* EPA total and discrepancy display */}
                {detail && (
                  <div data-testid="medium-discrepancy-section" style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#374151' }}>EPA-Reported Total:</span>
                      <span data-testid="medium-epa-total" style={{ fontSize: '13px', fontWeight: 700, color: '#111827' }}>
                        {formatLbs(detail.total_release_lbs)}
                      </span>
                    </div>
                    {(() => {
                      const epaTotal = detail.total_release_lbs ?? 0
                      const discrepancy = mediumSum - epaTotal
                      const discrepancyAbs = Math.abs(discrepancy)
                      const discrepancyPct = epaTotal > 0 ? (discrepancyAbs / epaTotal) * 100 : 0
                      const hasDiscrepancy = discrepancyAbs >= 1
                      return (
                        <>
                          {hasDiscrepancy && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                          <span style={{ fontSize: '12px', color: '#6b7280' }}>Aggregate Discrepancy {yearFilter ? `(${yearFilter})` : '(all years)'}:</span>
                              <span data-testid="medium-discrepancy-value" style={{ fontSize: '12px', fontWeight: 600, color: discrepancy >= 0 ? '#059669' : '#dc2626' }}>
                                {discrepancy >= 0 ? '+' : '−'}{formatNumber(discrepancyAbs)} lbs ({discrepancyPct.toFixed(1)}%)
                              </span>
                            </div>
                          )}
                          <p data-testid="medium-discrepancy-footnote" style={{ margin: '8px 0 0', fontSize: '10px', lineHeight: '1.4', color: '#6b7280' }}>
                            {hasDiscrepancy ? (
                              yearFilter ? (
                                // Single year selected — simpler note
                                <>
                                  <strong>Note:</strong> This discrepancy exists because the EPA&apos;s on-site total (Field 65) does not always equal
                                  the sum of individual mediums due to facility self-reporting errors, data amendments, or Form A certifications.
                                  <a 
                                    href="https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality" 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    style={{ color: '#2563eb', marginLeft: '4px' }}
                                  >
                                    Learn more about TRI data quality →
                                  </a>
                                </>
                              ) : (
                                // All years — mention year-over-year cancellation
                                <>
                                  <strong>Note:</strong> This aggregate discrepancy is calculated across all reporting years. Positive and negative 
                                  year-over-year discrepancies may cancel out — <strong>see the Release Trend tab for per-year discrepancy details</strong>. 
                                  The EPA total combines on-site releases (air, water, land, underground) with off-site transfers. While off-site 
                                  values are consistent, the EPA&apos;s on-site total does not always equal the sum of individual mediums due to 
                                  facility self-reporting errors, data amendments, or Form A certifications where detailed breakdowns are not required. 
                                  <a 
                                    href="https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality" 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    style={{ color: '#2563eb', marginLeft: '4px' }}
                                  >
                                    Learn more about TRI data quality →
                                  </a>
                                </>
                              )
                            ) : hasYearWithHighDiscrepancy && !yearFilter ? (
                              <>
                                <strong>Note:</strong> While the aggregate discrepancy is minimal, <strong>some individual years show ≥5% discrepancies</strong> that 
                                cancel out — see the Release Trend tab for per-year details. The EPA&apos;s on-site total does not always equal the sum of 
                                individual mediums due to facility self-reporting errors, data amendments, or Form A certifications. 
                                <a 
                                  href="https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality" 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  style={{ color: '#2563eb', marginLeft: '4px' }}
                                >
                                  Learn more about TRI data quality →
                                </a>
                              </>
                            ) : (
                              <>
                                <strong>Note:</strong> The EPA total combines on-site releases (air, water, land, underground) with off-site 
                                transfers. {!yearFilter && 'See the Release Trend tab for year-by-year release data. '}
                                <a 
                                  href="https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality" 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  style={{ color: '#2563eb', marginLeft: '4px' }}
                                >
                                  Learn more about TRI data quality →
                                </a>
                              </>
                            )}
                          </p>
                        </>
                      )
                    })()}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Tab 3: Release trend (dynamic range, clamped to TRI start year 1987) */}
        {!releasesLoading && activeTab === 'trend' && (
          <div>
            <h3 style={{ margin: '0 0 4px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              Release Trend
            </h3>
            <p data-testid="trend-range-subtitle" style={{ margin: '0 0 12px', fontSize: '11px', color: '#6b7280' }}>
              {trendStartYear}–{trendEndYear}
              {trendYearsAvailable < 15 && (
                <span style={{ marginLeft: '6px', color: '#9ca3af' }}>({trendYearsAvailable} {trendYearsAvailable === 1 ? 'year' : 'years'} available — TRI reporting began 1987)</span>
              )}
            </p>
            {trendData.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No trend data available.</p>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip
                      labelFormatter={(year) => `Reporting Year: ${year}`}
                      content={({ active, payload, label }) => {
                        if (!active || !payload || !payload.length) return null
                        const data = payload[0].payload as typeof trendData[0]
                        // Check if this year has actual data (not a gap)
                        if (!data.hasData) {
                          return (
                            <div data-testid="trend-tooltip" style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '4px', padding: '8px 10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                              <p style={{ margin: 0, fontSize: '11px', fontWeight: 600, color: '#374151' }}>
                                Reporting Year: {label}
                              </p>
                              <p style={{ margin: '4px 0 0', fontSize: '11px', color: '#9ca3af', fontStyle: 'italic' }}>
                                No TRI report filed this year
                              </p>
                            </div>
                          )
                        }
                        const hasNonZeroData = (data.lbs ?? 0) > 0 || (data.mediumSum ?? 0) > 0
                        return (
                          <div data-testid="trend-tooltip" style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '4px', padding: '8px 10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                            <p style={{ margin: 0, fontSize: '11px', fontWeight: 600, color: '#374151' }}>
                              Reporting Year: {label}
                            </p>
                            <p style={{ margin: '4px 0 0', fontSize: '11px', color: '#111827' }}>
                              EPA Total: {formatNumber(data.lbs ?? 0)} lbs
                            </p>
                            {hasNonZeroData && (
                              <>
                                <p style={{ margin: '2px 0 0', fontSize: '10px', color: '#6b7280' }}>
                                  Medium Sum: {formatNumber(data.mediumSum ?? 0)} lbs
                                </p>
                                <p data-testid="trend-tooltip-discrepancy" style={{ margin: '2px 0 0', fontSize: '10px', fontWeight: 600, color: Math.abs(data.discrepancy) < 1 ? '#059669' : (data.discrepancy >= 0 ? '#059669' : '#dc2626') }}>
                                  Discrepancy: {data.discrepancy >= 0 ? '+' : '−'}{formatNumber(Math.abs(data.discrepancy))} lbs ({data.discrepancyPct.toFixed(1)}%)
                                </p>
                              </>
                            )}
                          </div>
                        )
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="lbs" 
                      stroke="#3b82f6"
                      connectNulls={false}  // Break line at missing years (don't interpolate)
                      dot={(props) => {
                        const { cx, cy, payload } = props
                        // Skip dot rendering for years with no data (null values)
                        if (!payload?.hasData || cx === undefined || cy === undefined) {
                          return <g key={`dot-${payload?.year}`} />
                        }
                        const hasHighDiscrepancy = payload && Math.abs(payload.discrepancy) >= 1 && payload.discrepancyPct >= 5
                        // Red ring around dots with ≥5% discrepancy to draw attention
                        return (
                          <g key={`dot-${payload?.year}`}>
                            {hasHighDiscrepancy && (
                              <circle cx={cx} cy={cy} r={6} fill="none" stroke="#dc2626" strokeWidth={2} opacity={0.6} />
                            )}
                            <circle cx={cx} cy={cy} r={3} fill="#3b82f6" stroke="#fff" strokeWidth={1} />
                          </g>
                        )
                      }}
                      name="Total release (lbs)" 
                    />
                  </LineChart>
                </ResponsiveContainer>
                {/* Per-year discrepancy legend — footnote style */}
                <div data-testid="trend-discrepancy-legend" style={{ marginTop: '8px', fontSize: '10px', color: '#6b7280', lineHeight: 1.8 }}>
                  <div>
                    <sup style={{ fontWeight: 600, marginRight: '4px' }}>1</sup>
                    Hover for per-year details
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <sup style={{ fontWeight: 600, marginRight: '4px' }}>2</sup>
                    <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', border: '2px solid #dc2626', opacity: 0.6, marginRight: '4px' }}></span>
                    Year with ≥5% data discrepancy
                  </div>
                  {yearsWithGaps > 0 && (
                    <div style={{ fontStyle: 'italic' }}>
                      <sup style={{ fontWeight: 600, marginRight: '4px' }}>3</sup>
                      Gap in line = no TRI report filed (missing {yearsWithGaps} {yearsWithGaps === 1 ? 'year' : 'years'})
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* EPA TRI Facility Report link — mirrors Superfund's EPA Site Progress Profile link */}
      {detail && (
        <div style={{ flexShrink: 0, borderTop: '1px solid #e5e7eb', padding: '12px 16px' }}>
          <a
            data-testid="facility-epa-report-link"
            href={`https://enviro.epa.gov/facts/tri/ef-facilities/#/Facility/${detail.tri_facility_id}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: '13px', color: '#2563eb', display: 'flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}
          >
            EPA TRI Facility Report ↗
          </a>
        </div>
      )}

      {/* Close link at bottom (UX Invariant 9) */}
      <div className="toxmap-drawer-footer" style={{ flexShrink: 0, borderTop: '1px solid #e5e7eb', padding: '10px', textAlign: 'center' }}>
        <button
          data-testid="popup-close-bottom"
          type="button"
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '11px', color: '#9ca3af', fontFamily: 'inherit' }}
        >
          Close panel
        </button>
      </div>

      {/* Resize handle — drag to adjust drawer width (7.BUG.30) */}
      <div
        data-testid="facility-drawer-resize-handle"
        onMouseDown={handleMouseDown}
        style={{
          position: 'absolute',
          top: 0,
          left: -3, // Extend slightly outside for easier grabbing (left side for right drawer)
          width: '8px',
          height: '100%',
          cursor: 'col-resize',
          background: isResizing ? '#3b82f6' : 'transparent',
          zIndex: 50, // Above everything
        }}
        onMouseEnter={(e) => { if (!isResizing) (e.currentTarget as HTMLElement).style.background = 'rgba(59, 130, 246, 0.3)' }}
        onMouseLeave={(e) => { if (!isResizing) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
      />
    </div>
  )
}
