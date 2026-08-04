/**
 * FacilityDrawer — story 3.4.3, 3.4.4, 3.4.5.
 * Shows full facility detail with 3-tab Recharts: top chemicals, release by medium, 15-year trend.
 * UX Invariants: 8 (comma numbers), T-08 (ATSDR link opens new tab, preserves map state).
 */
import { useState, useEffect } from 'react'
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
}

/** Fixed right-side drawer showing full facility detail with Recharts tabs. */
export function FacilityDrawer({ facilityId, onClose }: FacilityDrawerProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('chemicals')
  const { detail, loading: detailLoading } = useFacilityDetail(facilityId)
  const { releases, loading: releasesLoading } = useFacilityReleases(facilityId)

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

  // Medium breakdown from most-recent year's releases
  const latestRelease = releases.length > 0
    ? releases.reduce((a, b) => (b.reporting_year > a.reporting_year ? b : a))
    : null

  const mediumData = latestRelease
    ? [
        { medium: 'Air', lbs: latestRelease.air_release_lbs ?? 0 },
        { medium: 'Water', lbs: latestRelease.water_release_lbs ?? 0 },
        { medium: 'Land', lbs: latestRelease.land_release_lbs ?? 0 },
        { medium: 'Underground', lbs: latestRelease.underground_release_lbs ?? 0 },
      ].filter((d) => d.lbs > 0)
    : []

  // 15-year trend data
  const trendData = [...releases]
    .sort((a, b) => a.reporting_year - b.reporting_year)
    .map((r) => ({ year: r.reporting_year, lbs: r.total_release_lbs ?? 0 }))

  return (
    <div
      data-testid="facility-detail-panel"
      className="toxmap-drawer"
      style={{ position: 'absolute', right: 0, top: 0, height: '100%', width: '380px', maxWidth: '90vw', zIndex: 40, background: '#fff', borderLeft: '1px solid #e5e7eb', boxShadow: '-4px 0 16px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', fontFamily: 'system-ui, sans-serif' }}
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

        {/* Tab 1: Top chemicals */}
        {!detailLoading && activeTab === 'chemicals' && detail && (
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              Top chemicals by release amount
            </h3>
            {detail.top_chemicals.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No chemical data available.</p>
            ) : (
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
                  <tbody>
                    {detail.top_chemicals.map((c) => {
                      const chem = chemicalData.get(c.chemical_name.toUpperCase())
                      return (
                        <tr key={c.chemical_name} style={{ borderBottom: '1px solid #f3f4f6' }}>
                          <td style={{ padding: '4px 0' }}>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', flexWrap: 'wrap' }}>
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
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </>
            )}
          </div>
        )}

        {/* Tab 2: Release by medium */}
        {!releasesLoading && activeTab === 'medium' && (
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
              Release by medium (most recent year)
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
              15-year release trend
            </h3>
            {trendData.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>No trend data available.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)) + ' lbs', 'Total release']} />
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
    </div>
  )
}
