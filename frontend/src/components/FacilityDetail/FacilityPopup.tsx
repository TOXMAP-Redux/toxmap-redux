/**
 * FacilityPopup — story 3.4.1, 3.4.2, 3.4.4.
 * UX Invariants: 8 (comma numbers), 9 (close link at BOTTOM of popup).
 * Rendered inside the MapLibre map canvas via react-map-gl Popup.
 */
import { Popup } from 'react-map-gl/maplibre'
import { formatLbs } from '../../utils/formatLbs'
import type { FacilityFeature } from '../../api/types'

interface FacilityPopupProps {
  facility: FacilityFeature
  onClose: () => void
  onOpenDetail: (id: string) => void
}

/**
 * MapLibre GL popup shown when a TRI facility circle is clicked.
 * Close link is at the BOTTOM of the popup (UX Invariant 9).
 */
export function FacilityPopup({ facility, onClose, onOpenDetail }: FacilityPopupProps): JSX.Element {
  const [lon, lat] = facility.geometry.coordinates
  const props = facility.properties

  const colorMap: Record<string, string> = {
    red: '#dc2626', orange: '#ea580c', yellow: '#ca8a04', green: '#16a34a',
  }
  const amountColor = colorMap[props.color_band] ?? '#374151'

  return (
    <Popup
      longitude={lon}
      latitude={lat}
      onClose={onClose}
      closeButton={false}
      anchor="bottom"
      maxWidth="300px"
    >
      <div data-testid="facility-detail-panel" className="toxmap-popup" style={{ minWidth: '200px', maxWidth: '280px', fontSize: '13px', fontFamily: 'system-ui, sans-serif' }}>
        <div className="toxmap-popup-name" style={{ fontWeight: 700, marginBottom: '2px', color: '#111827', lineHeight: 1.3 }}>{props.name}</div>
        <div className="toxmap-popup-addr" style={{ fontSize: '11px', color: '#6b7280', marginBottom: '8px' }}>
          {props.address && <span>{props.address}, </span>}
          {props.city}, {props.state_code}
        </div>

        {props.chemical_name && (
          <div className="toxmap-popup-chem" style={{ fontSize: '12px', marginBottom: '10px' }}>
            <span style={{ fontWeight: 600 }}>{props.chemical_name}: </span>
            <span
              data-testid="facility-release-amount"
              style={{ fontFamily: 'monospace', fontWeight: 700, color: amountColor }}
            >
              {formatLbs(props.total_release_lbs)}
            </span>
            {props.reporting_year && (
              <span style={{ color: '#9ca3af' }}> ({props.reporting_year})</span>
            )}
          </div>
        )}

        <button
          type="button"
          onClick={() => onOpenDetail(props.tri_facility_id)}
          className="toxmap-popup-btn"
          style={{ display: 'block', width: '100%', padding: '7px 10px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', textAlign: 'center', marginBottom: '8px', fontFamily: 'inherit' }}
        >
          View full details →
        </button>

        {/* Close link at BOTTOM of popup — UX Invariant 9 */}
        <button
          data-testid="popup-close-bottom"
          type="button"
          onClick={onClose}
          className="toxmap-popup-close"
          style={{ display: 'block', width: '100%', textAlign: 'center', fontSize: '11px', color: '#9ca3af', background: 'none', border: 'none', cursor: 'pointer', padding: '2px', fontFamily: 'inherit' }}
        >
          Close
        </button>
      </div>
    </Popup>
  )
}
