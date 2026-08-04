/**
 * SearchPanel — stories 3.2.3–3.2.9.
 * UX Invariants: 1 (single sidebar), 2 (viewport scoped), 3 (state filter restricts),
 *                4 (correct labels), 8 (comma numbers).
 *
 * Panel label MUST be "Search Chemical Releases by Location" — NOT "Quick Search".
 * data-testids match TEST_ID_REGISTRY exactly.
 */
import { useState, type FormEvent } from 'react'
import { useChemicalAutocomplete } from '../../hooks/useChemicalAutocomplete'
import { ResultsTable } from '../ResultsTable/ResultsTable'
import type { Chemical, FacilityCollection, SuperfundCollection } from '../../api/types'

/** US states for the state dropdown. */
const US_STATES = [
  // 50 states + DC (alphabetical by code)
  'AK','AL','AR','AZ','CA','CO','CT','DC','DE','FL','GA','HI','IA','ID','IL','IN',
  'KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ',
  'NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA',
  'WI','WV','WY',
]

/** Continental US = 48 contiguous states + DC (excludes AK, HI, and territories). */
const CONTINENTAL_US_STATES = new Set([
  'AL','AR','AZ','CA','CO','CT','DC','DE','FL','GA','IA','ID','IL','IN',
  'KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ',
  'NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA',
  'WI','WV','WY',
])

/** US territories included in TRI data. */
const US_TERRITORIES = ['AS', 'GU', 'MP', 'PR', 'VI']

/** Check if a state code is in the continental US (48 states + DC). */
export function isContinentalUS(stateCode: string): boolean {
  return CONTINENTAL_US_STATES.has(stateCode)
}

/** Special value for "Continental US" filter option. */
export const CONUS_FILTER = 'CONUS'

/** Year range for the year dropdown (1987 → present). */
function buildYears(): number[] {
  const years: number[] = []
  const current = new Date().getFullYear()
  for (let y = current; y >= 1987; y--) years.push(y)
  return years
}
const YEARS = buildYears()

export interface SearchFormValues {
  location: string
  chemical: string
  chemicalObj: Chemical | null
  year: string
  /** If set, filters results to this state only */
  state: string
  /** Which dataset the search targets — controls results table mode (story 4.1.3) */
  dataset: 'tri' | 'superfund' | 'both'
  /** ADR-007: Skip chemical family expansion (search exact term only) */
  exactMatch?: boolean
}

interface SearchPanelProps {
  facilities: FacilityCollection | null
  /** Superfund results — non-null when dataset=superfund and search submitted */
  superfundResults: SuperfundCollection | null
  loading: boolean
  error: string | null
  highlightedFacilityId: string | null
  onHighlight: (id: string | null) => void
  onSelect: (id: string, type: 'tri' | 'superfund') => void
  onSearch: (values: SearchFormValues) => void
}

/**
 * Search panel — labeled "Search Chemical Releases by Location" (UX invariant 4).
 * Includes chemical autocomplete, location geocode, year/state filters, and results table.
 */
