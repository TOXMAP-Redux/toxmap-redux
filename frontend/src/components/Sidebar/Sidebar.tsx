/**
 * Sidebar — stories 3.2.1, 3.2.9, 5.1.1.
 * UX Invariant 1: Map Contents and Search Results NEVER visible simultaneously.
 * Only one panel is active at a time (controlled by activePanel prop).
 */
import { MapContentsPanel } from './MapContentsPanel'
import { useState, useRef, useCallback } from 'react'
import { SearchPanel, type SearchFormValues } from './SearchPanel'
import type { FacilityCollection, SuperfundCollection, DemographicLayer } from '../../api/types'
import type { GeocodeResult } from '../../api/geocode'

export type ActivePanel = 'map-contents' | 'search'

interface SidebarProps {
  /** Which panel is currently active — controlled by parent (App). */
  activePanel: ActivePanel
  isCollapsed: boolean
  onToggleCollapse: () => void
  onPanelChange: (panel: ActivePanel) => void
  onSearch: (values: SearchFormValues) => void
  /** Current sidebar width in pixels (controlled by parent) */
  sidebarWidth: number
  /** Callback when user drags to resize sidebar */
  onSidebarWidthChange: (width: number) => void

  /** Data passed through to SearchPanel */
  facilities: FacilityCollection | null
  /** Superfund search results for Superfund dataset mode (story 4.1.3) */
  superfundResults: SuperfundCollection | null
  loading: boolean
  error: string | null
  highlightedFacilityId: string | null
  onHighlight: (id: string | null) => void
  onFacilitySelect: (id: string, type: 'tri' | 'superfund') => void
  /** Resolved geocode result with confidence info */
  resolvedGeocode: GeocodeResult | null

  /** Passed to MapContentsPanel */
  latestYear: number | null
  /** Controls TRI circle layer visibility */
  showTRILayer: boolean
  onToggleTRILayer: () => void
  /** Controls the Superfund diamond layer visibility (story 4.1.2) */
  showSuperfundLayer: boolean
  onToggleSuperfundLayer: () => void
  /** Layer status for MapContentsPanel badges */
  triViewportCount: number | null
  triViewportLoading: boolean
  superfundViewportCount: number | null
  superfundViewportLoading: boolean
  /** Currently selected demographic layer (story 5.2.1) */
  selectedDemographicLayer: DemographicLayer | null
  /** Handler for demographic layer selection */
  onDemographicLayerSelect: (layer: DemographicLayer | null) => void
}

/**
 * Collapsible left sidebar with single-panel enforcement (UX Invariant 1).
 * Shows MapContentsPanel by default; switches to SearchPanel after search.
 */
