/**
 * CensusHealthPanel — stories 5.1.1–5.1.5, 5.4.1–5.4.2.
 * UX Invariant 4: Label MUST be "US Census & Health Data" — NOT "Demographics".
 * UX Invariant 10: Co-occurrence disclaimer on mortality tabs only.
 *
 * Tab structure:
 *   Year tabs (Census 2000 / Census 2020) >
 *   Category tabs (Population / Income / Age / Race / Mortality) >
 *   Sub-layer buttons >
 *   Gender radio (mortality only)
 */
import { useState, type ReactNode } from 'react'
import type { DemographicLayer } from '../../api/types'

/** Census year tabs */
type CensusYear = '2000' | '2020'

/** Category tabs within a census year */
type Category = 'population' | 'income' | 'mortality'

interface CensusHealthPanelProps {
  /** Currently selected sub-layer */
  selectedLayer: DemographicLayer | null
  /** Handler when user selects a sub-layer */
  onLayerSelect: (layer: DemographicLayer | null) => void
}

/** Simple tab button component */
function TabButton({
  active,
  onClick,
  testId,
  children,
}: {
  active: boolean
  onClick: () => void
  testId?: string
  children: ReactNode
}): JSX.Element {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      style={{
        padding: '6px 12px',
        background: active ? '#2563eb' : 'transparent',
        color: active ? '#fff' : '#4b5563',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '12px',
        fontWeight: active ? 600 : 400,
        transition: 'all 150ms ease',
      }}
    >
      {children}
    </button>
  )
}

/** Sub-layer button (selectable layer toggle) */
function SubLayerButton({
  active,
  onClick,
  testId,
  children,
}: {
  active: boolean
  onClick: () => void
  testId: string
  children: ReactNode
}): JSX.Element {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: '8px 12px',
        background: active ? '#eff6ff' : '#f9fafb',
        color: active ? '#1d4ed8' : '#374151',
        border: active ? '1px solid #3b82f6' : '1px solid #e5e7eb',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '12px',
        fontWeight: active ? 600 : 400,
        marginBottom: '6px',
      }}
    >
      {children}
    </button>
  )
}

/**
 * US Census & Health Data panel (story 5.1.1).
 * Provides tab navigation for demographic layers and choropleth controls.
 */
