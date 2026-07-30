/**
 * MapContentsPanel — stories 3.2.2, 4.1.2, 4.3.1, 5.1.1–5.1.5.
 * UX Invariant 7: year toggle shows "(latest year)" on most-recent year.
 * UX Invariant 1: this panel is hidden when SearchPanel is active.
 * UX Invariant 6: Superfund toggle + legend entry distinct from TRI circles.
 * UX Invariant 4: Label is "US Census & Health Data" (NOT "Demographics").
 */
import { CensusHealthPanel } from '../Demographics/CensusHealthPanel'
import type { DemographicLayer } from '../../api/types'

interface MapContentsPanelProps {
  latestYear: number | null
  /** Controls TRI circle layer visibility */
  showTRILayer: boolean
  onToggleTRILayer: () => void
  /** Whether the Superfund diamond layer is currently visible (story 4.1.2) */
  showSuperfundLayer: boolean
  /** Toggle handler for the Superfund layer checkbox */
  onToggleSuperfundLayer: () => void
  /** Number of TRI facilities currently loaded in viewport (null = loading) */
  triCount: number | null
  triLoading: boolean
  /** Number of Superfund sites currently loaded in viewport */
  superfundCount: number | null
  superfundLoading: boolean
  /** Currently selected demographic layer (story 5.2.1) */
  selectedDemographicLayer: DemographicLayer | null
  /** Handler for demographic layer selection */
  onDemographicLayerSelect: (layer: DemographicLayer | null) => void
}

/** Small inline status badge: "loading…", "N sites", or empty */
function LayerStatus({
  loading,
  count,
}: {
  loading: boolean
  count: number | null
}): JSX.Element {
  if (loading && count === null)
    return <span style={{ fontSize: '10px', color: '#9ca3af', marginLeft: '6px' }}>loading…</span>
  if (count !== null)
    return (
      <span style={{ fontSize: '10px', color: '#6b7280', marginLeft: '6px' }}>
        {count.toLocaleString()} in view
      </span>
    )
  return <></>
}

/** Layer toggles and legend shown when no search is active. */
export function MapContentsPanel({
  latestYear,
  showTRILayer,
  onToggleTRILayer,
  showSuperfundLayer,
  onToggleSuperfundLayer,
  triCount,
  triLoading,
  superfundCount,
  superfundLoading,
  selectedDemographicLayer,
  onDemographicLayerSelect,
}: MapContentsPanelProps): JSX.Element {
  return (
    <div data-testid="map-contents-panel" className="toxmap-map-contents" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto', flex: 1 }}>
      <h2 style={{ margin: 0, fontSize: '13px', fontWeight: 700 }}>Map Contents</h2>

      {/* TRI Layers */}
      <section>
        <h3 style={{ margin: '0 0 6px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>TRI Layers</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer', fontWeight: 'normal', marginBottom: 0 }}>
          <input
            data-testid="layer-toggle-tri"
            type="checkbox"
            checked={showTRILayer}
            onChange={onToggleTRILayer}
            style={{ accentColor: '#2563eb' }}
          />
          <span style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '2px' }}>
            TRI Facilities —{' '}
            <span
              data-testid="year-toggle-latest"
              style={{ color: '#6b7280', fontStyle: 'italic' }}
            >
              {latestYear ? `${latestYear} (latest year)` : '(latest year)'}
            </span>
            <LayerStatus loading={triLoading} count={triCount} />
          </span>
        </label>
      </section>

      {/* Superfund Layer (story 4.1.2) */}
      <section>
        <h3 style={{ margin: '0 0 6px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>Superfund Layers</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer', fontWeight: 'normal', marginBottom: 0 }}>
          <input
            data-testid="layer-toggle-superfund"
            type="checkbox"
            checked={showSuperfundLayer}
            onChange={onToggleSuperfundLayer}
            style={{ accentColor: '#ef4444' }}
          />
          <span style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '2px' }}>
            Superfund / NPL Sites
            <LayerStatus loading={superfundLoading} count={superfundCount} />
          </span>
        </label>
      </section>

      {/* Unified legend (story 4.3.1) */}
      <section>
        <h3 style={{ margin: '0 0 6px', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280' }}>Legend</h3>

        {/* TRI Release Tiers */}
        <p style={{ margin: '0 0 4px', fontSize: '10px', color: '#9ca3af', fontWeight: 500 }}>TRI Release Tiers</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginBottom: '10px' }}>
          {[
            { color: '#22c55e', label: '< 1,000 lbs', shape: 'circle' },
            { color: '#eab308', label: '1,000 – 9,999 lbs', shape: 'circle' },
            { color: '#f97316', label: '10,000 – 99,999 lbs', shape: 'circle' },
            { color: '#ef4444', label: '≥ 100,000 lbs', shape: 'circle' },
          ].map(({ color, label }) => (
            <div key={color} className="toxmap-legend-item" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
              <span
                className="toxmap-legend-swatch"
                style={{ width: '12px', height: '12px', borderRadius: '50%', flexShrink: 0, background: color, display: 'inline-block' }}
              />
              <span>{label}</span>
            </div>
          ))}
        </div>

        {/* Superfund entry */}
        {showSuperfundLayer && (
          <>
            <p style={{ margin: '0 0 4px', fontSize: '10px', color: '#9ca3af', fontWeight: 500 }}>Superfund</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
              {/* Diamond SVG swatch (distinct from circle — UX invariant 6) */}
              <svg width="14" height="14" viewBox="0 0 14 14" style={{ flexShrink: 0 }}>
                <rect x="1" y="1" width="12" height="12" rx="1"
                  fill="#ef4444" stroke="white" strokeWidth="1.5"
                  transform="rotate(45 7 7)" />
              </svg>
              <span>Superfund NPL site</span>
            </div>
          </>
        )}
      </section>

      {/* Divider before Census panel */}
      <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '4px 0' }} />

      {/* US Census & Health Data panel (stories 5.1.1–5.1.5) */}
      <CensusHealthPanel
        selectedLayer={selectedDemographicLayer}
        onLayerSelect={onDemographicLayerSelect}
      />
    </div>
  )
}