export function Sidebar({
  activePanel,
  isCollapsed,
  onToggleCollapse,
  onPanelChange,
  onSearch,
  sidebarWidth,
  onSidebarWidthChange,
  facilities,
  superfundResults,
  loading,
  error,
  highlightedFacilityId,
  onHighlight,
  onFacilitySelect,
  resolvedGeocode,
  latestYear,
  showTRILayer,
  onToggleTRILayer,
  showSuperfundLayer,
  onToggleSuperfundLayer,
  triViewportCount,
  triViewportLoading,
  superfundViewportCount,
  superfundViewportLoading,
  selectedDemographicLayer,
  onDemographicLayerSelect,
}: SidebarProps): JSX.Element {
  // Ref for direct DOM manipulation during resize (avoids React re-render lag)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const [isResizing, setIsResizing] = useState(false)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsResizing(true)

    const startX = e.clientX
    const startWidth = sidebarWidth
    const sidebar = sidebarRef.current

    // Disable text selection and transitions during drag
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
    if (sidebar) {
      sidebar.style.transition = 'none'
    }

    const handleMouseMove = (moveEvent: MouseEvent) => {
      moveEvent.preventDefault()
      moveEvent.stopPropagation()
      const delta = moveEvent.clientX - startX
      const newWidth = Math.min(600, Math.max(200, startWidth + delta))
      // Direct DOM update for smooth dragging (no React state during drag)
      if (sidebar) {
        sidebar.style.width = `${newWidth}px`
      }
    }

    const handleMouseUp = (upEvent: MouseEvent) => {
      upEvent.preventDefault()
      upEvent.stopPropagation()
      
      // Restore normal behavior
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
      if (sidebar) {
        sidebar.style.transition = ''
      }

      // Commit final width to React state
      if (sidebar) {
        const finalWidth = parseInt(sidebar.style.width, 10)
        if (!isNaN(finalWidth)) {
          onSidebarWidthChange(finalWidth)
        }
      }

      setIsResizing(false)
      document.removeEventListener('mousemove', handleMouseMove, true)
      document.removeEventListener('mouseup', handleMouseUp, true)
    }

    // Use capture phase to intercept events before map receives them
    document.addEventListener('mousemove', handleMouseMove, true)
    document.addEventListener('mouseup', handleMouseUp, true)
  }, [sidebarWidth, onSidebarWidthChange])

  const width = isCollapsed ? '2.5rem' : `${sidebarWidth}px`

  return (
    <div
      ref={sidebarRef}
      data-testid="sidebar-panel"
      data-active={!isCollapsed ? 'true' : 'false'}
      className="toxmap-sidebar absolute left-0 top-0 z-30 flex h-full flex-col bg-white shadow-lg transition-all duration-300"
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        height: '100%',
        zIndex: 30,
        background: '#fff',
        boxShadow: '2px 0 12px rgba(0,0,0,0.12)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: isResizing ? 'none' : 'width 250ms ease',
        width,
      }}
    >
      {/* Header with panel tabs + collapse toggle */}
      <div
        className="toxmap-sidebar-header flex shrink-0 items-center border-b border-gray-200 bg-gray-50"
        style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #e5e7eb', background: '#f9fafb', flexShrink: 0 }}
      >
        {!isCollapsed && (
          <div className="flex flex-1 overflow-hidden" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
            <button
              type="button"
              onClick={() => onPanelChange('map-contents')}
              className={`toxmap-sidebar-tab flex-1 truncate px-2 py-2 text-xs font-medium transition-colors ${
                activePanel === 'map-contents' ? 'active border-b-2 border-blue-600 text-blue-700' : 'text-gray-500 hover:text-gray-700'
              }`}
              style={{ flex: 1, padding: '8px 4px', fontSize: '12px', fontWeight: 500, background: 'none', border: 'none', borderBottom: activePanel === 'map-contents' ? '2px solid #2563eb' : '2px solid transparent', cursor: 'pointer', color: activePanel === 'map-contents' ? '#1d4ed8' : '#6b7280' }}
            >
              Map Contents
            </button>
            <button
              type="button"
              onClick={() => onPanelChange('search')}
              className={`toxmap-sidebar-tab flex-1 truncate px-2 py-2 text-xs font-medium transition-colors ${
                activePanel === 'search' ? 'active border-b-2 border-blue-600 text-blue-700' : 'text-gray-500 hover:text-gray-700'
              }`}
              style={{ flex: 1, padding: '8px 4px', fontSize: '12px', fontWeight: 500, background: 'none', border: 'none', borderBottom: activePanel === 'search' ? '2px solid #2563eb' : '2px solid transparent', cursor: 'pointer', color: activePanel === 'search' ? '#1d4ed8' : '#6b7280' }}
            >
              Search
            </button>
          </div>
        )}

        <button
          data-testid="sidebar-collapse-btn"
          type="button"
          onClick={onToggleCollapse}
          className="toxmap-sidebar-collapse shrink-0 p-2 text-gray-500 hover:text-gray-800"
          style={{ flexShrink: 0, padding: '8px', background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', fontSize: '16px', lineHeight: 1 }}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '›' : '‹'}
        </button>
      </div>

      {/* Panel content — only one is rendered at a time (UX Invariant 1) */}
      {!isCollapsed && (
        <div
          className="toxmap-sidebar-body flex-1 overflow-hidden"
          style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
        >
          {activePanel === 'map-contents' && (
            <MapContentsPanel
              latestYear={latestYear}
              showTRILayer={showTRILayer}
              onToggleTRILayer={onToggleTRILayer}
              showSuperfundLayer={showSuperfundLayer}
              onToggleSuperfundLayer={onToggleSuperfundLayer}
              triCount={triViewportCount}
              triLoading={triViewportLoading}
              superfundCount={superfundViewportCount}
              superfundLoading={superfundViewportLoading}
              selectedDemographicLayer={selectedDemographicLayer}
              onDemographicLayerSelect={onDemographicLayerSelect}
            />
          )}
          {activePanel === 'search' && (
            <SearchPanel
              facilities={facilities}
              superfundResults={superfundResults}
              loading={loading}
              error={error}
              highlightedFacilityId={highlightedFacilityId}
              onHighlight={onHighlight}
              onSelect={onFacilitySelect}
              onSearch={onSearch}
              resolvedGeocode={resolvedGeocode}
            />
          )}
        </div>
      )}

      {/* Resize handle — drag to adjust sidebar width */}
      {!isCollapsed && (
        <div
          data-testid="sidebar-resize-handle"
          onMouseDown={handleMouseDown}
          style={{
            position: 'absolute',
            top: 0,
            right: -3, // Extend slightly outside for easier grabbing
            width: '8px',
            height: '100%',
            cursor: 'col-resize',
            background: isResizing ? '#3b82f6' : 'transparent',
            zIndex: 50, // Above everything
          }}
          onMouseEnter={(e) => { if (!isResizing) (e.currentTarget as HTMLElement).style.background = 'rgba(59, 130, 246, 0.3)' }}
          onMouseLeave={(e) => { if (!isResizing) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
        />
      )}
    </div>
  )
}
