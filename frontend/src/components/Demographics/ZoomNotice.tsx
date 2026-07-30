/**
 * ZoomNotice — story 5.2.2.
 * Shows "Zoom out to see more counties" when zoom > 8.
 */

interface ZoomNoticeProps {
  /** Current map zoom level */
  zoom: number
  /** Whether a demographic layer is active */
  isLayerActive: boolean
}

const ZOOM_THRESHOLD = 8

/**
 * Notice displayed when zoomed in too far to see county-level context.
 */
export function ZoomNotice({ zoom, isLayerActive }: ZoomNoticeProps): JSX.Element | null {
  if (!isLayerActive || zoom <= ZOOM_THRESHOLD) {
    return null
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: '80px',
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '8px 16px',
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        fontSize: '12px',
        color: '#4b5563',
        zIndex: 20,
        pointerEvents: 'none',
      }}
    >
      Zoom out to see more counties
    </div>
  )
}