export function SearchPanel({
  facilities,
  superfundResults,
  loading,
  error,
  highlightedFacilityId,
  onHighlight,
  onSelect,
  onSearch,
}: SearchPanelProps): JSX.Element {
  const [location, setLocation] = useState('')
  const [chemicalInput, setChemicalInput] = useState('')
  const [selectedChemical, setSelectedChemical] = useState<Chemical | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [year, setYear] = useState('')
  const [state, setState] = useState('')
  const [dataset, setDataset] = useState<'tri' | 'superfund' | 'both'>('both')

  const { suggestions, loading: suggestionsLoading } = useChemicalAutocomplete(chemicalInput)

  const handleChemicalSelect = (chem: Chemical) => {
    setSelectedChemical(chem)
    setChemicalInput(chem.name)
    setShowSuggestions(false)
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    onSearch({
      location,
      chemical: selectedChemical?.name ?? chemicalInput,
      chemicalObj: selectedChemical,
      year,
      state,
      dataset,
      exactMatch: false,
    })
  }

  // ADR-007: Handler for "Search exact term only" from banner
  const handleSearchExact = () => {
    onSearch({
      location,
      chemical: selectedChemical?.name ?? chemicalInput,
      chemicalObj: selectedChemical,
      year,
      state,
      dataset,
      exactMatch: true,
    })
  }

  return (
    <div data-testid="search-panel" className="toxmap-search-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Panel label — MUST be "Search Chemical Releases by Location" (UX invariant 4) */}
      <h2 style={{ margin: 0, padding: '10px 12px', fontSize: '13px', fontWeight: 700, borderBottom: '1px solid #e5e7eb', color: '#111827', flexShrink: 0 }}>
        Search Chemical Releases by Location
      </h2>

      {/* Scrollable content area — allows form + results to scroll when window is small */}
      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
        <form onSubmit={handleSubmit} className="toxmap-search-form" style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '12px' }}>
          {/* Chemical field with autocomplete */}
        <div className="toxmap-search-field" style={{ position: 'relative' }}>
          <label htmlFor="chemical-input" style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#6b7280', marginBottom: '3px' }}>
            Chemical
          </label>
          <input
            id="chemical-input"
            data-testid="chemical-input"
            type="text"
            value={chemicalInput}
            onChange={(e) => {
              setChemicalInput(e.target.value)
              setSelectedChemical(null)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            placeholder="e.g. LEAD COMPOUNDS"
            autoComplete="off"
          />

          {/* ATSDR ToxFAQ link — shown when a chemical with atsdr_url is selected (T-08) */}
          {selectedChemical?.atsdr_url && (
            <a
              data-testid="atsdr-link"
              href={selectedChemical.atsdr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="toxmap-chem-link"
              style={{ fontSize: '11px', color: '#2563eb', textDecoration: 'none', display: 'block', marginTop: '3px' }}
            >
              See ToxFAQs™: {selectedChemical.name} ↗
            </a>
          )}

          {selectedChemical?.pubchem_url && (
            <a
              data-testid="pubchem-link"
              href={selectedChemical.pubchem_url}
              target="_blank"
              rel="noopener noreferrer"
              className="toxmap-chem-link"
              style={{ fontSize: '11px', color: '#2563eb', textDecoration: 'none', display: 'block', marginTop: '2px' }}
            >
              PubChem record ↗
            </a>
          )}

          {/* Autocomplete dropdown */}
          {showSuggestions && chemicalInput.length >= 2 && (
            <ul
              className="toxmap-autocomplete"
              style={{ position: 'absolute', left: 0, right: 0, top: '100%', zIndex: 50, maxHeight: '180px', overflowY: 'auto', background: '#fff', border: '1px solid #d1d5db', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.12)', marginTop: '2px', padding: 0 }}
            >
              {suggestionsLoading && (
                <li style={{ listStyle: 'none', padding: '8px 10px', fontSize: '12px', color: '#9ca3af' }}>Searching…</li>
              )}
              {!suggestionsLoading && suggestions.length === 0 && (
                <li style={{ listStyle: 'none', padding: '8px 10px', fontSize: '12px', color: '#9ca3af' }}>No chemicals found</li>
              )}
              {suggestions.map((chem) => (
                <li
                  key={chem.id}
                  data-testid="chemical-autocomplete-option"
                  style={{ listStyle: 'none', padding: '8px 10px', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                  onMouseOver={(e) => { (e.currentTarget as HTMLElement).style.background = '#eff6ff' }}
                  onMouseOut={(e) => { (e.currentTarget as HTMLElement).style.background = '' }}
                  onMouseDown={() => handleChemicalSelect(chem)}
                >
                  <span>{chem.name}</span>
                  {chem.cas_number && (
                    <span style={{ fontSize: '11px', color: '#9ca3af' }}>{chem.cas_number}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Location field */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <label htmlFor="location-input" style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#6b7280' }}>
            Location (city, state or zip)
          </label>
          <input
            id="location-input"
            data-testid="location-input"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Sparrows Point, MD"
          />
        </div>

        {/* Year dropdown */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <label htmlFor="year-select" style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#6b7280' }}>
            Reporting Year
          </label>
          <select
            id="year-select"
            data-testid="year-select"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="">All years</option>
            {YEARS.map((y) => (
              <option key={y} value={String(y)}>{y}</option>
            ))}
          </select>
        </div>

        {/* State filter dropdown (always filters when selected) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <label htmlFor="state-select" style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#6b7280' }}>
            Filter to state (optional)
          </label>
          <select
            id="state-select"
            data-testid="state-select"
            value={state}
            onChange={(e) => setState(e.target.value)}
          >
            <option value="">All</option>
            <option value={CONUS_FILTER}>Continental US</option>
            <optgroup label="States">
              {US_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </optgroup>
            <optgroup label="Territories">
              {US_TERRITORIES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </optgroup>
          </select>
        </div>

        {/* Dataset radio buttons — TRI, Superfund, or Both (story 4.1.3, Fig 2015-4) */}
        <div className="toxmap-dataset-radios" style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#6b7280' }}>
          {[
            { testid: 'dataset-radio-both', value: 'both' as const, label: 'Both' },
            { testid: 'dataset-radio-tri', value: 'tri' as const, label: 'TRI' },
            { testid: 'dataset-radio-superfund', value: 'superfund' as const, label: 'Superfund' },
          ].map(({ testid, value, label }) => (
            <label key={value} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', cursor: 'pointer', marginBottom: 0 }}>
              <input
                data-testid={testid}
                type="radio"
                name="dataset"
                value={value}
                checked={dataset === value}
                onChange={() => setDataset(value)}
                style={{ accentColor: '#2563eb' }}
              />
              {label}
            </label>
          ))}
        </div>

        <button
          data-testid="search-submit-btn"
          type="submit"
          style={{ width: '100%', padding: '9px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}
        >
          Search
        </button>

        {/* Show error only when there is no data to fall back on.
             Background re-fetch failures (map move) are suppressed by the hook;
             this handles the initial search failure case. */}
        {error && !facilities && (
          <p style={{ margin: 0, fontSize: '12px', color: '#dc2626' }}>
            {error}
          </p>
        )}
      </form>

      {/* Results table — shown after search */}
      {(facilities !== null || superfundResults !== null || loading) && (
        <div className="toxmap-results-table-container" data-testid="results-table-content" style={{ borderTop: '1px solid #e5e7eb' }}>
          <ResultsTable
            mode={dataset}
            triData={facilities}
            superfundData={superfundResults}
            loading={loading}
            highlightedFacilityId={highlightedFacilityId}
            onHighlight={onHighlight}
            onSelect={onSelect}
            searchExpansion={facilities?.meta.search_expansion}
            onSearchExact={handleSearchExact}
          />
        </div>
      )}
      </div>
    </div>
  )
}
