/**
 * FacilityDrawer — story 3.4.3, 3.4.4, 3.4.5.
 * Shows full facility detail with 3-tab Recharts: top chemicals, release by medium, 15-year trend.
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
  const { detail, loading: detailLoading } = useFacilityDetail(facilityId)
  // Fetch ALL years (1987–present) to match "Emissions estimates (all years)" label
  const { releases, loading: releasesLoading } = useFacilityReleases(facilityId, 1987, new Date().getFullYear())

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

  // Medium breakdown aggregated across all years (consistent with Top Chemicals)
  const mediumData = releases.length > 0
    ? [
        { medium: 'Air', lbs: releases.reduce((sum, r) => sum + (r.air_release_lbs ?? 0), 0) },
        { medium: 'Water', lbs: releases.reduce((sum, r) => sum + (r.water_release_lbs ?? 0), 0) },
        { medium: 'Land', lbs: releases.reduce((sum, r) => sum + (r.land_release_lbs ?? 0), 0) },
        { medium: 'Underground', lbs: releases.reduce((sum, r) => sum + (r.underground_release_lbs ?? 0), 0) },
        { medium: 'Off-site', lbs: releases.reduce((sum, r) => sum + (r.off_site_lbs ?? 0), 0) },
      ].filter((d) => d.lbs > 0)
    : []

  // 15-year trend data — aggregate all chemicals per year, fill missing years with zeros
  // Range is relative to selected year filter, or current year if no filter
  const trendReferenceYear = selectedYear && /^\d{4}$/.test(selectedYear)
    ? parseInt(selectedYear, 10)
    : new Date().getFullYear()
  const trendStartYear = trendReferenceYear - 14 // 15 years total

  const trendData = (() => {
    // Aggregate all chemicals per year (sum total_release_lbs across all chemicals)
    const dataByYear = new Map<number, number>()
    for (const r of releases) {
      const currentTotal = dataByYear.get(r.reporting_year) ?? 0
      dataByYear.set(r.reporting_year, currentTotal + (r.total_release_lbs ?? 0))
    }

    // Generate full 15-year range ending at reference year
    const fullRange: { year: number; lbs: number }[] = []
    for (let y = trendStartYear; y <= trendReferenceYear; y++) {
      fullRange.push({ year: y, lbs: dataByYear.get(y) ?? 0 })
    }
    return fullRange
  })()

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
                <p className="toxmap-drawer-subtitle" style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px', margin: '2px 0 0' }}>
                  {detail.address}, {detail.city}, {detail.state_code}
                </p>
              )}
            </>
          )}
        </div>
        <button
          data-testid="popup-close-bottom"
          type="button"
          onClick={onClose}
          className="toxmap-drawer-close"
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', color: '#9ca3af', padding: 0, lineHeight: 1, flexShrink: 0 }}
          aria-label="Close facility detail"
        >
          ✕
        </button>
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
          { id: 'trend', testid: 'facility-chart-tab-3', label: '15-Year Trend' },
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

        {/* Tab 1: Top chemicals — matches Fig 11 (2006): shows "Release Amount (lbs./all years)", %, and TOTAL */}
        {!detailLoading && activeTab === 'chemicals' && detail && (
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              Emissions estimates (all years)
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
                            Release Amount<br /><span style={{ fontWeight: 400 }}>(lbs./all years)</span>
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
              Release by medium (lbs./all years)
            </h3>
            {mediumData.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No medium breakdown available.</p>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={mediumData}>
                  <XAxis dataKey="medium" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)) + ' lbs', 'Released']} />
                  <Bar dataKey="lbs" fill="#f97316" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        {/* Tab 3: 15-year trend */}
        {!releasesLoading && activeTab === 'trend' && (
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              15-year release trend ({trendStartYear}–{trendReferenceYear})
            </h3>
            {trendData.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No trend data available.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    labelFormatter={(year) => `Reporting Year: ${year}`}
                    formatter={(v) => [formatNumber(Number(v ?? 0)) + ' lbs', 'Total release']}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="lbs" stroke="#3b82f6" dot={true} name="Total release (lbs)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </div>

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
