/**
 * ZoomNotice — story 5.2.2.
 * UCD-10: "County data unclear when zoomed in → Add zoom-out hint"
 *
 * From UCD 2011 Fig 17: Users zoomed in closely saw only one color (a single
 * county filling the viewport) and didn't understand why the layer wasn't
 * showing variation. They needed prompting to zoom out to see county-level
 * context.
 *
 * Shows "Demographic data is at the county level. Zoom out to see more counties."
 * when zoom > 8 (roughly street-level, where only 1-2 counties are visible).
 */

interface ZoomNoticeProps {
  /** Current map zoom level */
  zoom: number
  /** Whether a demographic layer is active */
  isLayerActive: boolean
}

/**
 * Zoom threshold: at zoom > 8, most US viewports show only 1-2 counties.
 * UCD 2011 Fig 17 showed users at "2 km / 1 mi" scale (zoom ~12-13) seeing
 * solid color across the viewport. We show the notice earlier (zoom > 8) to
 * proactively guide users before they hit the single-county edge case.
 */
const ZOOM_THRESHOLD = 8

/**
 * Notice displayed when zoomed in too far to see county-level context (UCD-10).
 */
export function ZoomNotice({ zoom, isLayerActive }: ZoomNoticeProps): JSX.Element | null {
  if (!isLayerActive || zoom <= ZOOM_THRESHOLD) {
    return null
  }

  return (
    <div
      data-testid="demographic-zoom-notice"
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
      Demographic data is at the county level. Zoom out to see more counties.
    </div>
  )
}
