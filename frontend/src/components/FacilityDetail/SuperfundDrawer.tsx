/**
 * SuperfundDrawer — Superfund site detail panel (stories 4.2.1, 4.2.2, 4.2.3).
 * UX Invariant 9 (close at bottom) — popup-close-bottom shared testid.
 *
 * Opened when the user clicks a Superfund diamond on the map or a row in
 * the Superfund results table.
 */
import { useSuperfundDetail } from '../../hooks/useSuperfundDetail'
import type { SuperfundDetail } from '../../api/types'

/** HRS score badge coloring: red ≥50, amber 28–50, green <28 */
function hrsBadgeStyle(score: number | null): React.CSSProperties {
  let bg = '#e5e7eb'
  let color = '#374151'
  if (score !== null) {
    if (score >= 50) { bg = '#fee2e2'; color = '#ef4444' }
    else if (score >= 28) { bg = '#fef3c7'; color = '#d97706' }
    else { bg = '#dcfce7'; color = '#16a34a' }
  }
  return { background: bg, color, padding: '3px 10px', borderRadius: '999px', fontSize: '13px', fontWeight: 700, display: 'inline-block' }
}

interface SuperfundDrawerProps {
  epaId: string
  onClose: () => void
}

/** Full Superfund site detail drawer. */
export function SuperfundDrawer({ epaId, onClose }: SuperfundDrawerProps): JSX.Element {
  const { data, loading, error } = useSuperfundDetail(epaId)

  return (
    <div
      data-testid="superfund-detail-panel"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '340px',
        height: '100vh',
        background: '#fff',
        borderLeft: '1px solid #e5e7eb',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.12)',
        zIndex: 200,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {loading && (
        <p style={{ padding: '20px', color: '#6b7280', fontSize: '13px', margin: 0 }}>Loading…</p>
      )}

      {error && (
        <p style={{ padding: '20px', color: '#dc2626', fontSize: '13px', margin: 0 }}>
          Failed to load site detail.
        </p>
      )}

      {data && <SuperfundDrawerContent site={data} onClose={onClose} />}

      {/* Close link at bottom (UX Invariant 9) */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid #e5e7eb', marginTop: 'auto', flexShrink: 0 }}>
        <button
          data-testid="popup-close-bottom"
          onClick={onClose}
          style={{ fontSize: '12px', color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: 'inherit' }}
        >
          ← Close
        </button>
      </div>
    </div>
  )
}

/** Inner content when data is loaded. */
function SuperfundDrawerContent({ site, onClose }: { site: SuperfundDetail; onClose: () => void }): JSX.Element {
  return (
    <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb', background: '#fef2f2' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#111827', lineHeight: 1.3 }}>
            {site.name}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#6b7280', flexShrink: 0, padding: '0 4px' }}
          >
            ×
          </button>
        </div>
        <p style={{ margin: '4px 0 0', fontSize: '11px', color: '#6b7280', fontFamily: 'monospace' }}>
          EPA ID: {site.epa_id}
        </p>
        <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#6b7280' }}>
          {[site.address, site.city, site.state_code, site.zip_code].filter(Boolean).join(', ')}
        </p>
      </div>

      {/* Body */}
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, overflowY: 'auto' }}>

        {/* Status + HRS score */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '3px', background: '#fef2f2', color: '#ef4444', fontWeight: 600 }}>
            {site.status}
          </span>
          {site.hrs_score !== null && (
            <span data-testid="superfund-hrs-score" style={hrsBadgeStyle(site.hrs_score)}>
              HRS {site.hrs_score.toFixed(2)}
            </span>
          )}
          {site.npl_date && (
            <span style={{ fontSize: '11px', color: '#6b7280' }}>
              Listed: {site.npl_date}
            </span>
          )}
        </div>

        {/* Contaminants list (story 4.2.2) */}
        <section>
          <h3 style={{ margin: '0 0 8px', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>
            Contaminants ({site.contaminants.length})
          </h3>
          {site.contaminants.length === 0 ? (
            <p style={{ margin: 0, fontSize: '12px', color: '#9ca3af' }}>None on record.</p>
          ) : (
            <ul
              data-testid="superfund-contaminants-list"
              style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '4px' }}
            >
              {site.contaminants.map((c) => (
                <li key={c.name} style={{ fontSize: '12px', color: '#374151', lineHeight: 1.4 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', flexWrap: 'wrap' }}>
                    {/* Diamond bullet */}
                    <svg width="6" height="6" viewBox="0 0 6 6" style={{ flexShrink: 0, position: 'relative', top: '-1px' }}>
                      <rect x="0.5" y="0.5" width="5" height="5" rx="0.5" fill="#ef4444" transform="rotate(45 3 3)" />
                    </svg>
                    {/* Chemical name — link to PubChem if available */}
                    {c.pubchem_url ? (
                      <a
                        data-testid="superfund-contaminant-pubchem"
                        href={c.pubchem_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                      >
                        {c.name}
                      </a>
                    ) : (
                      <span style={{ fontWeight: 500 }}>{c.name}</span>
                    )}
                    {/* CAS number inline */}
                    {c.cas_number && (
                      <span style={{ fontSize: '10px', color: '#9ca3af' }}>
                        {c.cas_number}
                      </span>
                    )}
                    {/* ATSDR link inline if present */}
                    {c.atsdr_url && (
                      <a
                        data-testid="superfund-contaminant-link"
                        href={c.atsdr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: '10px', color: '#059669', textDecoration: 'none', marginLeft: '2px' }}
                      >
                        ToxFAQs™
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* EPA Site Progress Profile link (story 4.2.3) */}
        {site.epa_progress_url && (
          <a
            data-testid="superfund-epa-progress-link"
            href={site.epa_progress_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: '13px', color: '#2563eb', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            EPA Site Progress Profile ↗
          </a>
        )}
      </div>
    </div>
  )
}
