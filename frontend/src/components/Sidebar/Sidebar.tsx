/**
 * Sidebar — stories 3.2.1, 3.2.9.
 * UX Invariant 1: Map Contents and Search Results NEVER visible simultaneously.
 * Only one panel is active at a time (controlled by activePanel prop).
 */
import { MapContentsPanel } from './MapContentsPanel'
import { SearchPanel, type SearchFormValues } from './SearchPanel'
import type { FacilityCollection, SuperfundCollection } from '../../api/types'

export type ActivePanel = 'map-contents' | 'search'

interface SidebarProps {
  /** Which panel is currently active — controlled by parent (App). */
  activePanel: ActivePanel
  isCollapsed: boolean
  onToggleCollapse: () => void
  onPanelChange: (panel: ActivePanel) => void
  onSearch: (values: SearchFormValues) => void

  /** Data passed through to SearchPanel */
  facilities: FacilityCollection | null
  /** Superfund search results for Superfund dataset mode (story 4.1.3) */
  superfundResults: SuperfundCollection | null
  loading: boolean
  error: string | null
  highlightedFacilityId: string | null
  onHighlight: (id: string | null) => void
  onFacilitySelect: (id: string) => void

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
  facilities,
  superfundResults,
  loading,
  error,
  highlightedFacilityId,
  onHighlight,
  onFacilitySelect,
  latestYear,
  showTRILayer,
  onToggleTRILayer,
  showSuperfundLayer,
  onToggleSuperfundLayer,
  triViewportCount,
  triViewportLoading,
  superfundViewportCount,
  superfundViewportLoading,
}: SidebarProps): JSX.Element {
  const width = isCollapsed ? '2.5rem' : '20rem'

  return (
    <div
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
        transition: 'width 250ms ease',
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
            />
          )}
        </div>
      )}
    </div>
  )
}
