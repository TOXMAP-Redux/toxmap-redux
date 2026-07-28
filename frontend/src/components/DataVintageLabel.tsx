/**
 * DataVintageLabel — shows TRI data vintage in the map footer.
 * Story 3.1.5 · UX Invariant 7 (latest year label).
 * data-testid="data-vintage-label" is required by TEST_ID_REGISTRY and Phase 3 DoD.
 *
 * OSM/Photon attribution is handled by MapLibre's AttributionControl (compact=false)
 * in MapContainer — always visible, linked to openstreetmap.org/copyright. This
 * component only shows the TRI data vintage (product info, not legal attribution).
 */

interface DataVintageLabelProps {
  vintageLabel: string | null
}

/** Fixed bottom-right overlay showing the EPA TRI data vintage. */
export function DataVintageLabel({ vintageLabel }: DataVintageLabelProps): JSX.Element {
  // Show vintage_label as-is from the API — the backend is responsible for
  // constructing a meaningful string (real EPA freeze date in production;
  // a dev/seed fallback in development). No extra formatting here.
  const label = vintageLabel ?? 'TRI: loading…'

  return (
    <div
      data-testid="data-vintage-label"
      className="toxmap-vintage-label"
      style={{
        position: 'absolute',
        bottom: '42px',
        right: '8px',
        zIndex: 10,
        background: 'rgba(255,255,255,0.92)',
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        color: '#374151',
        boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
        pointerEvents: 'none',
        fontFamily: 'system-ui, sans-serif',
        textAlign: 'left',
        whiteSpace: 'nowrap',
      }}
    >
      {label}
    </div>
  )
}
