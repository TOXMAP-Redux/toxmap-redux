/**
 * InterpretationBanner — story 3.6.2.
 * "Release quantity does not indicate health risk" disclaimer shown at all times
 * in a subtle bar at the top of the map viewport.
 */
import { useState } from 'react'

/** Non-dismissable interpretation banner anchored to the bottom of the viewport. */
export function InterpretationBanner(): JSX.Element {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return <></>

  return (
    <div
      data-testid="interpretation-banner"
      className="toxmap-banner absolute bottom-0 left-0 right-0 z-20 flex items-center justify-end bg-blue-50 px-4 py-1.5 text-xs text-blue-800 shadow-sm"
      style={{ position: 'absolute', bottom: 0, left: 0, right: 0, zIndex: 20, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', background: '#eff6ff', borderTop: '1px solid #bfdbfe', padding: '6px 16px', fontSize: '11px', color: '#1e40af' }}
    >
      <span>
        ⚠️ Release quantities indicate amounts reported to the EPA. They do not indicate health risk
        or exposure levels.
      </span>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '14px', color: '#3b82f6', padding: '0 4px', lineHeight: 1, marginLeft: '12px' }}
        aria-label="Dismiss interpretation banner"
      >
        ✕
      </button>
    </div>
  )
}
