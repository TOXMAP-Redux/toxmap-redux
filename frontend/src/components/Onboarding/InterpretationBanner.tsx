/**
 * InterpretationBanner — story 3.6.2.
 * "Release quantity does not indicate health risk" disclaimer shown at first load.
 * Anchored to the top of the map viewport with smooth dismiss animation.
 */
import { useState } from 'react'

/** Dismissable interpretation banner anchored to the top of the map viewport. */
export function InterpretationBanner(): JSX.Element {
  const [dismissed, setDismissed] = useState(false)
  const [animatingOut, setAnimatingOut] = useState(false)

  const handleDismiss = () => {
    setAnimatingOut(true)
    setTimeout(() => setDismissed(true), 200) // Match animation duration
  }

  if (dismissed) return <></>

  return (
    <div
      data-testid="interpretation-banner"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 30,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        background: 'linear-gradient(to right, #fef3c7, #fef9c3)',
        borderBottom: '1px solid #fcd34d',
        padding: '10px 48px 10px 16px',
        fontSize: '13px',
        color: '#92400e',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        transform: animatingOut ? 'translateY(-100%)' : 'translateY(0)',
        opacity: animatingOut ? 0 : 1,
        transition: 'transform 0.2s ease-out, opacity 0.2s ease-out',
      }}
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ flexShrink: 0 }}
        aria-hidden="true"
      >
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
      <span style={{ lineHeight: 1.4 }}>
        <strong>Note:</strong> Release quantities indicate amounts reported to the EPA.
        They do not indicate health risk or exposure levels.
      </span>
      <button
        type="button"
        onClick={handleDismiss}
        style={{
          position: 'absolute',
          right: '12px',
          top: '50%',
          transform: 'translateY(-50%)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontSize: '18px',
          color: '#b45309',
          padding: '4px 8px',
          lineHeight: 1,
          borderRadius: '4px',
          transition: 'background 0.15s',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(180, 83, 9, 0.1)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
        aria-label="Dismiss disclaimer"
      >
        ×
      </button>
    </div>
  )
}