export function CensusHealthPanel({
  selectedLayer,
  onLayerSelect,
}: CensusHealthPanelProps): JSX.Element {
  const [censusYear, setCensusYear] = useState<CensusYear>('2000')
  const [category, setCategory] = useState<Category>('population')
  const [gender, setGender] = useState<'male' | 'female'>('female')

  // Only Census 2000 is available for MVP (story 5.1.2)
  const showComingSoon = censusYear === '2020'

  // Determine if we're on a mortality tab (UX Invariant 10)
  const isMortalityTab = category === 'mortality'

  /** Handle sub-layer selection */
  const handleLayerClick = (layer: DemographicLayer) => {
    // Toggle off if clicking the already-selected layer
    onLayerSelect(selectedLayer === layer ? null : layer)
  }

  /** Get mortality layer based on gender radio */
  const cancerLayer: DemographicLayer =
    gender === 'male' ? 'cancer_mortality_male_per_100k' : 'cancer_mortality_female_per_100k'

  return (
    <div
      data-testid="census-health-panel"
      style={{
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      {/* Panel title — MUST be "US Census & Health Data" (UX Invariant 4) */}
      <h2
        style={{
          margin: 0,
          fontSize: '13px',
          fontWeight: 700,
          color: '#111827',
        }}
      >
        US Census &amp; Health Data
      </h2>

      {/* Year tabs (story 5.1.2) */}
      <div style={{ display: 'flex', gap: '4px', background: '#f3f4f6', padding: '4px', borderRadius: '6px' }}>
        <TabButton active={censusYear === '2000'} onClick={() => setCensusYear('2000')}>
          Census 2000
        </TabButton>
        <TabButton active={censusYear === '2020'} onClick={() => setCensusYear('2020')}>
          Census 2020
        </TabButton>
      </div>

      {/* Census 2020 coming soon placeholder */}
      {showComingSoon ? (
        <div
          style={{
            padding: '24px 16px',
            textAlign: 'center',
            color: '#6b7280',
            fontSize: '13px',
            background: '#f9fafb',
            borderRadius: '6px',
          }}
        >
          Census 2020 data coming soon
        </div>
      ) : (
        <>
          {/* Category tabs (story 5.1.2) */}
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            <TabButton
              active={category === 'population'}
              onClick={() => setCategory('population')}
              testId="demo-tab-population"
            >
              Population
            </TabButton>
            <TabButton
              active={category === 'income'}
              onClick={() => setCategory('income')}
              testId="demo-tab-income"
            >
              Income
            </TabButton>
            <TabButton
              active={category === 'mortality'}
              onClick={() => setCategory('mortality')}
              testId="demo-tab-mortality"
            >
              Mortality
            </TabButton>
          </div>

          {/* Sub-layers per category */}
          <div>
            {category === 'population' && (
              <>
                <SubLayerButton
                  active={selectedLayer === 'pct_under_18'}
                  onClick={() => handleLayerClick('pct_under_18')}
                  testId="demo-sublayer-pct-under-18"
                >
                  % Under 18
                </SubLayerButton>
                <SubLayerButton
                  active={selectedLayer === 'pct_over_65'}
                  onClick={() => handleLayerClick('pct_over_65')}
                  testId="demo-sublayer-pct-over-65"
                >
                  % Over 65
                </SubLayerButton>
                <SubLayerButton
                  active={selectedLayer === 'total_pop'}
                  onClick={() => handleLayerClick('total_pop')}
                  testId="demo-sublayer-total-pop"
                >
                  Total Population
                </SubLayerButton>
              </>
            )}

            {category === 'income' && (
              <SubLayerButton
                active={selectedLayer === 'median_income'}
                onClick={() => handleLayerClick('median_income')}
                testId="demo-sublayer-median-income"
              >
                Median Household Income
              </SubLayerButton>
            )}

            {category === 'mortality' && (
              <>
                {/* Gender radio for mortality (story 5.4.2) */}
                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                    marginBottom: '10px',
                    fontSize: '12px',
                  }}
                >
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="mortality-gender"
                      value="male"
                      checked={gender === 'male'}
                      onChange={() => setGender('male')}
                      style={{ accentColor: '#2563eb' }}
                    />
                    Male
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="mortality-gender"
                      value="female"
                      checked={gender === 'female'}
                      onChange={() => setGender('female')}
                      style={{ accentColor: '#2563eb' }}
                    />
                    Female
                  </label>
                </div>

                <SubLayerButton
                  active={selectedLayer === cancerLayer}
                  onClick={() => handleLayerClick(cancerLayer)}
                  testId="demo-sublayer-cancer-female"
                >
                  Cancer Mortality ({gender === 'male' ? 'Male' : 'Female'})
                </SubLayerButton>
                <SubLayerButton
                  active={selectedLayer === 'heart_disease_mortality_per_100k'}
                  onClick={() => handleLayerClick('heart_disease_mortality_per_100k')}
                  testId="demo-sublayer-heart-disease"
                >
                  Heart Disease Mortality
                </SubLayerButton>
              </>
            )}
          </div>

          {/* Co-occurrence disclaimer — ONLY on mortality tabs (UX Invariant 10) */}
          {isMortalityTab && (
            <aside
              data-testid="cooccurrence-disclaimer"
              style={{
                padding: '10px 12px',
                background: '#fef3c7',
                borderLeft: '3px solid #f59e0b',
                borderRadius: '4px',
                fontSize: '11px',
                color: '#92400e',
                lineHeight: 1.4,
              }}
            >
              <strong>Note:</strong> Correlation does not imply causation. Demographic overlays show
              co-occurrence patterns only and do not establish causal relationships between
              environmental releases and health outcomes.
            </aside>
          )}
        </>
      )}
    </div>
  )
}
