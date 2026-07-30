/**
 * InlineLegend — stories 5.3.1, 5.3.2, 5.3.3.
 * UX Invariant 5: Legend values and units MUST be visible without hover.
 *
 * Displays a color-range legend for the active demographic layer.
 * At least 3 entries visible at all times.
 */
import type { DemographicLayer, DemographicUnits } from '../../api/types'
import { getColorScale, getLegendRanges, getLayerLabel } from './colorUtils'

interface InlineLegendProps {
  /** Currently selected demographic layer */
  layer: DemographicLayer
  /** Units metadata from API response meta.units */
  units: DemographicUnits | null
  /** Handler for "Clear layer" button (story 5.3.3) */
  onClear: () => void
}

/**
 * Inline demographic legend with always-visible values (UX Invariant 5).
 * At least 3 color-range entries are visible without hover.
 */
export function InlineLegend({
  layer,
  units,
  onClear,
}: InlineLegendProps): JSX.Element {
  const colors = getColorScale(layer)
  const ranges = getLegendRanges(layer)
  const label = getLayerLabel(layer)
  const unit = units?.[layer] ?? ''

  return (
    <div
      data-testid="demographic-legend"
      style={{
        padding: '8px 12px',
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '6px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
        fontSize: '12px',
      }}
    >
      {/* Layer title with unit */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <span style={{ fontWeight: 600, color: '#111827' }}>
          {label} {unit && <span style={{ color: '#6b7280', fontWeight: 400 }}>({unit})</span>}
        </span>
        <button
          data-testid="clear-layer-btn"
          type="button"
          onClick={onClear}
          style={{
            background: 'none',
            border: 'none',
            color: '#2563eb',
            cursor: 'pointer',
            fontSize: '11px',
            padding: '2px 4px',
          }}
        >
          Clear layer
        </button>
      </div>

      {/* Color entries — at least 3 visible without hover (UX Invariant 5) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {colors.map((color, i) => (
          <div
            key={color}
            data-testid="demographic-legend-entry"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span
              style={{
                width: '16px',
                height: '16px',
                borderRadius: '3px',
                background: color,
                flexShrink: 0,
                border: '1px solid rgba(0,0,0,0.1)',
              }}
            />
            <span style={{ color: '#374151' }}>{ranges[i]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Re-export utilities from colorUtils for convenience
export { COLOR_SCALES, getColorScale, getLegendRanges } from './colorUtils'
