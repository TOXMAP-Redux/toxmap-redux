/**
 * Demographic layer color utilities.
 * Used by both InlineLegend and MapContainer for consistent colors.
 * 
 * Color scheme: Unified 8-bin light green → dark blue gradient
 * (matches historical TOXMAP Fig 2015-5 design)
 * 
 * ColorBrewer GnBu 8-class sequential scheme:
 * https://colorbrewer2.org/#type=sequential&scheme=GnBu&n=8
 */
import type { DemographicLayer } from '../../api/types'

/** 
 * Unified color scale for all demographic layers.
 * 8-bin light green → dark blue (ColorBrewer GnBu 8-class).
 * Matches historical TOXMAP census overlay appearance (Fig 2015-5).
 */
export const DEMOGRAPHIC_COLORS = [
  '#f7fcf0', // 1. Very light green-white
  '#e0f3db', // 2. Light green
  '#ccebc5', // 3. Pale green
  '#a8ddb5', // 4. Light teal-green
  '#7bccc4', // 5. Teal
  '#4eb3d3', // 6. Light blue
  '#2b8cbe', // 7. Medium blue
  '#08589e', // 8. Dark blue
] as const

/** @deprecated Use DEMOGRAPHIC_COLORS directly. Kept for backward compatibility. */
export const COLOR_SCALES = {
  population: DEMOGRAPHIC_COLORS,
  income: DEMOGRAPHIC_COLORS,
  mortality: DEMOGRAPHIC_COLORS,
} as const

/** Map layer type to its color scale (unified 8-bin scheme) */
export function getColorScale(_layer: DemographicLayer): readonly string[] {
  // All layers now use the unified 8-bin GnBu scheme
  return DEMOGRAPHIC_COLORS
}

/** Approximate data ranges for legend labels (8 bins to match color scale) */
export function getLegendRanges(layer: DemographicLayer): string[] {
  switch (layer) {
    case 'pct_under_18':
      // US county range typically 15-30%, bins centered around national avg ~22%
      return ['0-16%', '16-18%', '18-20%', '20-22%', '22-24%', '24-26%', '26-28%', '28%+']
    case 'pct_over_65':
      // US county range typically 10-25%, bins centered around national avg ~16%
      return ['0-10%', '10-12%', '12-14%', '14-16%', '16-18%', '18-20%', '20-22%', '22%+']
    case 'pct_nonwhite':
      return ['0-5%', '5-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-70%', '70%+']
    case 'median_income':
      return ['<$25k', '$25-35k', '$35-45k', '$45-55k', '$55-65k', '$65-80k', '$80-100k', '$100k+']
    case 'cancer_mortality_male_per_100k':
    case 'cancer_mortality_female_per_100k':
      return ['<80', '80-100', '100-120', '120-150', '150-180', '180-210', '210-250', '250+']
    case 'heart_disease_mortality_per_100k':
      return ['<80', '80-100', '100-130', '130-160', '160-200', '200-250', '250-300', '300+']
    case 'total_pop':
      return ['<5k', '5-10k', '10-25k', '25-50k', '50-100k', '100-250k', '250-500k', '500k+']
    default:
      return ['0-12%', '12-25%', '25-37%', '37-50%', '50-62%', '62-75%', '75-87%', '87%+']
  }
}

/** Human-readable label for the layer type */
export function getLayerLabel(layer: DemographicLayer): string {
  switch (layer) {
    case 'pct_under_18':
      return '% Under 18'
    case 'pct_over_65':
      return '% Over 65'
    case 'pct_nonwhite':
      return '% Non-White'
    case 'median_income':
      return 'Median Household Income'
    case 'cancer_mortality_male_per_100k':
      return 'Cancer Mortality (Male)'
    case 'cancer_mortality_female_per_100k':
      return 'Cancer Mortality (Female)'
    case 'heart_disease_mortality_per_100k':
      return 'Heart Disease Mortality'
    case 'total_pop':
      return 'Total Population'
  }
}

/** Breakpoints for each layer type — 8 bins to match DEMOGRAPHIC_COLORS */
function getBreakpoints(layer: DemographicLayer): number[] {
  switch (layer) {
    case 'pct_under_18':
      return [0, 16, 18, 20, 22, 24, 26, 28]
    case 'pct_over_65':
      return [0, 10, 12, 14, 16, 18, 20, 22]
    case 'pct_nonwhite':
      return [0, 5, 10, 20, 30, 40, 50, 70]
    case 'median_income':
      return [0, 25000, 35000, 45000, 55000, 65000, 80000, 100000]
    case 'cancer_mortality_male_per_100k':
    case 'cancer_mortality_female_per_100k':
      return [0, 80, 100, 120, 150, 180, 210, 250]
    case 'heart_disease_mortality_per_100k':
      return [0, 80, 100, 130, 160, 200, 250, 300]
    case 'total_pop':
      return [0, 5000, 10000, 25000, 50000, 100000, 250000, 500000]
    default:
      return [0, 12, 25, 37, 50, 62, 75, 87]
  }
}

/** Get the bin label for a given value and layer type */
export function getBinLabel(layer: DemographicLayer, value: number | null): string {
  if (value === null || value === undefined) return 'No data'
  
  const breaks = getBreakpoints(layer)
  const ranges = getLegendRanges(layer)
  
  // Find which bin the value falls into
  for (let i = breaks.length - 1; i >= 0; i--) {
    if (value >= breaks[i]) {
      return ranges[i]
    }
  }
  return ranges[0]
}

/** Format raw value with appropriate units for tooltip display */
export function formatValue(layer: DemographicLayer, value: number | null): string {
  if (value === null || value === undefined) return 'No data'
  
  switch (layer) {
    case 'pct_under_18':
    case 'pct_over_65':
    case 'pct_nonwhite':
      return `${value.toFixed(1)}%`
    case 'median_income':
      return `$${value.toLocaleString()}`
    case 'total_pop':
      return value.toLocaleString()
    case 'cancer_mortality_male_per_100k':
    case 'cancer_mortality_female_per_100k':
    case 'heart_disease_mortality_per_100k':
      return `${value.toFixed(1)} per 100k`
    default:
      return String(value)
  }
}
